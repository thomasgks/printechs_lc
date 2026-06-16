import frappe
from frappe import _
from erpnext.setup.utils import get_exchange_rate
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, today

from printechs_lc.printechs_lc.accounting import (
	post_bank_charges,
	post_bank_paid_supplier,
	post_company_settlement,
	post_margin_block,
	post_margin_release,
)
from printechs_lc.printechs_lc.doctype.lc_settings.lc_settings import get_company_defaults
from printechs_lc.utils.utilization import get_lc_limit


class LetterofCredit(Document):
	def validate(self):
		self.set_defaults_from_company()
		self.set_exchange_rate()
		self.set_margin_amount()
		self.set_bank_payment_confirmation_date()
		self.set_charge_base_amounts()
		self.update_utilization()
		self.set_base_amounts()
		self.validate_utilization_limit()
		self.validate_lc_type()
		self.validate_dates()
		self.validate_close()

	def set_defaults_from_company(self):
		if self.lc_margin_account and self.lc_liability_account and self.bank_charges_account and self.bank_account:
			return

		defaults = get_company_defaults(self.company)
		if not defaults:
			return

		self.lc_margin_account = self.lc_margin_account or defaults.lc_margin_account
		self.lc_liability_account = self.lc_liability_account or defaults.lc_liability_account
		self.bank_charges_account = self.bank_charges_account or defaults.bank_charges_account
		self.bank_account = self.bank_account or defaults.default_bank_account

	def set_exchange_rate(self):
		if not (self.company and self.currency):
			return

		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		if self.currency == company_currency:
			self.exchange_rate = 1
			return

		if flt(self.exchange_rate) and flt(self.exchange_rate) != 1:
			return

		exchange_rate = get_exchange_rate(
			self.currency,
			company_currency,
			self.opening_date or today(),
			"for_buying",
		)
		if exchange_rate:
			self.exchange_rate = exchange_rate

	def set_margin_amount(self):
		if not self.margin_amount and self.margin_percent and self.lc_amount:
			self.margin_amount = flt(self.lc_amount) * flt(self.margin_percent) / 100

	def is_zero_margin_lc(self):
		return self.get("allow_zero_margin") and not flt(self.margin_percent) and not flt(self.margin_amount)

	def validate_margin_required(self):
		if self.is_zero_margin_lc():
			return

		if not flt(self.margin_amount):
			frappe.throw(
				_(
					"Margin Amount or Margin % is required before submitting the L/C. "
					"Enable Allow Zero Margin if no bank margin is required."
				)
			)

	def set_bank_payment_confirmation_date(self):
		if self.bank_payment_confirmed and not self.bank_payment_confirmation_date:
			self.bank_payment_confirmation_date = today()

	def set_charge_base_amounts(self):
		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		for row in self.charges or []:
			if not row.get("charge_currency"):
				row.charge_currency = company_currency

			if not flt(row.get("exchange_rate")):
				row.exchange_rate = self.exchange_rate if row.charge_currency == self.currency else 1

			row.base_amount = flt(row.amount) * flt(row.exchange_rate)

	def update_utilization(self):
		utilized = self._get_linked_invoice_total()
		for row in self.shipments or []:
			utilized = max(utilized, flt(row.shipped_amount))

		self.utilized_amount = utilized
		self.available_amount = flt(self.lc_amount) - utilized

	def set_base_amounts(self):
		exchange_rate = flt(self.exchange_rate) or 1
		self.base_lc_amount = flt(self.lc_amount) * exchange_rate
		self.base_utilized_amount = flt(self.utilized_amount) * exchange_rate
		self.base_available_amount = flt(self.available_amount) * exchange_rate

	def validate_utilization_limit(self):
		limit = get_lc_limit(self)
		if flt(self.utilized_amount) > limit:
			frappe.throw(
				_("Utilized amount exceeds allowed L/C limit. L/C Amount: {0}, Limit: {1}, Utilized: {2}").format(
					self.lc_amount, limit, self.utilized_amount
				)
			)

	def _get_linked_invoice_total(self):
		if not frappe.db.has_column("Purchase Invoice", "letter_of_credit"):
			return 0

		result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(grand_total), 0)
			FROM `tabPurchase Invoice`
			WHERE letter_of_credit = %s AND docstatus = 1
			""",
			self.name,
		)
		return flt(result[0][0]) if result else 0

	def validate_lc_type(self):
		if self.lc_type == "Standby" and self.purchase_order:
			return

		if self.lc_type != "Standby" and not self.purchase_order:
			frappe.msgprint(
				_("Purchase Order is recommended for procurement L/C types."),
				indicator="orange",
			)

		if self.lc_type == "Usance":
			if not self.usance_days:
				frappe.throw(_("Usance Days is required for Usance L/C."))
			if self.acceptance_date and not self.maturity_date:
				self.maturity_date = add_days(self.acceptance_date, self.usance_days)

	def validate_dates(self):
		if self.expiry_date and getdate(self.expiry_date) < getdate(today()) and self.status not in (
			"Closed",
			"Cancelled",
			"Expired",
		):
			if self.docstatus == 1:
				frappe.msgprint(_("This L/C is past expiry date."), indicator="red")

	def validate_close(self):
		if self.status != "Closed":
			return

		if flt(self.outstanding_liability) > 0:
			frappe.throw(_("Cannot close L/C while bank liability is outstanding."))
		if self.margin_blocked and not self.margin_released:
			frappe.throw(_("Cannot close L/C until margin is released."))

	def before_submit(self):
		self.validate_margin_required()

	def on_submit(self):
		if self.is_zero_margin_lc() and self.status in ("Draft", "Requested", "Approved"):
			self.db_set("status", "Opened")
			return

		if self.status == "Draft":
			self.db_set("status", "Requested")

	def before_cancel(self):
		if self.status == "Closed":
			frappe.throw(_("Closed L/C cannot be cancelled without reopening."))


@frappe.whitelist()
def make_margin_block(lc_name, amount=None):
	return post_margin_block(lc_name, amount)


@frappe.whitelist()
def make_bank_charges(lc_name, charge_row_idx=None, amount=None):
	return post_bank_charges(lc_name, charge_row_idx, amount)


@frappe.whitelist()
def make_bank_paid_supplier(lc_name, amount=None):
	return post_bank_paid_supplier(lc_name, amount)


@frappe.whitelist()
def make_company_settlement(lc_name, amount=None):
	return post_company_settlement(lc_name, amount)


@frappe.whitelist()
def make_margin_release(lc_name, amount=None):
	return post_margin_release(lc_name, amount)


@frappe.whitelist()
def get_po_details(purchase_order):
	po = frappe.db.get_value(
		"Purchase Order",
		purchase_order,
		["supplier", "currency", "conversion_rate", "grand_total", "company", "incoterm"],
		as_dict=True,
	)
	if not po:
		return {}
	return {
		"supplier": po.supplier,
		"currency": po.currency,
		"exchange_rate": po.conversion_rate or 1,
		"lc_amount": po.grand_total,
		"company": po.company,
		"incoterms": po.incoterm,
	}


@frappe.whitelist()
def update_status(lc_name, status):
	doc = frappe.get_doc("Letter of Credit", lc_name)
	doc.check_permission("write")
	doc.status = status
	doc.save()
	return doc.status
