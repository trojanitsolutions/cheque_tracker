// Copyright (c) 2026, Trojan Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cheque Tracker", {
	refresh(frm) {
		frm.set_df_property("outstanding_amount", "read_only", 1);
		if (frm.doc.sales_invoice) {
			_fetch_and_set_outstanding(frm);
		} else if (frm.is_new()) {
			// route_options are applied synchronously after refresh fires;
			// defer one tick to catch the sales_invoice value set from route_options.
			setTimeout(() => {
				if (frm.doc.sales_invoice) {
					_fetch_and_set_outstanding(frm);
				}
			}, 0);
		}
	},

	sales_invoice(frm) {
		if (frm.doc.sales_invoice) {
			_fetch_and_set_outstanding(frm);
		} else {
			frm.doc.outstanding_amount = "";
			frm.refresh_field("outstanding_amount");
		}
	},

	cheque_amount(frm) {
		if (frm.doc.sales_invoice) {
			_fetch_and_set_outstanding(frm);
		}
	},
});

function _fetch_and_set_outstanding(frm) {
	frappe.call({
		method: "cheque_tracker.cheque_tracker.doctype.cheque_tracker.cheque_tracker.get_cheque_outstanding",
		args: { sales_invoice: frm.doc.sales_invoice },
		callback(r) {
			if (!r.message) return;
			// Use direct doc assignment + refresh_field — more reliable than
			// frm.set_value() for read-only fields in all Frappe versions.
			frm.doc.outstanding_amount = frappe.utils.fmt_money(r.message.outstanding);
			frm.refresh_field("outstanding_amount");
		},
	});
}
