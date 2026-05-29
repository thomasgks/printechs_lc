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
