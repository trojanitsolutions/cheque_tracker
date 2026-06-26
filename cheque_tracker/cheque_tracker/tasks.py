# Copyright (c) 2026, Trojan Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate, get_url, nowdate


def send_cheque_due_notifications():
	"""Daily scheduler: send cheque due reminder notifications to configured users."""
	print("[CHEQUE NOTIF] Starting...")

	settings = frappe.get_single("Cheque Tracker Settings")
	print(f"[CHEQUE NOTIF] Enable: {settings.enable_cheque_notification}, Notify Before: {settings.notify_before}, Users: {len(settings.notify_user)}")

	if settings.enable_cheque_notification != "Yes":
		print("[CHEQUE NOTIF] Disabled - exiting")
		return

	if not settings.notify_before or not settings.notify_user:
		print("[CHEQUE NOTIF] notify_before or notify_user missing - exiting")
		return

	notify_before = int(settings.notify_before)
	today_date = getdate(nowdate())
	today_str = str(today_date)

	cheques = frappe.get_all(
		"Cheque Tracker",
		filters=[
			["docstatus", "!=", 2],
			["status", "not in", ["Cleared", "Bounced"]],
		],
		fields=[
			"name",
			"cheque_reference_no",
			"sales_invoice",
			"cheque_amount",
			"cheque_date",
			"outstanding_amount",
			"status",
		],
	)
	print(f"[CHEQUE NOTIF] Found {len(cheques)} active cheque(s)")

	for cheque in cheques:
		print(f"[CHEQUE NOTIF] Checking {cheque.name} | date={cheque.cheque_date} | status={cheque.status}")

		if not cheque.cheque_date:
			print(f"[CHEQUE NOTIF] {cheque.name} has no cheque_date - skipping")
			continue

		cheque_date = getdate(cheque.cheque_date)
		notification_date = getdate(add_days(cheque_date, -notify_before))
		print(f"[CHEQUE NOTIF] {cheque.name} | today={today_date} | notify_from={notification_date} | fires={today_date >= notification_date}")

		if today_date < notification_date:
			print(f"[CHEQUE NOTIF] {cheque.name} not yet due for notification - skipping")
			continue

		days_remaining = (cheque_date - today_date).days

		si_details = (
			frappe.db.get_value(
				"Sales Invoice",
				cheque.sales_invoice,
				["customer", "company", "grand_total", "outstanding_amount"],
				as_dict=True,
			)
			or {}
		)
		customer = si_details.get("customer", "")

		for user_row in settings.notify_user:
			user = user_row.user
			print(f"[CHEQUE NOTIF] Processing user: {user!r}")
			if not user:
				print("[CHEQUE NOTIF] Empty user - skipping")
				continue

			_send_system_notification(cheque, customer, days_remaining, user, today_str)
			_send_email_notification(cheque, si_details, customer, user, today_str)

	print("[CHEQUE NOTIF] Done")


def _send_system_notification(cheque, customer, days_remaining, user, today_str):
	"""Insert a Notification Log entry (bell notification) for the cheque reminder."""
	# Check if already sent today
	existing = frappe.db.sql(
		"""SELECT name FROM `tabNotification Log`
		   WHERE document_type='Cheque Tracker'
		     AND document_name=%s
		     AND for_user=%s
		     AND `subject`='Cheque Due Reminder'
		     AND DATE(creation)=%s
		   LIMIT 1""",
		(cheque.name, user, today_str),
	)
	if existing:
		print(f"[CHEQUE NOTIF] System notification already sent today for {cheque.name} → {user}")
		return

	if days_remaining > 0:
		days_label = _("{0} day(s) remaining").format(days_remaining)
	elif days_remaining == 0:
		days_label = _("Due today")
	else:
		days_label = _("{0} day(s) overdue").format(abs(days_remaining))

	message = (
		f"<b>{_('Cheque Number')}:</b> {cheque.cheque_reference_no}<br>"
		f"<b>{_('Customer')}:</b> {customer}<br>"
		f"<b>{_('Sales Invoice')}:</b> {cheque.sales_invoice}<br>"
		f"<b>{_('Cheque Amount')}:</b> {cheque.cheque_amount}<br>"
		f"<b>{_('Cheque Date')}:</b> {cheque.cheque_date}<br>"
		f"<b>{_('Outstanding Amount')}:</b> {cheque.outstanding_amount}<br>"
		f"<b>{_('Days Remaining')}:</b> {days_label}"
	)

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"subject": _("Cheque Due Reminder"),
				"email_content": message,
				"for_user": user,
				"type": "Alert",
				"document_type": "Cheque Tracker",
				"document_name": cheque.name,
				"from_user": "Administrator",
				"read": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"[CHEQUE NOTIF] System notification created: {doc.name} for {user}")
	except Exception:
		print(f"[CHEQUE NOTIF] ERROR creating system notification for {cheque.name}")
		import traceback; traceback.print_exc()
		frappe.log_error(frappe.get_traceback(), f"Cheque Notification Log failed: {cheque.name}")


