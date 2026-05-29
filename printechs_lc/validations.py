import frappe
from frappe import _


def validate_letter_of_credit(doc, method=None):
	validate_lc_bank_number(doc)


def validate_lc_bank_number(doc):
	if not doc.get("lc_bank_number"):
		frappe.throw(_("Bank L/C Number is mandatory."))

	existing = frappe.db.get_value(
		"Letter of Credit",
		{
			"lc_bank_number": doc.lc_bank_number,
			"name": ["!=", doc.name],
		},
		"name",
	)
	if existing:
		frappe.throw(_("Bank L/C Number {0} is already used in {1}.").format(doc.lc_bank_number, existing))
