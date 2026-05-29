import frappe
from frappe import _
from frappe.utils import add_days, today


def execute(filters=None):
	filters = filters or {}
	days = int(filters.get("days") or 30)
	until = add_days(today(), days)

	columns = [
		{"label": _("L/C"), "fieldname": "name", "fieldtype": "Link", "options": "Letter of Credit", "width": 130},
		{"label": _("Bank L/C No"), "fieldname": "lc_bank_number", "fieldtype": "Data", "width": 120},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 120},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 100},
		{"label": _("Amount"), "fieldname": "lc_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Available"), "fieldname": "available_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
	]

	filters_dict = {
		"docstatus": 1,
		"status": ["not in", ["Closed", "Cancelled"]],
		"expiry_date": ["between", [today(), until]],
	}
	if filters.get("company"):
		filters_dict["company"] = filters["company"]

	data = frappe.get_all(
		"Letter of Credit",
		filters=filters_dict,
		fields=["name", "lc_bank_number", "supplier", "expiry_date", "lc_amount", "available_amount", "status"],
		order_by="expiry_date asc",
	)
	return columns, data
