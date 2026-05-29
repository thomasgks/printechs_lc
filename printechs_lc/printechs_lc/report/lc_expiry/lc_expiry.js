frappe.query_reports["LC Expiry"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "days",
			label: __("Days Ahead"),
			fieldtype: "Int",
			default: 30,
		},
	],
};
