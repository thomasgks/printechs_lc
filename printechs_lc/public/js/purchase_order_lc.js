frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
		if (!frm.doc.lc_required || frm.doc.docstatus !== 1) return;
		frm.add_custom_button(
			__("Letter of Credit"),
			() => {
				frappe.new_doc("Letter of Credit", {
					company: frm.doc.company,
					purchase_order: frm.doc.name,
					supplier: frm.doc.supplier,
					currency: frm.doc.currency,
					exchange_rate: frm.doc.conversion_rate,
					lc_amount: frm.doc.grand_total,
				});
			},
			__("Create")
		);
	},
});
