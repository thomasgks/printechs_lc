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
		set_lc_company_defaults(frm);
		set_lc_exchange_rate(frm);
	},

	currency(frm) {
		set_lc_exchange_rate(frm, true);
	},

	opening_date(frm) {
		set_lc_exchange_rate(frm);
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
				set_lc_company_defaults(frm);
			},
		});
	},

	validate(frm) {
		update_lc_amounts(frm);
		update_all_charge_base_amounts(frm);
	},

	refresh(frm) {
		frm.clear_custom_buttons();
		if (frm.is_new()) return;
		add_accounting_buttons(frm);
		frm.add_custom_button(__("L/C Ledger"), () => {
			frappe.set_route("query-report", "LC Ledger", {
				letter_of_credit: frm.doc.name,
				company: frm.doc.company,
			});
		}, __("View"));
	},

	exchange_rate(frm) {
		update_lc_amounts(frm);
		update_charge_exchange_rates(frm);
	},

	lc_amount(frm) {
		update_lc_amounts(frm);
	},

	utilized_amount(frm) {
		update_lc_amounts(frm);
	},

	margin_percent(frm) {
		update_lc_amounts(frm);
	},
});

frappe.ui.form.on("LC Shipment", {
	shipped_amount(frm) {
		update_shipment_utilization(frm);
	},

	shipments_remove(frm) {
		update_shipment_utilization(frm);
	},
});

frappe.ui.form.on("LC Charge", {
	amount(frm, cdt, cdn) {
		update_charge_base_amount(frm, cdt, cdn);
	},

	exchange_rate(frm, cdt, cdn) {
		update_charge_base_amount(frm, cdt, cdn);
	},

	charge_currency(frm, cdt, cdn) {
		set_charge_exchange_rate(frm, cdt, cdn);
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

function set_lc_company_defaults(frm) {
	if (!frm.doc.company) return;

	frappe.db.get_doc("LC Settings", "LC Settings").then((settings) => {
		const defaults = (settings.company_lc_defaults || []).find(
			(row) => row.company === frm.doc.company
		);
		if (!defaults) return;

		const values = {
			bank_account: defaults.default_bank_account,
			lc_margin_account: defaults.lc_margin_account,
			lc_liability_account: defaults.lc_liability_account,
			bank_charges_account: defaults.bank_charges_account,
		};

		Object.keys(values).forEach((fieldname) => {
			if (!frm.doc[fieldname] && values[fieldname]) {
				frm.set_value(fieldname, values[fieldname]);
			}
		});
	});
}

function set_lc_exchange_rate(frm, force = false) {
	if (!frm.doc.company || !frm.doc.currency) return;

	frappe.db.get_value("Company", frm.doc.company, "default_currency").then((r) => {
		const company_currency = r.message && r.message.default_currency;
		if (!company_currency) return;

		if (frm.doc.currency === company_currency) {
			frm.set_value("exchange_rate", 1);
			return;
		}

		if (!force && flt(frm.doc.exchange_rate) && flt(frm.doc.exchange_rate) !== 1) return;

		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency: frm.doc.currency,
				to_currency: company_currency,
				transaction_date: frm.doc.opening_date || frappe.datetime.get_today(),
				args: "for_buying",
			},
			callback(r) {
				if (r.message) {
					frm.set_value("exchange_rate", r.message);
				}
			},
		});
	});
}

function update_shipment_utilization(frm) {
	const shipment_utilized = Math.max(
		0,
		...(frm.doc.shipments || []).map((row) => flt(row.shipped_amount))
	);
	if (shipment_utilized > flt(frm.doc.utilized_amount)) {
		frm.set_value("utilized_amount", shipment_utilized);
	}
	update_lc_amounts(frm);
}

function update_lc_amounts(frm) {
	if (flt(frm.doc.margin_percent) && flt(frm.doc.lc_amount)) {
		const margin_amount = (flt(frm.doc.lc_amount) * flt(frm.doc.margin_percent)) / 100;
		if (flt(frm.doc.margin_amount) !== margin_amount) {
			frm.set_value("margin_amount", margin_amount);
		}
	}

	const available_amount = flt(frm.doc.lc_amount) - flt(frm.doc.utilized_amount);
	if (flt(frm.doc.available_amount) !== available_amount) {
		frm.set_value("available_amount", available_amount);
	}

	const exchange_rate = flt(frm.doc.exchange_rate || 1);
	const base_values = {
		base_lc_amount: flt(frm.doc.lc_amount) * exchange_rate,
		base_utilized_amount: flt(frm.doc.utilized_amount) * exchange_rate,
		base_available_amount: available_amount * exchange_rate,
	};
	Object.keys(base_values).forEach((fieldname) => {
		if (flt(frm.doc[fieldname]) !== base_values[fieldname]) {
			frm.set_value(fieldname, base_values[fieldname]);
		}
	});
}

