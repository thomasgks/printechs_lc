app_name = "printechs_lc"
app_title = "Printechs Letter of Credit"
app_publisher = "Printechs"
app_description = "Letter of Credit management for ERPNext"
app_email = "sakeer@printechs.com"
app_license = "mit"
required_apps = ["erpnext"]

add_to_apps_screen = [
	{
		"name": "printechs_lc",
		"logo": "/assets/printechs_lc/images/lc-icon.svg",
		"title": "Letter of Credit",
		"route": "/app/lc-management",
		"has_permission": "printechs_lc.api.permission.has_app_permission",
	}
]

after_install = "printechs_lc.install.after_install"
after_migrate = ["printechs_lc.install.after_migrate"]

doctype_js = {
	"Letter of Credit": "public/js/letter_of_credit.js",
	"Purchase Order": "public/js/purchase_order_lc.js",
}


doctype_tree_js = {
	"Account": "public/js/account_tree_lc.js",
}
doctype_list_js = {
	"Letter of Credit": "public/js/letter_of_credit_list.js",
}

doc_events = {
	"Letter of Credit": {
		"validate": "printechs_lc.validations.validate_letter_of_credit",
	},
	"Purchase Invoice": {
		"validate": "printechs_lc.overrides.purchase_invoice.validate_lc_utilization",
	},
	"Purchase Receipt": {
		"validate": "printechs_lc.overrides.purchase_receipt.validate_lc_utilization",
	},
}

scheduler_events = {
	"daily": [
		"printechs_lc.tasks.send_lc_expiry_and_maturity_alerts",
	],
}

# Custom fields are created in install.setup_custom_fields()
