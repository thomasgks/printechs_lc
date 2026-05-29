import frappe
from frappe import _
from frappe.utils import flt


def get_lc_limit(lc):
	limit = flt(lc.lc_amount)
	settings = frappe.get_cached_doc("LC Settings")
	if settings.allow_over_utilization and settings.over_utilization_percent:
		limit += limit * flt(settings.over_utilization_percent) / 100
	return limit


def validate_amount_within_lc_limit(lc, amount, label=None):
	limit = get_lc_limit(lc)
	if flt(amount) > limit:
		frappe.throw(
			_("{0} cannot exceed allowed L/C limit. L/C: {1}, Limit: {2}, Amount: {3}").format(
				label or _("Amount"), lc.name, limit, amount
			)
		)


def validate_lc_utilization(letter_of_credit, amount, doctype, docname):
	lc = frappe.get_doc("Letter of Credit", letter_of_credit)
	if lc.status in ("Closed", "Cancelled", "Expired"):
		frappe.throw(_("L/C {0} is {1}. Cannot link {2}.").format(lc.name, lc.status, doctype))

	limit = get_lc_limit(lc)

	# exclude current doc when validating updates
	existing = _get_utilized_excluding(lc.name, doctype, docname)
	if existing + flt(amount) > limit:
		frappe.throw(
			_("Amount exceeds available L/C balance. L/C: {0}, Limit: {1}, Utilized: {2}, This doc: {3}").format(
				lc.name, limit, existing, amount
			)
		)


def _get_utilized_excluding(lc_name, doctype, docname):
	if not frappe.db.has_column("Purchase Invoice", "letter_of_credit"):
		return 0

	total = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(grand_total), 0)
		FROM `tabPurchase Invoice`
		WHERE letter_of_credit = %s AND docstatus = 1 AND name != %s
		""",
		(lc_name, docname if doctype == "Purchase Invoice" else ""),
	)[0][0]
	return flt(total)
