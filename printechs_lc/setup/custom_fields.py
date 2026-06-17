import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
	"Purchase Order": [
		{
			"fieldname": "lc_required",
			"fieldtype": "Check",
			"insert_after": "payment_terms_template",
			"label": "L/C Required",
		},
		{
			"fieldname": "letter_of_credit",
			"fieldtype": "Link",
			"insert_after": "lc_required",
			"label": "Letter of Credit",
			"options": "Letter of Credit",
		},
	],
	"Purchase Receipt": [
		{
			"fieldname": "letter_of_credit",
			"fieldtype": "Link",
			"insert_after": "supplier",
			"label": "Letter of Credit",
			"options": "Letter of Credit",
		},
	],
	"Purchase Invoice": [
		{
			"fieldname": "letter_of_credit",
			"fieldtype": "Link",
			"insert_after": "supplier",
			"label": "Letter of Credit",
			"options": "Letter of Credit",
		},
		{
			"fieldname": "lc_payment_status",
			"fieldtype": "Select",
			"insert_after": "letter_of_credit",
			"label": "L/C Payment Status",
			"options": "\nPending\nBank Paid\nSettled",
		},
	],
	"Journal Entry": [
		{
			"fieldname": "letter_of_credit",
			"fieldtype": "Link",
			"insert_after": "company",
			"label": "Letter of Credit",
			"options": "Letter of Credit",
		},
		{
			"fieldname": "lc_transaction_type",
			"fieldtype": "Select",
			"insert_after": "letter_of_credit",
			"label": "L/C Transaction Type",
			"options": "\nMargin Block\nBank Charge\nSupplier Invoice\nSupplier Payment\nBank Paid Supplier\nCompany Settlement\nMargin Release\nAmendment Charge\nOther",
		},
	],
	"Payment Entry": [
		{
			"fieldname": "letter_of_credit",
			"fieldtype": "Link",
			"insert_after": "company",
			"label": "Letter of Credit",
			"options": "Letter of Credit",
		},
		{
			"fieldname": "lc_settlement_type",
			"fieldtype": "Select",
			"insert_after": "letter_of_credit",
			"label": "L/C Settlement Type",
			"options": "\nMargin Block\nBank Charge\nSupplier Payment\nBank Paid Supplier\nCompany Settlement\nMargin Release\nOther",
		},
	],
	"Account": [
		{
			"fieldname": "is_lc_control_account",
			"fieldtype": "Check",
			"insert_after": "account_type",
			"label": "Is L/C Control Account",
		},
		{
			"fieldname": "lc_account_role",
			"fieldtype": "Select",
			"insert_after": "is_lc_control_account",
			"label": "L/C Account Role",
			"options": "\nMargin\nLiability\nCharges",
		},
	],
}


def setup_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, update=True)
	for dt in CUSTOM_FIELDS:
		frappe.clear_cache(doctype=dt)
