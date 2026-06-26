import frappe


def run():
	rows = frappe.db.sql(
		"SELECT name, `subject`, for_user, `read`, creation FROM `tabNotification Log` WHERE document_type='Cheque Tracker' ORDER BY creation DESC",
		as_dict=True,
	)
	print("=== Notification Log ===")
	for r in rows:
		print(dict(r))

	errors = frappe.db.sql(
		"SELECT name, method, error, creation FROM `tabError Log` ORDER BY creation DESC LIMIT 5",
		as_dict=True,
	)
	print("\n=== Recent Error Logs (full) ===")
	for e in errors:
		print("NAME:", e.name)
		print("METHOD:", e.method)
		print("ERROR:", (e.error or "")[:500])
		print("---")
