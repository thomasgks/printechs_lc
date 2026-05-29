import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("L/C No"), "fieldname": "letter_of_credit", "fieldtype": "Link", "options": "Letter of Credit", "width": 130},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 120},
		{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 180},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
		{"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 130},
		{"label": _("Transaction Type"), "fieldname": "transaction_type", "fieldtype": "Data", "width": 140},
		{"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 110},
		{"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 110},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 110},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 200},
	]


def get_data(filters):
	conditions = ["gle.is_cancelled = 0"]
	values = {}

	if filters.get("company"):
		conditions.append("gle.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("account"):
		conditions.append("gle.account = %(account)s")
		values["account"] = filters["account"]

	if filters.get("from_date"):
		conditions.append("gle.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("gle.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	lc_filter = ""
	if filters.get("letter_of_credit"):
		lc_filter = "AND lc.name = %(letter_of_credit)s"
		values["letter_of_credit"] = filters["letter_of_credit"]

	if filters.get("supplier"):
		lc_filter += " AND lc.supplier = %(supplier)s"
		values["supplier"] = filters["supplier"]

	# GL entries for LC-linked journal entries and payment entries, plus LC control accounts
	rows = frappe.db.sql(
		f"""
		SELECT
			gle.posting_date,
			COALESCE(je.letter_of_credit, pe.letter_of_credit, pi.letter_of_credit) AS letter_of_credit,
			lc.supplier,
			gle.account,
			gle.voucher_type,
			gle.voucher_no,
			COALESCE(je.lc_transaction_type, pe.lc_settlement_type, '') AS transaction_type,
			gle.debit,
			gle.credit,
			gle.remarks
		FROM `tabGL Entry` gle
		LEFT JOIN `tabJournal Entry` je
			ON gle.voucher_type = 'Journal Entry' AND gle.voucher_no = je.name
		LEFT JOIN `tabPayment Entry` pe
			ON gle.voucher_type = 'Payment Entry' AND gle.voucher_no = pe.name
		LEFT JOIN `tabPurchase Invoice` pi
			ON gle.voucher_type = 'Purchase Invoice' AND gle.voucher_no = pi.name
		LEFT JOIN `tabLetter of Credit` lc
			ON lc.name = COALESCE(je.letter_of_credit, pe.letter_of_credit, pi.letter_of_credit)
		WHERE {" AND ".join(conditions)}
			AND (
				je.letter_of_credit IS NOT NULL
				OR pe.letter_of_credit IS NOT NULL
				OR pi.letter_of_credit IS NOT NULL
				OR gle.account IN (
					SELECT name FROM `tabAccount`
					WHERE is_lc_control_account = 1
					{account_company_filter(filters)}
				)
			)
			{lc_filter}
		ORDER BY gle.posting_date, gle.creation
		""",
		values,
		as_dict=True,
	)

	# Also include voucher_links from Letter of Credit when GL might not have custom fields yet
	if filters.get("letter_of_credit"):
		rows.extend(_get_voucher_link_rows(filters))

	rows.sort(key=lambda r: (r.posting_date or "", r.voucher_no or ""))

	balance = 0
	for row in rows:
		balance += flt(row.debit) - flt(row.credit)
		row["balance"] = balance

	return rows


def account_company_filter(filters):
	if not filters.get("company"):
		return ""
	return " AND company = %(company)s"


def _get_voucher_link_rows(filters):
	lc = frappe.get_doc("Letter of Credit", filters["letter_of_credit"])
	rows = []
	for link in lc.voucher_links or []:
		if filters.get("account") and link.account != filters["account"]:
			continue
		rows.append(
			{
				"posting_date": link.posting_date,
				"letter_of_credit": lc.name,
				"supplier": lc.supplier,
				"account": link.account,
				"voucher_type": link.voucher_type,
				"voucher_no": link.voucher_no,
				"transaction_type": link.transaction_type,
				"debit": link.debit,
				"credit": link.credit,
				"remarks": link.remarks,
			}
		)
	return rows
