# Copyright (c) 2026, Trojan Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, formatdate, getdate, get_url, nowdate


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
	formatted_date = formatdate(cheque.cheque_date, "dd MMM yyyy") if cheque.cheque_date else _("N/A")

	css = """<style>
body{margin:0;padding:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;}
table{border-collapse:collapse;}
.wrapper{width:100%;background:#f4f7fb;padding:30px 15px;}
.container{max-width:700px;margin:auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 8px 25px rgba(0,0,0,.08);}
.header{background:linear-gradient(135deg,#0c2d6b,#1d4ed8);padding:40px;color:#fff;}
.header h1{margin:0;font-size:34px;font-weight:700;}
.header p{margin:15px 0 0;font-size:17px;line-height:28px;color:#dbeafe;}
.badge{margin:30px auto;display:inline-block;border:1px solid #d6e4ff;background:#fff;color:#2563eb;padding:14px 28px;border-radius:40px;font-size:18px;font-weight:600;}
.section{padding:0 35px 35px;}
.section-title{font-size:24px;font-weight:bold;color:#1f2937;margin-bottom:20px;}
.card{border:1px solid #e5e7eb;border-radius:12px;padding:25px;}
.data-table{width:100%;}
.data-table td{padding:12px 0;border-bottom:1px dashed #ececec;font-size:15px;}
.data-table tr:last-child td{border-bottom:none;}
.label{color:#374151;font-weight:600;}
.value{color:#2563eb;font-weight:bold;text-align:right;}
.normal{color:#111827;font-weight:500;}
.red{color:#dc2626;font-weight:bold;text-align:right;}
.status{display:inline-block;background:#fff7e6;color:#d97706;padding:6px 16px;border-radius:30px;font-size:14px;font-weight:bold;}
.cta{margin:35px;background:#eff6ff;border-radius:12px;padding:22px;}
.cta table{width:100%;}
.button{background:#2563eb;color:#fff !important;text-decoration:none;padding:15px 28px;border-radius:8px;display:inline-block;font-weight:bold;}
.footer{border-top:1px solid #e5e7eb;padding:35px;}
.footer table{width:100%;}
.help{font-size:15px;color:#4b5563;line-height:26px;}
.help b{display:block;color:#111827;font-size:20px;margin-bottom:12px;}
.signature{text-align:right;color:#374151;line-height:28px;}
.signature strong{font-size:18px;}
.note{border-top:1px solid #ececec;text-align:center;padding:18px;color:#6b7280;font-size:14px;}
</style>"""

	message = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cheque Due Reminder</title>
{css}
</head>
<body>
<table class="wrapper" width="100%">
<tr><td align="center">
<table class="container" width="700">

<tr>
<td class="header">
<h1>&#128276; Cheque Due Reminder</h1>
<p>This is an automated reminder that a cheque associated with your sales invoice is approaching its due date.</p>
</td>
</tr>

<tr>
<td align="center">
<div class="badge">&#128196; Sales Invoice : {cheque.sales_invoice}</div>
</td>
</tr>

<tr>
<td class="section">
<div class="section-title">&#128203; Sales Invoice Details</div>
<div class="card">
<table class="data-table">
<tr><td class="label">Sales Invoice</td><td class="value">{cheque.sales_invoice}</td></tr>
<tr><td class="label">Customer</td><td class="normal" align="right">{customer}</td></tr>
<tr><td class="label">Company</td><td class="normal" align="right">{company}</td></tr>
<tr><td class="label">Grand Total</td><td class="value">{grand_total}</td></tr>
<tr><td class="label">Outstanding Amount</td><td class="red">{si_outstanding}</td></tr>
</table>
</div>
</td>
</tr>

<tr>
<td class="section">
<div class="section-title">&#127974; Cheque Details</div>
<div class="card">
<table class="data-table">
<tr><td class="label">Cheque Tracker</td><td class="value">{cheque.name}</td></tr>
<tr><td class="label">Cheque Number</td><td class="normal" align="right">{cheque.cheque_reference_no}</td></tr>
<tr><td class="label">Cheque Amount</td><td class="normal" align="right">{cheque.cheque_amount}</td></tr>
<tr><td class="label">Cheque Date</td><td class="value">{formatted_date}</td></tr>
<tr><td class="label">Bank Name</td><td class="normal" align="right">N/A</td></tr>
<tr><td class="label">Current Status</td><td align="right"><span class="status">{cheque.status}</span></td></tr>
</table>
</div>
</td>
</tr>

<tr>
<td>
<div class="cta">
<table>
<tr>
<td style="font-size:16px;color:#374151;">View complete cheque information and tracker history.</td>
<td align="right"><a href="{cheque_url}" class="button">View Cheque Tracker &#8594;</a></td>
</tr>
</table>
</div>
</td>
</tr>

<tr>
<td class="footer">
<table>
<tr>
<td class="help"><b>Need Help?</b>If you have any questions regarding this cheque, please contact your Accounts Team.</td>
<td class="signature">Best Regards,<br><strong>{company} Team</strong></td>
</tr>
</table>
</td>
</tr>

<tr>
<td class="note">This is an automated email. Please do not reply.</td>
</tr>

</table>
</td></tr>
</table>
</body>
</html>"""

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
