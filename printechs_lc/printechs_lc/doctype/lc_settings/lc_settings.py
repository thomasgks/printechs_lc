import frappe
from frappe.model.document import Document


class LCSettings(Document):
	pass


def get_company_defaults(company):
	settings = frappe.get_cached_doc("LC Settings")
	for row in settings.company_lc_defaults or []:
		if row.company == company:
			return row
	return None


@frappe.whitelist()
def get_lc_company_defaults(company):
	defaults = get_company_defaults(company)
	if not defaults:
		return {}

	return {
		"lc_margin_account": defaults.lc_margin_account,
		"lc_liability_account": defaults.lc_liability_account,
		"bank_charges_account": defaults.bank_charges_account,
		"bank_account": defaults.default_bank_account,
	}
