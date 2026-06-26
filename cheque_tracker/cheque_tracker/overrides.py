from frappe import _


def get_sales_invoice_dashboard_data(data):
	"""Append Cheque Tracker to the Sales Invoice Document Links dashboard."""
	data["transactions"].append({
		"label": _("Cheque"),
		"items": ["Cheque Tracker"],
	})
	return data
