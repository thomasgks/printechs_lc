import frappe

from printechs_lc.setup.custom_fields import setup_custom_fields
from printechs_lc.setup.print_formats import setup_print_formats
from printechs_lc.setup.property_setters import setup_property_setters
from printechs_lc.setup.workspace import create_workspace


def after_install():
	after_migrate()


def after_migrate():
	setup_custom_fields()
	setup_property_setters()
	setup_print_formats()
	create_workspace()
	from printechs_lc.setup.workspace import update_workspace

	update_workspace()
	frappe.clear_cache()


def before_uninstall():
	pass
