import frappe


def has_app_permission():
	return frappe.has_permission("Letter of Credit", ptype="read")
