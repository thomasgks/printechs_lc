frappe.listview_settings["Letter of Credit"] = {
	add_fields: ["status", "expiry_date", "outstanding_liability"],

	get_indicator(doc) {
		const status_colors = {
			Draft: "grey",
			Requested: "orange",
			Approved: "blue",
			Opened: "blue",
			"In Progress": "yellow",
			Invoiced: "yellow",
			"Supplier Paid": "orange",
			"Liability Outstanding": "red",
			Settled: "green",
			"Margin Released": "green",
			Closed: "green",
			Cancelled: "red",
			Expired: "red",
		};

		const color = status_colors[doc.status] || "grey";
		return [__(doc.status), color, "status,=," + doc.status];
	},
};