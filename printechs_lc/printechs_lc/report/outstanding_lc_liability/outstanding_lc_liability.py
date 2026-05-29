import frappe
from frappe import _


def execute(filters=None):
	columns = [
		{"label": _("L/C"), "fieldname": "name", "fieldtype": "Link", "options": "Letter of Credit", "width": 130},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 120},
		{"label": _("Type"), "fieldname": "lc_type", "fieldtype": "Data", "width": 90},
		{"label": _("Outstanding"), "fieldname": "outstanding_liability", "fieldtype": "Currency", "width": 120},
		{"label": _("Maturity Date"), "fieldname": "maturity_date", "fieldtype": "Date", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]

	filters_dict = {
		"docstatus": 1,
		"outstanding_liability": [">", 0],
	}
	if filters and filters.get("company"):
		filters_dict["company"] = filters["company"]

	data = frappe.get_all(
		"Letter of Credit",
		filters=filters_dict,
		fields=["name", "supplier", "lc_type", "outstanding_liability", "maturity_date", "status"],
		order_by="maturity_date asc",
	)
	return columns, data
