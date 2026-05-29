import frappe
from frappe import _
from frappe.utils import flt

from printechs_lc.utils.utilization import validate_lc_utilization as validate_lc_amount


def validate_lc_utilization(doc, method=None):
	if not doc.get("letter_of_credit"):
		return
	validate_lc_amount(doc.letter_of_credit, flt(doc.grand_total), "Purchase Invoice", doc.name)
