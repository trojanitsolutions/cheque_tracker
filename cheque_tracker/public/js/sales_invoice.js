// Adds "Create Cheque" button to submitted Sales Invoice forms.
// This file is injected via doctype_js hook — no ERPNext core files are modified.

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(
				__("Cheque"),
				function () {
					frappe.route_options = { sales_invoice: frm.doc.name };
					frappe.new_doc("Cheque Tracker");
				},
				__("Create")
			);
		}
	},
});
