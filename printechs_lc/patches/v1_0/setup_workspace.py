import frappe

from printechs_lc.setup.workspace import create_workspace


def execute():
	create_workspace()
	frappe.db.commit()
