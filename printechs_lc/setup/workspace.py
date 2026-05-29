import json

import frappe


def create_workspace():
	_upsert_workspace()


def update_workspace():
	_upsert_workspace()


def _upsert_workspace():
	if not frappe.db.exists("DocType", "Letter of Credit"):
		return

	workspace_name = "LC Management"
	content = [
		{"type": "header", "data": {"text": "Letter of Credit", "col": 12}},
		{"type": "shortcut", "data": {"shortcut_name": "Letter of Credit", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "LC Settings", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "LC Ledger", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "Outstanding LC Liability", "col": 3}},
		{"type": "shortcut", "data": {"shortcut_name": "LC Expiry", "col": 3}},
	]

	if frappe.db.exists("Workspace", "Letter of Credit") and not frappe.db.exists(
		"Workspace", workspace_name
	):
		frappe.rename_doc("Workspace", "Letter of Credit", workspace_name, force=True)

	if frappe.db.exists("Workspace", "Letter of Credit") and frappe.db.exists("Workspace", workspace_name):
		frappe.delete_doc("Workspace", "Letter of Credit", force=True, ignore_permissions=True)

	if frappe.db.exists("Workspace", workspace_name):
		doc = frappe.get_doc("Workspace", workspace_name)
	else:
		doc = frappe.new_doc("Workspace")
		doc.name = workspace_name
		doc.title = "Letter of Credit"
		doc.label = "Letter of Credit"
		doc.module = "Printechs LC"
		doc.icon = "loan"
		doc.indicator_color = "blue"
		doc.public = 1
		doc.sequence_id = 15.0

	doc.title = "Letter of Credit"
	doc.label = workspace_name
	doc.is_hidden = 0
	doc.content = json.dumps(content)
	doc.shortcuts = []

	doc.append(
		"shortcuts",
		{
			"type": "URL",
			"label": "Letter of Credit",
			"url": "/app/letter-of-credit/view/list",
		},
	)

	if frappe.db.exists("DocType", "LC Settings"):
		doc.append(
			"shortcuts",
			{
				"type": "DocType",
				"label": "LC Settings",
				"link_to": "LC Settings",
				"doc_view": "",
			},
		)

	for report_name in ("LC Ledger", "Outstanding LC Liability", "LC Expiry"):
		if frappe.db.exists("Report", report_name):
			doc.append(
				"shortcuts",
				{
					"type": "Report",
					"label": report_name,
					"link_to": report_name,
					"report_ref_doctype": "Letter of Credit",
				},
			)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
