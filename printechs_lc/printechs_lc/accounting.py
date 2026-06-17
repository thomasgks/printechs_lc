import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from printechs_lc.utils.utilization import validate_amount_within_lc_limit


def create_journal_entry(lc, accounts, transaction_type, remark=None):
	"""Create and submit a Journal Entry linked to Letter of Credit."""
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = lc.company
	je.posting_date = today()
	je.user_remark = remark or f"{transaction_type} for {lc.name}"

	if frappe.get_meta("Journal Entry").has_field("letter_of_credit"):
		je.letter_of_credit = lc.name
	if frappe.get_meta("Journal Entry").has_field("lc_transaction_type"):
		je.lc_transaction_type = transaction_type

	for row in accounts:
		je.append(
			"accounts",
			{
				"account": row["account"],
				"debit_in_account_currency": flt(row.get("debit")),
				"credit_in_account_currency": flt(row.get("credit")),
				"party_type": row.get("party_type"),
				"party": row.get("party"),
				"cost_center": row.get("cost_center"),
			},
		)

	je.insert(ignore_permissions=True)
	je.submit()

	_add_voucher_link(lc, je, transaction_type, accounts)
	return je.name


def create_payment_entry(
	lc,
	payment_type,
	paid_from,
	paid_to,
	amount,
	transaction_type,
	party_type=None,
	party=None,
	remark=None,
	accounts=None,
):
	"""Create and submit a Payment Entry linked to Letter of Credit."""
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = lc.company
	pe.posting_date = today()
	pe.paid_from = paid_from
	pe.paid_to = paid_to
	pe.paid_amount = amount
	pe.received_amount = amount
	pe.source_exchange_rate = 1
	pe.target_exchange_rate = 1
	pe.reference_no = lc.bank_payment_reference or lc.lc_bank_number or lc.name
	pe.reference_date = lc.bank_payment_confirmation_date or today()
	pe.custom_remarks = 1
	pe.remarks = remark or f"{transaction_type} for {lc.name}"

	if payment_type != "Internal Transfer":
		pe.party_type = party_type
		pe.party = party

	if frappe.get_meta("Payment Entry").has_field("letter_of_credit"):
		pe.letter_of_credit = lc.name
	if frappe.get_meta("Payment Entry").has_field("lc_settlement_type"):
		pe.lc_settlement_type = transaction_type

	pe.insert(ignore_permissions=True)
	pe.submit()

	_add_voucher_link(lc, pe, transaction_type, accounts or [])
	return pe.name


def get_lc_voucher_type(fieldname):
	return frappe.db.get_single_value("LC Settings", fieldname) or "Journal Entry"


def get_voucher_link_total(lc, transaction_types, account=None, amount_field="credit"):
	total = 0
	for row in lc.voucher_links or []:
		if row.transaction_type not in transaction_types:
			continue
		if account and row.account != account:
			continue
		total += flt(row.get(amount_field))
	return total


def get_supplier_payment_total(lc):
	return get_voucher_link_total(
		lc,
		("Supplier Payment", "Bank Paid Supplier"),
		account=lc.lc_liability_account,
		amount_field="credit",
	)


def get_company_settlement_total(lc):
	return get_voucher_link_total(
		lc,
		("Company Settlement",),
		account=lc.lc_liability_account,
		amount_field="debit",
	)


def get_current_outstanding_liability(lc):
	linked_outstanding = get_supplier_payment_total(lc) - get_company_settlement_total(lc)
	return max(flt(lc.outstanding_liability), linked_outstanding, 0)


def _add_voucher_link(lc, voucher, transaction_type, accounts):
	lc_doc = frappe.get_doc("Letter of Credit", lc.name)
	posting_date = getdate(voucher.posting_date if hasattr(voucher, "posting_date") else today())

	for row in accounts:
		lc_doc.append(
			"voucher_links",
			{
				"posting_date": posting_date,
				"transaction_type": transaction_type,
				"voucher_type": voucher.doctype,
				"voucher_no": voucher.name,
				"account": row["account"],
				"debit": flt(row.get("debit")),
				"credit": flt(row.get("credit")),
				"remarks": voucher.user_remark if hasattr(voucher, "user_remark") else transaction_type,
			},
		)

	lc_doc.flags.ignore_validate = True
	lc_doc.save(ignore_permissions=True)


def post_margin_block(lc_name, amount=None):
	lc = frappe.get_doc("Letter of Credit", lc_name)
	if lc.margin_blocked:
		frappe.throw(_("Margin is already blocked for this L/C."))

	amount = flt(amount) or flt(lc.margin_amount) or flt(lc.lc_amount) * flt(lc.margin_percent) / 100
	if not amount:
		frappe.throw(_("Set Margin Amount or Margin % before blocking margin."))
	validate_amount_within_lc_limit(lc, amount, _("Margin Amount"))

	if not lc.bank_account:
		frappe.throw(_("Bank Account is required to block margin."))

	je = create_journal_entry(
		lc,
		[
			{"account": lc.lc_margin_account, "debit": amount},
			{"account": lc.bank_account, "credit": amount},
		],
		"Margin Block",
	)

	frappe.db.set_value(
		"Letter of Credit",
		lc.name,
		{
			"margin_amount": amount,
			"margin_blocked": 1,
			"status": "Opened" if lc.status in ("Draft", "Requested", "Approved") else lc.status,
		},
		update_modified=False,
	)
	return je


