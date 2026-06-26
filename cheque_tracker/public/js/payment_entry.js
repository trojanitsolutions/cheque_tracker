frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.mode_of_payment === "Cheque") {
			_show_linked_cheque_info(frm);
		}
		if (frm.doc.docstatus === 0) {
			_maybe_fetch_cheque(frm);
		}
	},

	mode_of_payment(frm) {
		_maybe_fetch_cheque(frm);
	},
});

frappe.ui.form.on("Payment Entry Reference", {
	reference_name(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.reference_doctype === "Sales Invoice" && row.reference_name) {
			_maybe_fetch_cheque(frm);
		}
	},
});

function _get_sales_invoice(frm) {
	if (!frm.doc.references) return null;
	let ref = frm.doc.references.find(
		(r) => r.reference_doctype === "Sales Invoice" && r.reference_name
	);
	return ref ? ref.reference_name : null;
}

function _maybe_fetch_cheque(frm) {
	if (frm.doc.docstatus !== 0) return;
	if (frm.doc.mode_of_payment !== "Cheque") return;
	let sales_invoice = _get_sales_invoice(frm);
	if (!sales_invoice) return;

	frappe.call({
		method: "cheque_tracker.cheque_tracker.doctype.cheque_tracker.cheque_tracker.get_pending_cheque_for_invoice",
		args: { sales_invoice },
		callback(r) {
			if (r.message) {
				let cheque = r.message;
				frm.set_value("reference_no", cheque.cheque_reference_no);
				frm.set_value("reference_date", cheque.cheque_date);
				frm.set_value("paid_amount", cheque.cheque_amount);
				frappe.show_alert({
					message: __(
						"Cheque {0} auto-linked (Amount: {1})",
						[cheque.cheque_reference_no, frappe.utils.fmt_money(cheque.cheque_amount)]
					),
					indicator: "green",
				});
			} else {
				frappe.msgprint({
					title: __("No Submitted Cheque Found"),
					message: __(
						"No submitted pending Cheque Tracker record exists for Sales Invoice "
						+ "<b>{0}</b>.<br><br>"
						+ "Please create and submit a Cheque Tracker record first.",
						[sales_invoice]
					),
					indicator: "orange",
					primary_action: {
						label: __("Create Cheque"),
						action() {
							frappe.route_options = { sales_invoice };
							frappe.new_doc("Cheque Tracker");
						},
					},
				});
			}
		},
	});
}

function _show_linked_cheque_info(frm) {
	frappe.call({
		method: "cheque_tracker.cheque_tracker.doctype.cheque_tracker.cheque_tracker.get_linked_cheque_tracker",
		args: { payment_entry: frm.doc.name },
		callback(r) {
			if (r.message) {
				frm.set_intro(
					__("Linked Cheque Tracker: <a href=\"/app/cheque-tracker/{0}\">{0}</a>", [r.message]),
					"blue"
				);
			}
		},
	});
}
