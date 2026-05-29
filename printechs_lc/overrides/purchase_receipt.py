import frappe
from frappe.utils import flt

from printechs_lc.utils.utilization import validate_lc_utilization as validate_lc_amount


def validate_lc_utilization(doc, method=None):
	if not doc.get("letter_of_credit"):
		return

	total = sum(flt(row.amount) for row in doc.items)
	validate_lc_amount(doc.letter_of_credit, total, "Purchase Receipt", doc.name)
