import frappe
from frappe.utils import add_days, getdate, today


def send_lc_expiry_and_maturity_alerts():
	settings = frappe.get_cached_doc("LC Settings")
	if not settings.enable_email_alerts:
		return

	days = settings.expiry_alert_days or 7
	expiry_until = add_days(today(), days)

	expiring = frappe.get_all(
		"Letter of Credit",
		filters={
			"docstatus": 1,
			"status": ["not in", ["Closed", "Cancelled"]],
			"expiry_date": ["between", [today(), expiry_until]],
		},
		fields=["name", "expiry_date", "lc_amount", "company"],
	)

	for lc in expiring:
		_notify(lc, "expiry")

	if not settings.enable_maturity_alerts:
		return

	maturing = frappe.get_all(
		"Letter of Credit",
		filters={
			"docstatus": 1,
			"lc_type": "Usance",
			"status": "Liability Outstanding",
			"maturity_date": ["between", [today(), expiry_until]],
		},
		fields=["name", "maturity_date", "outstanding_liability", "company"],
	)

	for lc in maturing:
		_notify(lc, "maturity")


def _notify(lc, alert_type):
	recipients = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "role": "Accounts Manager", "parent": ["!=", "Guest"]},
		pluck="parent",
	)
	if not recipients:
		return

	subject = f"L/C {alert_type.title()} alert: {lc.name}"
	if alert_type == "expiry":
		message = f"Letter of Credit {lc.name} expires on {lc.expiry_date}."
	else:
		message = f"Usance L/C {lc.name} matures on {lc.maturity_date}."

	frappe.sendmail(recipients=recipients, subject=subject, message=message)