function update_charge_exchange_rates(frm) {
	(frm.doc.charges || []).forEach((row) => {
		if (!row.journal_entry && row.charge_currency === frm.doc.currency) {
			frappe.model.set_value(row.doctype, row.name, "exchange_rate", frm.doc.exchange_rate || 1);
		}
	});
}

function set_charge_exchange_rate(frm, cdt, cdn) {
	const row = (locals[cdt] || {})[cdn];
	if (!row || !row.charge_currency) return;

	if (row.charge_currency === frm.doc.currency) {
		frappe.model.set_value(cdt, cdn, "exchange_rate", frm.doc.exchange_rate || 1);
		return;
	}

	frappe.db.get_value("Company", frm.doc.company, "default_currency").then((r) => {
		const company_currency = r.message && r.message.default_currency;
		if (!company_currency) return;

		if (row.charge_currency === company_currency) {
			frappe.model.set_value(cdt, cdn, "exchange_rate", 1);
			return;
		}

		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency: row.charge_currency,
				to_currency: company_currency,
				transaction_date: row.charge_date || frm.doc.opening_date || frappe.datetime.get_today(),
				args: "for_buying",
			},
			callback(res) {
				if (res.message) {
					frappe.model.set_value(cdt, cdn, "exchange_rate", res.message);
				}
			},
		});
	});
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
			frm._lc_posting_in_progress = frm._lc_posting_in_progress || {};
			const post_key = `${method}:${JSON.stringify(args)}`;
			if (frm._lc_posting_in_progress[post_key]) return;

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
					frm._lc_posting_in_progress[post_key] = true;
					frm.remove_custom_button(label, group);
					frappe.call({
						method,
						args: { lc_name: frm.doc.name, amount: values.amount, ...args },
						freeze: true,
						callback(r) {
							delete frm._lc_posting_in_progress[post_key];
							if (r.message) {
								frappe.show_alert({
									message: __("Voucher {0} created", [r.message]),
									indicator: "green",
								});
								frm.reload_doc();
							}
						},
						error() {
							delete frm._lc_posting_in_progress[post_key];
							frm.reload_doc();
						},
					});
				},
				label,
				__("Create Voucher")
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

	const unposted_charges = (frm.doc.charges || []).filter((row) => !row.journal_entry && !row.payment_entry);
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
	}

	const supplier_payment_total = get_linked_voucher_total(
		frm,
		["Supplier Payment", "Bank Paid Supplier"],
		frm.doc.lc_liability_account,
		"credit"
	);
	const company_settlement_total = get_linked_voucher_total(
		frm,
		["Company Settlement"],
		frm.doc.lc_liability_account,
		"debit"
	);
	const linked_outstanding = Math.max(supplier_payment_total - company_settlement_total, 0);
	const current_outstanding = Math.max(flt(frm.doc.outstanding_liability), linked_outstanding);
	const unposted_supplier_payment = flt(frm.doc.utilized_amount) - supplier_payment_total;

	if (frm.doc.bank_payment_confirmed && unposted_supplier_payment > 0 && current_outstanding === 0) {
		post(
			__("Supplier Payment"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_bank_paid_supplier",
			unposted_supplier_payment
		);
	}

	if (current_outstanding > 0) {
		post(
			__("Settle with Bank"),
			"printechs_lc.printechs_lc.doctype.letter_of_credit.letter_of_credit.make_company_settlement",
			current_outstanding
		);
	}
}

function get_linked_voucher_total(frm, transaction_types, account, amount_field) {
	return (frm.doc.voucher_links || [])
		.filter((row) => transaction_types.includes(row.transaction_type))
		.filter((row) => !account || row.account === account)
		.reduce((total, row) => total + flt(row[amount_field]), 0);
}
