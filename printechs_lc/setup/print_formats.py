import frappe


LC_PRINT_FORMAT_NAME = "LC Management Summary"


LC_MANAGEMENT_SUMMARY_HTML = """
{% set status_class = (doc.status or "Draft").lower().replace(" ", "-") %}
{% set total_charges = doc.charges | sum(attribute="base_amount") if doc.charges else 0 %}
{% set posted_charges = doc.charges | selectattr("journal_entry") | list | length if doc.charges else 0 %}
{% set verified_docs = doc.documents | selectattr("status", "equalto", "Verified") | list | length if doc.documents else 0 %}

<style>
	.lc-print {
		font-family: "Inter", "Segoe UI", Arial, sans-serif;
		color: #172033;
		font-size: 11px;
		line-height: 1.45;
	}
	.lc-topbar {
		border-bottom: 3px solid #1f4e79;
		padding-bottom: 14px;
		margin-bottom: 18px;
		display: table;
		width: 100%;
	}
	.lc-title-wrap, .lc-status-wrap {
		display: table-cell;
		vertical-align: top;
	}
	.lc-title {
		font-size: 24px;
		font-weight: 800;
		letter-spacing: .01em;
		color: #1f4e79;
		margin: 0;
	}
	.lc-subtitle {
		color: #64748b;
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: .09em;
		margin-top: 4px;
	}
	.lc-status-wrap {
		text-align: right;
		width: 30%;
	}
	.lc-badge {
		display: inline-block;
		border-radius: 999px;
		padding: 7px 14px;
		font-weight: 800;
		font-size: 11px;
		color: #fff;
		background: #64748b;
		text-transform: uppercase;
		letter-spacing: .05em;
	}
	.lc-badge.opened, .lc-badge.margin-released, .lc-badge.settled, .lc-badge.closed { background: #15803d; }
	.lc-badge.liability-outstanding, .lc-badge.in-progress { background: #b45309; }
	.lc-badge.cancelled, .lc-badge.expired { background: #b91c1c; }
	.lc-meta {
		margin-top: 9px;
		color: #64748b;
		font-size: 10px;
	}
	.lc-card-row {
		display: table;
		width: 100%;
		table-layout: fixed;
		margin: 14px 0 18px;
	}
	.lc-card {
		display: table-cell;
		background: #f8fafc;
		border: 1px solid #dbe4ee;
		border-left: 4px solid #1f4e79;
		border-radius: 4px;
		padding: 10px 12px;
		vertical-align: top;
	}
	.lc-card + .lc-card { border-left-width: 4px; }
	.lc-card-label {
		color: #64748b;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: .06em;
		font-weight: 700;
	}
	.lc-card-value {
		font-size: 15px;
		font-weight: 800;
		color: #0f172a;
		margin-top: 4px;
	}
	.lc-section {
		margin-top: 18px;
		page-break-inside: avoid;
	}
	.lc-section-title {
		font-size: 12px;
		color: #1f4e79;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: .08em;
		border-bottom: 1px solid #cbd5e1;
		padding-bottom: 5px;
		margin-bottom: 8px;
	}
	.lc-grid {
		width: 100%;
		border-collapse: collapse;
		table-layout: fixed;
	}
	.lc-grid td {
		border: 1px solid #e2e8f0;
		padding: 7px 9px;
		vertical-align: top;
	}
	.lc-label {
		width: 22%;
		background: #f8fafc;
		color: #64748b;
		font-weight: 700;
	}
	.lc-value {
		width: 28%;
		color: #0f172a;
		font-weight: 600;
	}
	.lc-table {
		width: 100%;
		border-collapse: collapse;
		table-layout: fixed;
		font-size: 10.5px;
	}
	.lc-table th {
		background: #1f4e79;
		color: #fff;
		font-weight: 800;
		text-align: left;
		border: 1px solid #1f4e79;
		padding: 7px 8px;
	}
	.lc-table td {
		border: 1px solid #dbe4ee;
		padding: 6px 8px;
		vertical-align: top;
	}
	.lc-table tr:nth-child(even) td { background: #fafafa; }
	.text-right { text-align: right; }
	.text-center { text-align: center; }
	.lc-muted { color: #94a3b8; }
	.lc-note {
		background: #f8fafc;
		border: 1px solid #dbe4ee;
		padding: 10px 12px;
		min-height: 44px;
	}
	.lc-signatures {
		display: table;
		width: 100%;
		table-layout: fixed;
		margin-top: 36px;
	}
	.lc-signature {
		display: table-cell;
		padding: 0 12px;
		text-align: center;
	}
	.lc-sign-line {
		border-top: 1px solid #475569;
		padding-top: 7px;
		font-weight: 700;
		color: #334155;
	}
	.lc-footer {
		margin-top: 24px;
		border-top: 1px solid #e2e8f0;
		padding-top: 8px;
		font-size: 9px;
		color: #94a3b8;
		text-align: center;
	}
	@media print {
		.lc-print { font-size: 10.5px; }
		.lc-section { page-break-inside: avoid; }
	}
</style>

<div class="lc-print">
	<div class="lc-topbar">
		<div class="lc-title-wrap">
			<h1 class="lc-title">{{ _("Letter of Credit Summary") }}</h1>
			<div class="lc-subtitle">
				{{ doc.company }} &nbsp; | &nbsp; {{ doc.name }} &nbsp; | &nbsp; Bank L/C No: {{ doc.lc_bank_number or "—" }}
			</div>
		</div>
		<div class="lc-status-wrap">
			<span class="lc-badge {{ status_class }}">{{ doc.status or _("Draft") }}</span>
			<div class="lc-meta">{{ _("Printed") }}: {{ frappe.utils.formatdate(frappe.utils.today()) }}</div>
		</div>
	</div>

	<div class="lc-card-row">
		<div class="lc-card">
			<div class="lc-card-label">{{ _("L/C Amount") }}</div>
			<div class="lc-card-value">{{ doc.get_formatted("lc_amount") or "—" }}</div>
			<div class="lc-muted">{{ _("Base") }}: {{ doc.get_formatted("base_lc_amount") or "0" }}</div>
		</div>
		<div class="lc-card">
			<div class="lc-card-label">{{ _("Utilized") }}</div>
			<div class="lc-card-value">{{ doc.get_formatted("utilized_amount") or "0" }}</div>
			<div class="lc-muted">{{ _("Base") }}: {{ doc.get_formatted("base_utilized_amount") or "0" }}</div>
		</div>
		<div class="lc-card">
			<div class="lc-card-label">{{ _("Available") }}</div>
			<div class="lc-card-value">{{ doc.get_formatted("available_amount") or "0" }}</div>
			<div class="lc-muted">{{ _("Base") }}: {{ doc.get_formatted("base_available_amount") or "0" }}</div>
		</div>
		<div class="lc-card">
			<div class="lc-card-label">{{ _("Outstanding Liability") }}</div>
			<div class="lc-card-value">{{ doc.get_formatted("outstanding_liability") or "0" }}</div>
		</div>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("1. L/C Header") }}</div>
		<table class="lc-grid">
			<tr>
				<td class="lc-label">{{ _("Supplier / Beneficiary") }}</td>
				<td class="lc-value">{{ doc.supplier or "—" }}</td>
				<td class="lc-label">{{ _("L/C Type") }}</td>
				<td class="lc-value">{{ doc.lc_type or "—" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Purchase Order") }}</td>
				<td class="lc-value">{{ doc.purchase_order or "—" }}</td>
				<td class="lc-label">{{ _("Currency / Exchange Rate") }}</td>
				<td class="lc-value">{{ doc.currency or "—" }} / {{ doc.exchange_rate or "—" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Opening Date") }}</td>
				<td class="lc-value">{{ doc.get_formatted("opening_date") if doc.opening_date else "—" }}</td>
				<td class="lc-label">{{ _("Expiry Date") }}</td>
				<td class="lc-value">{{ doc.get_formatted("expiry_date") if doc.expiry_date else "—" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Latest Shipment Date") }}</td>
				<td class="lc-value">{{ doc.get_formatted("latest_shipment_date") if doc.latest_shipment_date else "—" }}</td>
				<td class="lc-label">{{ _("Maturity Date") }}</td>
				<td class="lc-value">{{ doc.get_formatted("maturity_date") if doc.maturity_date else "—" }}</td>
			</tr>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("2. Bank & Facility Details") }}</div>
		<table class="lc-grid">
			<tr>
				<td class="lc-label">{{ _("Issuing Bank") }}</td>
				<td class="lc-value">{{ doc.issuing_bank or "—" }}</td>
				<td class="lc-label">{{ _("Advising Bank") }}</td>
				<td class="lc-value">{{ doc.advising_bank or "—" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Confirming Bank") }}</td>
				<td class="lc-value">{{ doc.confirming_bank or "—" }}</td>
				<td class="lc-label">{{ _("Bank Reference") }}</td>
				<td class="lc-value">{{ doc.bank_reference or "—" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Incoterms") }}</td>
				<td class="lc-value">{{ doc.incoterms or "—" }}</td>
				<td class="lc-label">{{ _("Bank Payment Confirmed") }}</td>
				<td class="lc-value">{{ _("Yes") if doc.bank_payment_confirmed else _("No") }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Confirmation Date") }}</td>
				<td class="lc-value">{{ doc.get_formatted("bank_payment_confirmation_date") if doc.bank_payment_confirmation_date else "—" }}</td>
				<td class="lc-label">{{ _("Payment Reference") }}</td>
				<td class="lc-value">{{ doc.bank_payment_reference or "—" }}</td>
			</tr>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("3. Amounts, Margin & Control Accounts") }}</div>
		<table class="lc-grid">
			<tr>
				<td class="lc-label">{{ _("Margin %") }}</td>
				<td class="lc-value">{{ doc.margin_percent or 0 }}%</td>
				<td class="lc-label">{{ _("Margin Amount") }}</td>
				<td class="lc-value">{{ doc.get_formatted("margin_amount") or "0" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Zero Margin Allowed") }}</td>
				<td class="lc-value">{{ _("Yes") if doc.allow_zero_margin else _("No") }}</td>
				<td class="lc-label">{{ _("Margin Status") }}</td>
				<td class="lc-value">{{ _("Blocked") if doc.margin_blocked else _("Not Blocked") }} / {{ _("Released") if doc.margin_released else _("Not Released") }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Bank Account") }}</td>
				<td class="lc-value">{{ doc.bank_account or "—" }}</td>
				<td class="lc-label">{{ _("Margin Account") }}</td>
				<td class="lc-value">{{ doc.lc_margin_account or "—" }}</td>
			</tr>
			<tr>
				<td class="lc-label">{{ _("Liability Account") }}</td>
				<td class="lc-value">{{ doc.lc_liability_account or "—" }}</td>
				<td class="lc-label">{{ _("Bank Charges Account") }}</td>
				<td class="lc-value">{{ doc.bank_charges_account or "—" }}</td>
			</tr>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("4. Charges") }} <span class="lc-muted">({{ posted_charges }}/{{ doc.charges|length if doc.charges else 0 }} posted, {{ frappe.utils.fmt_money(total_charges, currency=doc.currency) }})</span></div>
		<table class="lc-table">
			<thead>
				<tr>
					<th style="width: 13%;">{{ _("Date") }}</th>
					<th style="width: 15%;">{{ _("Type") }}</th>
					<th style="width: 12%;">{{ _("Currency") }}</th>
					<th style="width: 14%;" class="text-right">{{ _("Amount") }}</th>
					<th style="width: 12%;" class="text-right">{{ _("Rate") }}</th>
					<th style="width: 14%;" class="text-right">{{ _("Base Amount") }}</th>
					<th style="width: 20%;">{{ _("Journal Entry") }}</th>
				</tr>
			</thead>
			<tbody>
				{% for row in doc.charges %}
				<tr>
					<td>{{ frappe.utils.formatdate(row.charge_date) if row.charge_date else "—" }}</td>
					<td>{{ row.charge_type or "—" }}</td>
					<td>{{ row.charge_currency or doc.currency or "—" }}</td>
					<td class="text-right">{{ row.get_formatted("amount") if row.amount else "0" }}</td>
					<td class="text-right">{{ row.exchange_rate or 1 }}</td>
					<td class="text-right">{{ row.get_formatted("base_amount") if row.base_amount else "0" }}</td>
					<td>{{ row.journal_entry or "—" }}</td>
				</tr>
				{% else %}
				<tr><td colspan="7" class="text-center lc-muted">{{ _("No charges recorded") }}</td></tr>
				{% endfor %}
			</tbody>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("5. Shipments") }}</div>
		<table class="lc-table">
			<thead>
				<tr>
					<th>{{ _("Shipment Date") }}</th>
					<th>{{ _("Bill of Lading") }}</th>
					<th>{{ _("Vessel / Flight") }}</th>
					<th>{{ _("Ports") }}</th>
					<th>{{ _("ETA") }}</th>
					<th class="text-right">{{ _("Shipped Amount") }}</th>
					<th class="text-right">{{ _("Received Amount") }}</th>
				</tr>
			</thead>
			<tbody>
				{% for row in doc.shipments %}
				<tr>
					<td>{{ frappe.utils.formatdate(row.shipment_date) if row.shipment_date else "—" }}</td>
					<td>{{ row.bill_of_lading or "—" }}</td>
					<td>{{ row.vessel or "—" }}</td>
					<td>{{ row.port_of_loading or "—" }} → {{ row.port_of_discharge or "—" }}</td>
					<td>{{ frappe.utils.formatdate(row.eta) if row.eta else "—" }}</td>
					<td class="text-right">{{ row.get_formatted("shipped_amount") if row.shipped_amount else "0" }}</td>
					<td class="text-right">{{ row.get_formatted("received_amount") if row.received_amount else "0" }}</td>
				</tr>
				{% else %}
				<tr><td colspan="7" class="text-center lc-muted">{{ _("No shipments recorded") }}</td></tr>
				{% endfor %}
			</tbody>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("6. Documents") }} <span class="lc-muted">({{ verified_docs }}/{{ doc.documents|length if doc.documents else 0 }} verified)</span></div>
		<table class="lc-table">
			<thead>
				<tr>
					<th>{{ _("Document Type") }}</th>
					<th>{{ _("Document No") }}</th>
					<th>{{ _("Received Date") }}</th>
					<th>{{ _("Status") }}</th>
					<th>{{ _("Attachment") }}</th>
				</tr>
			</thead>
			<tbody>
				{% for row in doc.documents %}
				<tr>
					<td>{{ row.document_type or "—" }}</td>
					<td>{{ row.document_no or "—" }}</td>
					<td>{{ frappe.utils.formatdate(row.received_date) if row.received_date else "—" }}</td>
					<td>{{ row.status or "—" }}</td>
					<td>{{ _("Attached") if row.attach else "—" }}</td>
				</tr>
				{% else %}
				<tr><td colspan="5" class="text-center lc-muted">{{ _("No documents recorded") }}</td></tr>
				{% endfor %}
			</tbody>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("7. Amendments") }}</div>
		<table class="lc-table">
			<thead>
				<tr>
					<th>{{ _("Date") }}</th>
					<th>{{ _("Type") }}</th>
					<th>{{ _("Previous Value") }}</th>
					<th>{{ _("New Value") }}</th>
					<th class="text-right">{{ _("Charge") }}</th>
					<th>{{ _("Journal Entry") }}</th>
				</tr>
			</thead>
			<tbody>
				{% for row in doc.amendments %}
				<tr>
					<td>{{ frappe.utils.formatdate(row.amendment_date) if row.amendment_date else "—" }}</td>
					<td>{{ row.amendment_type or "—" }}</td>
					<td>{{ row.previous_value or "—" }}</td>
					<td>{{ row.new_value or "—" }}</td>
					<td class="text-right">{{ row.get_formatted("charge_amount") if row.charge_amount else "0" }}</td>
					<td>{{ row.journal_entry or "—" }}</td>
				</tr>
				{% else %}
				<tr><td colspan="6" class="text-center lc-muted">{{ _("No amendments recorded") }}</td></tr>
				{% endfor %}
			</tbody>
		</table>
	</div>

	<div class="lc-section">
		<div class="lc-section-title">{{ _("8. Linked Accounting Vouchers") }}</div>
		<table class="lc-table">
			<thead>
				<tr>
					<th>{{ _("Posting Date") }}</th>
					<th>{{ _("Transaction") }}</th>
					<th>{{ _("Voucher") }}</th>
					<th>{{ _("Account") }}</th>
					<th class="text-right">{{ _("Debit") }}</th>
					<th class="text-right">{{ _("Credit") }}</th>
				</tr>
			</thead>
			<tbody>
				{% for row in doc.voucher_links %}
				<tr>
					<td>{{ frappe.utils.formatdate(row.posting_date) if row.posting_date else "—" }}</td>
					<td>{{ row.transaction_type or "—" }}</td>
					<td>{{ row.voucher_type or "—" }} {{ row.voucher_no or "" }}</td>
					<td>{{ row.account or "—" }}</td>
					<td class="text-right">{{ row.get_formatted("debit") if row.debit else "0" }}</td>
					<td class="text-right">{{ row.get_formatted("credit") if row.credit else "0" }}</td>
				</tr>
				{% else %}
				<tr><td colspan="6" class="text-center lc-muted">{{ _("No linked vouchers recorded") }}</td></tr>
				{% endfor %}
			</tbody>
		</table>
	</div>

	{% if doc.remarks %}
	<div class="lc-section">
		<div class="lc-section-title">{{ _("9. Remarks") }}</div>
		<div class="lc-note">{{ doc.remarks }}</div>
	</div>
	{% endif %}

	<div class="lc-signatures">
		<div class="lc-signature"><div class="lc-sign-line">{{ _("Prepared By") }}</div></div>
		<div class="lc-signature"><div class="lc-sign-line">{{ _("Accounts Review") }}</div></div>
		<div class="lc-signature"><div class="lc-sign-line">{{ _("Management Approval") }}</div></div>
	</div>

	<div class="lc-footer">
		{{ _("Generated from ERPNext / Printechs LC") }} · {{ doc.name }} · {{ _("This report is system generated and intended for management and accounting review.") }}
	</div>
</div>
"""


