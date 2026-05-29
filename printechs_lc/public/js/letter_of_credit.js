frappe.ui.form.on("Letter of Credit", {
	setup(frm) {
		frm.set_query("lc_margin_account", () => account_filter(frm.doc.company));
		frm.set_query("lc_liability_account", () => account_filter(frm.doc.company));
		frm.set_query("bank_charges_account", () => account_filter(frm.doc.company));
		frm.set_query("bank_account", () => account_filter(frm.doc.company, "Bank"));
		frm.set_query("purchase_order", () => ({
			filters: {
				company: frm.doc.company,
				docstatus: 1,
				supplier: frm.doc.supplier || undefined,
			},
		}));
	},

	company(frm) {
		if (frm.doc.company && !frm.doc.currency) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency", (r) => {
				frm.set_value("currency", r.default_currency);
			});
		}
	},

	purchase_order(frm) {
		if (!frm.doc.purchase_order) return;
		frappe.call({
			method: "printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.get_po_details",
			args: { purchase_order: frm.doc.purchase_order },
			callback(r) {
				if (!r.message) return;
				$.each(r.message, (field, value) => {
					if (value) frm.set_value(field, value);
				});
			},
		});
	},

	validate(frm) {
		update_all_charge_base_amounts(frm);
	},

	refresh(frm) {
		update_all_charge_base_amounts(frm);
		if (frm.is_new()) return;
		add_accounting_buttons(frm);
		frm.add_custom_button(__("L/C Ledger"), () => {
			frappe.set_route("query-report", "LC Ledger", {
				letter_of_credit: frm.doc.name,
				company: frm.doc.company,
			});
		}, __("View"));
	},
});

frappe.ui.form.on("LC Charge", {
	amount(frm, cdt, cdn) {
		update_charge_base_amount(frm, cdt, cdn);
	},

	exchange_rate(frm, cdt, cdn) {
		update_charge_base_amount(frm, cdt, cdn);
	},
});

function account_filter(company, account_type) {
	return {
		filters: {
			company,
			is_group: 0,
			account_type: account_type || undefined,
		},
	};
}

function update_all_charge_base_amounts(frm) {
	(frm.doc.charges || []).forEach((row) => {
		update_charge_base_amount(frm, row.doctype, row.name);
	});
}

function update_charge_base_amount(frm, cdt, cdn) {
	const row = (locals[cdt] || {})[cdn];
	if (!row) return;

	const base_amount = flt(row.amount) * flt(row.exchange_rate || 1);
	if (flt(row.base_amount) === base_amount) return;

	frappe.model.set_value(cdt, cdn, "base_amount", base_amount);
	frm.refresh_field("charges");
}

function is_zero_margin_lc(doc) {
	return cint(doc.allow_zero_margin) && !flt(doc.margin_percent) && !flt(doc.margin_amount);
}

function add_accounting_buttons(frm) {
	if (frm.doc.docstatus !== 1) return;

	const group = __("Accounting");
	const post = (label, method, default_amount, args = {}) => {
		frm.add_custom_button(label, () => {
			frappe.prompt(
				[
					{
						fieldname: "amount",
						fieldtype: "Currency",
						label: __("Amount"),
						default: flt(default_amount),
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method,
						args: { lc_name: frm.doc.name, amount: values.amount, ...args },
						freeze: true,
						callback(r) {
							if (r.message) {
								frappe.show_alert({
									message: __("Journal Entry {0} created", [r.message]),
									indicator: "green",
								});
								frm.reload_doc();
							}
						},
					});
				},
				label,
				__("Create Journal Entry")
			);
		}, group);
	};

	if (!frm.doc.margin_blocked && !is_zero_margin_lc(frm.doc)) {
		const margin_amount =
			flt(frm.doc.margin_amount) || (flt(frm.doc.lc_amount) * flt(frm.doc.margin_percent)) / 100;
		post(
			__("Block Margin"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_margin_block",
			margin_amount
		);
	}

	if (!frm.doc.margin_released && frm.doc.margin_blocked) {
		post(
			__("Release Margin"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_margin_release",
			frm.doc.margin_amount
		);
	}

	const unposted_charges = (frm.doc.charges || []).filter((row) => !row.journal_entry);
	if (unposted_charges.length) {
		unposted_charges.forEach((row) => {
			const base_amount = flt(row.base_amount) || flt(row.amount) * flt(row.exchange_rate || 1);
			post(
				__("Post {0} Charge", [row.charge_type || __("Bank")]),
				"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_bank_charges",
				base_amount,
				{ charge_row_idx: row.idx }
			);
		});
	} else {
		post(
			__("Post Bank Charges"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_bank_charges",
			0
		);
	}

	if (
		frm.doc.bank_payment_confirmed &&
		flt(frm.doc.utilized_amount) > 0 &&
		flt(frm.doc.outstanding_liability) === 0
	) {
		post(
			__("Bank Paid Supplier"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_bank_paid_supplier",
			frm.doc.utilized_amount
		);
	}

	if (flt(frm.doc.outstanding_liability) > 0) {
		post(
			__("Settle with Bank"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_company_settlement",
			frm.doc.outstanding_liability
		);
	}
}
