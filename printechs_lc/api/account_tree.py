import frappe


@frappe.whitelist()
def get_lc_account_flags(accounts):
	if isinstance(accounts, str):
		import json

		accounts = json.loads(accounts)

	result = {}
	for account in accounts:
		flags = frappe.db.get_value(
			"Account",
			account,
			["is_lc_control_account", "lc_account_role"],
			as_dict=True,
		)
		result[account] = flags or {"is_lc_control_account": 0, "lc_account_role": None}

	return result
