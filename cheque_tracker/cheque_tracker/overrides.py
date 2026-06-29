from frappe import _


def get_sales_invoice_dashboard_data(data):
	
	data["transactions"].append({
		"label": _("Cheque"),
		"items": ["Cheque Tracker"],
	})
	return data