def setup_print_formats():
	if not frappe.db.exists("DocType", "Letter of Credit"):
		return

	doc = (
		frappe.get_doc("Print Format", LC_PRINT_FORMAT_NAME)
		if frappe.db.exists("Print Format", LC_PRINT_FORMAT_NAME)
		else frappe.new_doc("Print Format")
	)
	doc.update(
		{
			"name": LC_PRINT_FORMAT_NAME,
			"print_format_for": "DocType",
			"doc_type": "Letter of Credit",
			"module": "Printechs LC",
			"standard": "No",
			"custom_format": 1,
			"print_format_type": "Jinja",
			"disabled": 0,
			"html": LC_MANAGEMENT_SUMMARY_HTML,
			"font_size": 10,
			"margin_top": 8,
			"margin_bottom": 8,
			"margin_left": 8,
			"margin_right": 8,
			"page_number": "Bottom Center",
		}
	)
	doc.save(ignore_permissions=True)
	set_default_lc_print_format()
	frappe.clear_cache(doctype="Letter of Credit")


def set_default_lc_print_format():
	name = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": "Letter of Credit",
			"doctype_or_field": "DocType",
			"property": "default_print_format",
		},
	)
	values = {
		"doctype": "Property Setter",
		"doc_type": "Letter of Credit",
		"doctype_or_field": "DocType",
		"property": "default_print_format",
		"value": LC_PRINT_FORMAT_NAME,
		"property_type": "Data",
	}
	if name:
		frappe.db.set_value(
			"Property Setter",
			name,
			{
				"doc_type": values["doc_type"],
				"doctype_or_field": values["doctype_or_field"],
				"property": values["property"],
				"value": values["value"],
				"property_type": values["property_type"],
			},
			update_modified=False,
		)
	else:
		frappe.get_doc(values).insert(ignore_permissions=True)