def _send_email_notification(cheque, si_details, customer, user, today_str):
	"""Send an email reminder for the cheque due date."""
	# Check if email already sent today
	existing = frappe.db.sql(
		"""SELECT name FROM `tabNotification Log`
		   WHERE document_type='Cheque Tracker'
		     AND document_name=%s
		     AND for_user=%s
		     AND `subject`='Cheque Due Reminder [Email]'
		     AND DATE(creation)=%s
		   LIMIT 1""",
		(cheque.name, user, today_str),
	)
	if existing:
		print(f"[CHEQUE NOTIF] Email already sent today for {cheque.name} → {user}")
		return

	user_email = frappe.db.get_value("User", user, "email")
	if not user_email:
		print(f"[CHEQUE NOTIF] No email address for user {user}")
		return

	subject = _("Cheque Due Reminder - {0}").format(cheque.sales_invoice)
	cheque_url = f"{get_url()}/app/cheque-tracker/{cheque.name}"

	company = si_details.get("company", "")
	grand_total = si_details.get("grand_total", 0)
	si_outstanding = si_details.get("outstanding_amount", 0)

	message = f"""
<p style="font-family: Arial, sans-serif;">
  <strong>{_("This is an automated reminder for a cheque approaching its due date.")}</strong>
</p>

<h3 style="font-family: Arial, sans-serif;">{_("Sales Invoice Details")}</h3>
<table border="1" cellpadding="8" cellspacing="0"
       style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px;">
  <tr><td><b>{_("Sales Invoice")}</b></td><td>{cheque.sales_invoice}</td></tr>
  <tr><td><b>{_("Customer")}</b></td><td>{customer}</td></tr>
  <tr><td><b>{_("Company")}</b></td><td>{company}</td></tr>
  <tr><td><b>{_("Grand Total")}</b></td><td>{grand_total}</td></tr>
  <tr><td><b>{_("Outstanding Amount")}</b></td><td>{si_outstanding}</td></tr>
</table>
<br>
<h3 style="font-family: Arial, sans-serif;">{_("Cheque Details")}</h3>
<table border="1" cellpadding="8" cellspacing="0"
       style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px;">
  <tr><td><b>{_("Cheque Tracker ID")}</b></td><td>{cheque.name}</td></tr>
  <tr><td><b>{_("Cheque Number")}</b></td><td>{cheque.cheque_reference_no}</td></tr>
  <tr><td><b>{_("Cheque Amount")}</b></td><td>{cheque.cheque_amount}</td></tr>
  <tr><td><b>{_("Cheque Date")}</b></td><td>{cheque.cheque_date}</td></tr>
  <tr><td><b>{_("Bank Name")}</b></td><td>{_("N/A")}</td></tr>
  <tr><td><b>{_("Current Status")}</b></td><td>{cheque.status}</td></tr>
</table>
<br>
<a href="{cheque_url}"
   style="display: inline-block; padding: 10px 18px; background: #4a86e8;
          color: #ffffff; text-decoration: none; border-radius: 4px;
          font-family: Arial, sans-serif; font-size: 13px;">
  {_("View Cheque Tracker")}
</a>
"""

	try:
		frappe.sendmail(
			recipients=[user_email],
			subject=subject,
			message=message,
			delayed=True,  # queue for background sending
		)
		# Record that email was sent today
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"subject": _("Cheque Due Reminder [Email]"),
				"email_content": f"Email queued for {user_email}",
				"for_user": user,
				"type": "Alert",
				"document_type": "Cheque Tracker",
				"document_name": cheque.name,
				"from_user": "Administrator",
				"read": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"[CHEQUE NOTIF] Email queued for {user_email} ({cheque.name})")
	except Exception:
		print(f"[CHEQUE NOTIF] ERROR sending email for {cheque.name}")
		import traceback; traceback.print_exc()
		frappe.log_error(frappe.get_traceback(), f"Cheque Email Notification failed: {cheque.name}")
