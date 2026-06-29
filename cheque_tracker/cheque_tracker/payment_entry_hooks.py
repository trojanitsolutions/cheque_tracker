import frappe
from frappe import _


def validate_cheque_payment(doc, method=None):
	
	if doc.mode_of_payment != "Cheque":
		return

	si_refs = [r for r in (doc.references or []) if r.reference_doctype == "Sales Invoice"]
	if not si_refs:
		return

	for ref in si_refs:
		exists = frappe.get_all(
			"Cheque Tracker",
			filters=[
				["sales_invoice", "=", ref.reference_name],
				["docstatus", "=", 1],
				["status", "=", "Cleared"],
				["payment_entry", "is", "not set"],
			],
			limit=1,
		)
		if not exists:
			frappe.throw(
				_(
					"No submitted Cheque Tracker record (Status: Cleared, not yet linked to a Payment Entry) "
					"exists for Sales Invoice {0}.<br><br>"
					"Please create, clear, and submit a Cheque Tracker record before processing this payment."
				).format(frappe.bold(ref.reference_name)),
				frappe.ValidationError,
			)


def on_payment_entry_submit(doc, method=None):
	"""on_submit: link the Payment Entry back to the matched Cheque Tracker."""
	if doc.mode_of_payment != "Cheque":
		return

	si_refs = [r for r in (doc.references or []) if r.reference_doctype == "Sales Invoice"]
	if not si_refs:
		return

	for ref in si_refs:
		cheque_name = _find_cheque(ref.reference_name, doc.reference_no)
		if cheque_name:
			frappe.db.set_value(
				"Cheque Tracker",
				cheque_name,
				{"payment_entry": doc.name},
				update_modified=True,
			)


def _find_cheque(sales_invoice: str, reference_no: str = None) -> str | None:

	base_filters = [
		["sales_invoice", "=", sales_invoice],
		["docstatus", "=", 1],
		["status", "=", "Cleared"],
		["payment_entry", "is", "not set"],
	]

	if reference_no:
		name_result = frappe.get_all(
			"Cheque Tracker",
			filters=base_filters + [["cheque_reference_no", "=", reference_no]],
			fields=["name"],
			limit=1,
		)
		if name_result:
			return name_result[0].name

	records = frappe.get_all(
		"Cheque Tracker",
		filters=base_filters,
		fields=["name"],
		order_by="cheque_date asc, creation asc",
		limit=1,
	)
	return records[0].name if records else None
