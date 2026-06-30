import os

import frappe
from frappe import _
from frappe.utils import add_days, formatdate, getdate, get_url, nowdate

_CSS_PATH = os.path.join(os.path.dirname(__file__), "employe_notify.css")


def _load_css() -> str:
	with open(_CSS_PATH, "r") as f:
		return f.read()


def send_qatar_id_expiry_notifications():

	logger = frappe.logger("qatar_id_notify", allow_site=True)

	settings = frappe.get_single("HR Settings")


	notify_users = settings.qatar_id_notification or []
	if not notify_users:
		logger.info("Qatar ID Notify: no users configured — skipping")
		return

	notify_days = int(settings.qatar_id_notify_days or 0)
	today_date = getdate(nowdate())
	cutoff_date = add_days(today_date, notify_days)
	today_str = str(today_date)

	employees = _get_expiring_employees(today_date, cutoff_date)
	logger.info(f"Qatar ID Notify: {len(employees)} employee(s) to process (window: {notify_days} days)")

	for emp in employees:
		try:
			_process_employee(emp, settings, notify_users, today_str, today_date, logger)
		except Exception:
			logger.exception(f"Qatar ID Notify: unhandled error for {emp.name}")
			frappe.log_error(frappe.get_traceback(), f"Qatar ID Notify failed: {emp.name}")

	logger.info("Qatar ID Notify: completed")




def _get_expiring_employees(today_date, cutoff_date):
	return frappe.get_all(
		"Employee",
		filters=[
			["status", "=", "Active"],
			["qatar_id_expiry_date", "is", "set"],
			["qatar_id_expiry_date", "<=", cutoff_date],
		],
		fields=["name", "employee_name", "department", "designation", "qatar_id_expiry_date", "user_id", "company"],
	)



def _process_employee(emp, settings, notify_users, today_str, today_date, logger):
	days_remaining = (getdate(emp.qatar_id_expiry_date) - today_date).days

	logger.info(f"Qatar ID Notify: processing {emp.name} ({emp.employee_name}), {days_remaining} day(s) remaining")

	for row in notify_users:
		user = getattr(row, "user", None)
		if not user:
			continue
		_send_hr_system_notification(emp, days_remaining, user, today_str, logger)
		_send_hr_email(emp, days_remaining, user, today_str, logger)

	if settings.qatar_id_notify_employee and emp.user_id:
		_send_employee_system_notification(emp, days_remaining, today_str, logger)
		_send_employee_email(emp, days_remaining, today_str, logger)




def _already_notified(document_name, for_user, subject, today_str):
	return frappe.db.sql(
		"""SELECT name FROM `tabNotification Log`
		   WHERE document_type='Employee'
		     AND document_name=%s
		     AND for_user=%s
		     AND subject=%s
		     AND DATE(creation)=%s
		   LIMIT 1""",
		(document_name, for_user, subject, today_str),
	)



def _send_hr_system_notification(emp, days_remaining, user, today_str, logger):
	subject = _("Qatar ID Expiry Reminder")
	if _already_notified(emp.name, user, subject, today_str):
		return

	message = _(
		"The Qatar ID of <b>{0} ({1})</b> will expire in <b>{2} day(s)</b> on <b>{3}</b>."
		"<br>Please initiate the renewal process."
	).format(emp.employee_name, emp.name, days_remaining, formatdate(emp.qatar_id_expiry_date))

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": subject,
		"email_content": message,
		"for_user": user,
		"type": "Alert",
		"document_type": "Employee",
		"document_name": emp.name,
		"from_user": "Administrator",
		"read": 0,
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	logger.info(f"Qatar ID Notify: HR system notification → {user} for {emp.name}")


def _send_hr_email(emp, days_remaining, user, today_str, logger):
	dedup_subject = f"Qatar ID Expiry Reminder - {emp.name} [HR Email]"
	if _already_notified(emp.name, user, dedup_subject, today_str):
		return

	user_email = frappe.db.get_value("User", user, "email")
	if not user_email:
		logger.warning(f"Qatar ID Notify: no email address for HR user {user}")
		return

	frappe.sendmail(
		recipients=[user_email],
		subject=_("Qatar ID Expiry Reminder - {0}").format(emp.employee_name),
		message=_build_email(emp, days_remaining, is_hr=True),
		delayed=True,
	)
	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": dedup_subject,
		"email_content": f"Email queued for {user_email}",
		"for_user": user,
		"type": "Alert",
		"document_type": "Employee",
		"document_name": emp.name,
		"from_user": "Administrator",
		"read": 1,
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	logger.info(f"Qatar ID Notify: HR email queued → {user_email} for {emp.name}")




