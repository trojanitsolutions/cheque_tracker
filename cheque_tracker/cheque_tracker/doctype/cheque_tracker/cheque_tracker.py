# Copyright (c) 2026, Trojan Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import flt, fmt_money


class ChequeTracker(Document):
	def before_validate(self):
		self._set_outstanding_amount()

	def validate(self):
		self._validate_cheque_amount()

	def before_submit(self):
		if self.status not in ("Cleared", "Bounced"):
			frappe.throw(
				_(
					"Cheque Tracker can only be submitted when Status is <b>Cleared</b> or <b>Bounced</b>. "
					"Current status: {0}"
				).format(frappe.bold(self.status or _("Not Set"))),
				frappe.ValidationError,
			)

	def _set_outstanding_amount(self):
		if not self.sales_invoice:
			return
		grand_total = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "grand_total"))
		exclude_name = None if self.is_new() else self.name
		allocated = _get_allocated_amount(self.sales_invoice, exclude_name=exclude_name)
		self.outstanding_amount = fmt_money(max(grand_total - allocated, 0.0))

	def _validate_cheque_amount(self):
		if not self.sales_invoice or not self.cheque_amount:
			return

		grand_total = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "grand_total"))
		exclude_name = None if self.is_new() else self.name
		already_allocated = _get_allocated_amount(self.sales_invoice, exclude_name=exclude_name)
		total_allocated = already_allocated + flt(self.cheque_amount)

		if total_allocated > grand_total:
			remaining = max(grand_total - already_allocated, 0.0)
			frappe.throw(
				_(
					"Cheque Amount exceeds the outstanding balance for Sales Invoice {0}.<br><br>"
					"<ul>"
					"<li><b>Grand Total:</b> {1}</li>"
					"<li><b>Already Allocated:</b> {2}</li>"
					"<li><b>Remaining Outstanding:</b> {3}</li>"
					"<li><b>Current Cheque Amount:</b> {4}</li>"
					"</ul>"
				).format(
					frappe.bold(self.sales_invoice),
					fmt_money(grand_total),
					fmt_money(already_allocated),
					fmt_money(remaining),
					fmt_money(flt(self.cheque_amount)),
				),
				frappe.ValidationError,
			)


def _get_allocated_amount(sales_invoice: str, exclude_name: str = None) -> float:
	"""Sum cheque_amount for active (non-cancelled, non-bounced) Cheque Tracker docs linked to sales_invoice."""
	CT = frappe.qb.DocType("Cheque Tracker")
	query = (
		frappe.qb.from_(CT)
		.select(Sum(CT.cheque_amount))
		.where(CT.sales_invoice == sales_invoice)
		.where(CT.docstatus != 2)
		.where(CT.status != "Bounced")
	)
	if exclude_name:
		query = query.where(CT.name != exclude_name)

	result = query.run()
	return flt(result[0][0]) if result and result[0][0] else 0.0


@frappe.whitelist()
def get_pending_cheque_for_invoice(sales_invoice: str) -> dict | None:
	"""Return the oldest submitted Cheque Tracker (Cleared, not yet linked to a Payment Entry)."""
	frappe.has_permission("Sales Invoice", doc=sales_invoice, throw=True)
	records = frappe.get_all(
		"Cheque Tracker",
		filters=[
			["sales_invoice", "=", sales_invoice],
			["docstatus", "=", 1],
			["status", "=", "Cleared"],
			["payment_entry", "is", "not set"],
		],
		fields=["name", "cheque_reference_no", "cheque_amount", "cheque_date"],
		order_by="cheque_date asc, creation asc",
		limit=1,
	)
	return records[0] if records else None


@frappe.whitelist()
def get_linked_cheque_tracker(payment_entry: str) -> str | None:
	"""Return the Cheque Tracker name linked to a given Payment Entry, if any."""
	return frappe.db.get_value("Cheque Tracker", {"payment_entry": payment_entry}, "name")


@frappe.whitelist()
def get_cheque_outstanding(sales_invoice: str) -> dict:
	"""Return grand_total, already allocated, and remaining outstanding for a Sales Invoice."""
	frappe.has_permission("Sales Invoice", doc=sales_invoice, throw=True)
	grand_total = flt(frappe.db.get_value("Sales Invoice", sales_invoice, "grand_total"))
	allocated = _get_allocated_amount(sales_invoice)
	outstanding = max(grand_total - allocated, 0.0)
	return {
		"grand_total": grand_total,
		"allocated": allocated,
		"outstanding": outstanding,
	}
