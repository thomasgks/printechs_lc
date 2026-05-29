frappe.provide("frappe.treeview_settings");

const account_tree_settings =
	frappe.treeview_settings["Account"] || (frappe.treeview_settings["Account"] = {});

const original_onload = account_tree_settings.onload;
const original_on_get_node = account_tree_settings.on_get_node;
const original_toolbar = (account_tree_settings.toolbar || []).slice();

account_tree_settings.onload = function (treeview) {
	if (original_onload) {
		original_onload(treeview);
	}

	treeview.page.add_inner_button(
		__("L/C Ledger"),
		function () {
			const company = treeview.page.fields_dict.company.get_value();
			const node = treeview.tree.get_selected_node();
			const account = node && !node.root ? node.data.value : null;

			frappe.route_options = { company };
			if (account) {
				frappe.route_options.account = account;
			}
			frappe.set_route("query-report", "LC Ledger");
		},
		__("View")
	);
};

const has_lc_toolbar = original_toolbar.some((t) => t.label === __("Open L/C"));
if (!has_lc_toolbar) {
	original_toolbar.push({
		label: __("Open L/C"),
		condition(node) {
			return !node.root && node.data && node.data.is_lc_control_account;
		},
		click(node) {
			frappe.route_options = {
				company: account_tree_settings.treeview.page.fields_dict.company.get_value(),
				account: node.data.value,
			};
			frappe.set_route("query-report", "LC Ledger");
		},
		btnClass: "hidden-xs",
	});
}

account_tree_settings.toolbar = original_toolbar;

account_tree_settings.on_get_node = function (nodes, deep) {
	if (original_on_get_node) {
		original_on_get_node(nodes, deep);
	}

	const accounts = deep
		? nodes.reduce((acc, node) => [...acc, ...(node.data || [])], [])
		: nodes;

	if (!accounts || !accounts.length) return;

	const names = accounts.map((a) => (typeof a === "string" ? a : a.value)).filter(Boolean);
	frappe.call({
		method: "printechs_lc.api.account_tree.get_lc_account_flags",
		args: { accounts: names },
		callback(r) {
			if (!r.message) return;
			for (const [account, flags] of Object.entries(r.message)) {
				const node = cur_tree.nodes && cur_tree.nodes[account];
				if (node && node.data) {
					node.data.is_lc_control_account = flags.is_lc_control_account;
				}
			}
		},
	});
};
