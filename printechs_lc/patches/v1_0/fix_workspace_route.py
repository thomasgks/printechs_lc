import frappe

from printechs_lc.setup.workspace import update_workspace


def execute():
	update_workspace()
	frappe.clear_cache()