def _send_employee_system_notification(emp, days_remaining, today_str, logger):
	subject = _("Your Qatar ID is Expiring Soon")
	if _already_notified(emp.name, emp.user_id, subject, today_str):
		return

	message = _(
		"Dear {0},<br><br>"
		"Your Qatar ID will expire in <b>{1} day(s)</b> on <b>{2}</b>.<br><br>"
		"Please contact the HR department and complete the renewal process before the expiry date."
	).format(emp.employee_name, days_remaining, formatdate(emp.qatar_id_expiry_date))

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": subject,
		"email_content": message,
		"for_user": emp.user_id,
		"type": "Alert",
		"document_type": "Employee",
		"document_name": emp.name,
		"from_user": "Administrator",
		"read": 0,
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	logger.info(f"Qatar ID Notify: employee system notification → {emp.user_id} for {emp.name}")


def _send_employee_email(emp, days_remaining, today_str, logger):
	dedup_subject = f"Qatar ID Expiry Reminder - {emp.name} [Emp Email]"
	if _already_notified(emp.name, emp.user_id, dedup_subject, today_str):
		return

	emp_email = frappe.db.get_value("User", emp.user_id, "email")
	if not emp_email:
		logger.warning(f"Qatar ID Notify: no email for employee user {emp.user_id} ({emp.name})")
		return

	frappe.sendmail(
		recipients=[emp_email],
		subject=_("Qatar ID Expiry Reminder - {0}").format(emp.employee_name),
		message=_build_email(emp, days_remaining, is_hr=False),
		delayed=True,
	)
	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": dedup_subject,
		"email_content": f"Email queued for {emp_email}",
		"for_user": emp.user_id,
		"type": "Alert",
		"document_type": "Employee",
		"document_name": emp.name,
		"from_user": "Administrator",
		"read": 1,
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	logger.info(f"Qatar ID Notify: employee email queued → {emp_email} for {emp.name}")



def _build_email(emp, days_remaining, is_hr: bool) -> str:
	formatted_expiry = formatdate(emp.qatar_id_expiry_date, "dd MMM yyyy")
	today_formatted = formatdate(nowdate(), "dd MMM yyyy")
	emp_url = f"{get_url()}/app/employee/{emp.name}"

	title = _("Qatar ID Expiry Reminder") if is_hr else _("Your Qatar ID is Expiring Soon")
	intro = (
		_("This is an automated reminder regarding an employee Qatar ID approaching its expiry date.")
		if is_hr
		else _("This is an automated reminder that your Qatar ID is approaching its expiry date.")
	)
	action_note = (
		_("Kindly coordinate with the employee to complete the Qatar ID renewal before the expiry date.")
		if is_hr
		else _("Please ensure your Qatar ID renewal process is completed before the expiry date to avoid any legal or employment issues.")
	)

	logo_html = ""
	try:
		ws = frappe.get_single("Website Settings")
		if ws.banner_image:
			logo_html = f'<img src="{get_url()}{ws.banner_image}" alt="Logo" style="max-height:55px;margin-bottom:8px;">'
	except Exception:
		pass

	css = _load_css()

	return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<table class="wrap" width="100%"><tr><td align="center">
<table class="box" width="660">

<tr><td class="hdr">
{logo_html}
<h1>&#128204; {title}</h1>
<p>{intro}</p>
</td></tr>

<tr><td class="sec">
<div class="sec-title">&#128100; {_('Employee Details')}</div>
<div class="card">
<table class="dt">
<tr><td class="lbl">{_('Employee Name')}</td><td class="val">{emp.employee_name}</td></tr>
<tr><td class="lbl">{_('Employee ID')}</td><td class="norm">{emp.name}</td></tr>
<tr><td class="lbl">{_('Department')}</td><td class="norm">{emp.department or '—'}</td></tr>
<tr><td class="lbl">{_('Designation')}</td><td class="norm">{emp.designation or '—'}</td></tr>
</table>
</div>
</td></tr>

<tr><td class="sec">
<div class="sec-title">&#128196; {_('Qatar ID Details')}</div>
<div class="card">
<table class="dt">
<tr><td class="lbl">{_('Qatar ID Expiry Date')}</td><td class="val">{formatted_expiry}</td></tr>
<tr><td class="lbl">{_('Days Remaining')}</td><td class="red">&#9888;&#65039; {days_remaining} {_('day(s)')}</td></tr>
<tr><td class="lbl">{_('Current Date')}</td><td class="norm">{today_formatted}</td></tr>
</table>
</div>
</td></tr>

<tr><td>
<div class="note">&#8505;&#65039; {action_note}</div>
</td></tr>

<tr><td align="center" style="padding-bottom:28px;">
<a href="{emp_url}" class="btn">{_('View Employee Record')} &#8594;</a>
</td></tr>

<tr><td class="foot">{_('This is an automated notification generated by Luxury Stationery HRMS.')}</td></tr>

</table>
</td></tr></table>
</body>
</html>"""