def post_bank_charges(lc_name, charge_row_idx=None, amount=None):
	lc = frappe.get_doc("Letter of Credit", lc_name)
	if not lc.bank_account:
		frappe.throw(_("Bank Account is required."))

	if charge_row_idx is not None:
		row = lc.charges[int(charge_row_idx) - 1]
		if row.get("journal_entry") or row.get("payment_entry"):
			frappe.throw(_("Charge row {0} is already posted.").format(row.idx))
		charge_amount = flt(row.amount)
		charge_currency = row.get("charge_currency") or frappe.get_cached_value("Company", lc.company, "default_currency")
		exchange_rate = flt(row.get("exchange_rate")) or 1
		amount = flt(row.get("base_amount")) or charge_amount * exchange_rate
		charge_type = row.charge_type
		remark = f"{charge_type} charge for {lc.name}: {charge_currency} {charge_amount}"
	else:
		frappe.throw(_("Add a charge row before posting bank charges."))

	if not amount:
		frappe.throw(_("Charge amount is required."))

	je_name = create_journal_entry(
		lc,
		[
			{"account": lc.bank_charges_account, "debit": amount},
			{"account": lc.bank_account, "credit": amount},
		],
		"Bank Charge",
		remark=remark,
	)

	if charge_row_idx is not None:
		frappe.db.set_value(
			"LC Charge",
			row.name,
			"journal_entry",
			je_name,
			update_modified=False,
		)

	return je_name


def post_bank_paid_supplier(lc_name, amount=None):
	"""Bank pays supplier: Dr Supplier Payable, Cr L/C Liability."""
	lc = frappe.get_doc("Letter of Credit", lc_name)
	if get_current_outstanding_liability(lc) > 0:
		frappe.throw(_("Settle the outstanding L/C liability before posting another supplier payment."))
	if not lc.bank_payment_confirmed:
		frappe.throw(_("Bank payment confirmation is required before posting supplier payment."))
	if not lc.bank_payment_confirmation_date:
		frappe.throw(_("Bank Payment Confirmation Date is required before posting supplier payment."))

	remaining_supplier_payment = flt(lc.utilized_amount) - get_supplier_payment_total(lc)
	if remaining_supplier_payment <= 0:
		frappe.throw(_("Supplier Payment is already posted for the current utilized amount."))

	amount = flt(amount) or remaining_supplier_payment
	if not amount:
		frappe.throw(_("No utilized amount to settle with bank."))
	if amount > remaining_supplier_payment:
		frappe.throw(_("Supplier Payment Amount cannot exceed the unposted utilized amount."))
	validate_amount_within_lc_limit(lc, amount, _("Supplier Payment Amount"))

	supplier_account = frappe.get_cached_value("Company", lc.company, "default_payable_account")
	if not supplier_account:
		frappe.throw(_("Set Default Payable Account in Company {0}.").format(lc.company))

	accounts = [
		{
			"account": supplier_account,
			"debit": amount,
			"party_type": "Supplier",
			"party": lc.supplier,
		},
		{"account": lc.lc_liability_account, "credit": amount},
	]
	transaction_type = "Supplier Payment"
	if get_lc_voucher_type("supplier_payment_voucher_type") == "Payment Entry":
		voucher_name = create_payment_entry(
			lc,
			"Pay",
			lc.lc_liability_account,
			supplier_account,
			amount,
			transaction_type,
			party_type="Supplier",
			party=lc.supplier,
			accounts=accounts,
		)
	else:
		voucher_name = create_journal_entry(lc, accounts, transaction_type)

	outstanding_liability = get_current_outstanding_liability(lc) + amount
	frappe.db.set_value(
		"Letter of Credit",
		lc.name,
		{"outstanding_liability": outstanding_liability, "status": "Liability Outstanding"},
		update_modified=False,
	)
	return voucher_name


def post_company_settlement(lc_name, amount=None):
	lc = frappe.get_doc("Letter of Credit", lc_name)
	outstanding_liability = get_current_outstanding_liability(lc)
	amount = flt(amount) or outstanding_liability
	if not amount:
		frappe.throw(_("No outstanding liability to settle."))
	if amount > outstanding_liability:
		frappe.throw(_("Settlement amount cannot exceed outstanding liability."))

	if not lc.bank_account:
		frappe.throw(_("Bank Account is required."))

	accounts = [
		{"account": lc.lc_liability_account, "debit": amount},
		{"account": lc.bank_account, "credit": amount},
	]
	if get_lc_voucher_type("bank_settlement_voucher_type") == "Payment Entry":
		voucher_name = create_payment_entry(
			lc,
			"Internal Transfer",
			lc.bank_account,
			lc.lc_liability_account,
			amount,
			"Company Settlement",
			accounts=accounts,
		)
	else:
		voucher_name = create_journal_entry(lc, accounts, "Company Settlement")

	remaining_liability = outstanding_liability - amount
	frappe.db.set_value(
		"Letter of Credit",
		lc.name,
		{
			"outstanding_liability": remaining_liability,
			"status": "Settled" if not remaining_liability else "Liability Outstanding",
		},
		update_modified=False,
	)
	return voucher_name


def post_margin_release(lc_name, amount=None):
	lc = frappe.get_doc("Letter of Credit", lc_name)
	if not lc.margin_blocked:
		frappe.throw(_("Margin is not blocked for this L/C."))
	if lc.margin_released:
		frappe.throw(_("Margin is already released."))

	amount = flt(amount) or flt(lc.margin_amount)
	if amount != flt(lc.margin_amount):
		frappe.throw(_("Margin release amount must match the blocked margin amount."))
	if not lc.bank_account:
		frappe.throw(_("Bank Account is required."))

	je_name = create_journal_entry(
		lc,
		[
			{"account": lc.bank_account, "debit": amount},
			{"account": lc.lc_margin_account, "credit": amount},
		],
		"Margin Release",
	)

	frappe.db.set_value(
		"Letter of Credit",
		lc.name,
		{"margin_released": 1, "margin_blocked": 0, "status": "Margin Released"},
		update_modified=False,
	)
	return je_name
