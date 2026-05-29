import frappe


def setup_property_setters():
	set_lc_bank_number_rules()


def set_lc_bank_number_rules():
	if not frappe.db.exists("DocType", "Letter of Credit"):
		return

	_set_property(
		doctype="Letter of Credit",
		fieldname="lc_bank_number",
		property_name="reqd",
		value="1",
		property_type="Check",
	)
	_set_property(
		doctype="Letter of Credit",
		fieldname="lc_bank_number",
		property_name="unique",
		value="1",
		property_type="Check",
	)
	frappe.clear_cache(doctype="Letter of Credit")


def _set_property(doctype, fieldname, property_name, value, property_type):
	name = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": doctype,
			"doctype_or_field": "DocField",
			"field_name": fieldname,
			"property": property_name,
		},
	)

	if name:
		frappe.db.set_value(
			"Property Setter",
			name,
			{
				"value": value,
				"property_type": property_type,
			},
			update_modified=False,
		)
		return

	frappe.get_doc(
		{
			"doctype": "Property Setter",
			"doc_type": doctype,
			"doctype_or_field": "DocField",
			"field_name": fieldname,
			"property": property_name,
			"value": value,
			"property_type": property_type,
		}
	).insert(ignore_permissions=True)
