import frappe
from frappe import _
from frappe.utils import flt, cint

# Import the original PaymentEntry class from ERPNext
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as ERPNextPaymentEntry

class CustomPaymentEntry(ERPNextPaymentEntry):
    def get_current_tax_amount(self, tax):
        tax_rate = tax.rate

        if tax.charge_type in ["On Previous Row Amount", "On Previous Row Total"]:
            if tax.idx == 1:
                frappe.throw(
                    _("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row")
                )
            if not tax.row_id:
                tax.row_id = tax.idx - 1

        current_tax_amount = 0.0 # Initialize to avoid UnboundLocalError

        if tax.charge_type == "Actual":
            current_tax_amount = flt(tax.tax_amount, self.precision("tax_amount", tax))
        elif tax.charge_type == "On Paid Amount":
            current_tax_amount = (tax_rate / 100.0) * self.paid_amount_after_tax
        elif tax.charge_type == "On Net Total": # Added condition for "On Net Total"
            # Assuming "On Net Total" should be calculated based on paid_amount_after_tax
            current_tax_amount = (tax_rate / 100.0) * self.paid_amount_after_tax
        elif tax.charge_type == "On Previous Row Amount":
            current_tax_amount = (tax_rate / 100.0) * self.get("taxes")[cint(tax.row_id) - 1].tax_amount
        elif tax.charge_type == "On Previous Row Total":
            current_tax_amount = (tax_rate / 100.0) * self.get("taxes")[cint(tax.row_id) - 1].total
        else:
            # Handle unknown charge types or provide a default
            current_tax_amount = 0.0 # Default to 0 for unhandled types

        return current_tax_amount

    def calculate_taxes(self):
        # Store original tax amounts for "Actual" charge types
        original_actual_taxes = {}
        for tax in self.get("taxes"):
            if tax.charge_type == "Actual":
                original_actual_taxes[tax.name] = {
                    "tax_amount": tax.tax_amount,
                    "base_tax_amount": tax.base_tax_amount,
                    "total": tax.total,
                    "base_total": tax.base_total,
                    "rate": tax.rate # Preserve rate too
                }
        
        # Call the original ERPNext calculate_taxes method
        super().calculate_taxes()

        # Restore original tax amounts for "Actual" charge types
        restored = False
        for tax in self.get("taxes"):
            if tax.charge_type == "Actual" and tax.name in original_actual_taxes:
                restored = True
                tax.tax_amount = original_actual_taxes[tax.name]["tax_amount"]
                tax.base_tax_amount = original_actual_taxes[tax.name]["base_tax_amount"]
                tax.total = original_actual_taxes[tax.name]["total"]
                tax.base_total = original_actual_taxes[tax.name]["base_total"]
                tax.rate = original_actual_taxes[tax.name]["rate"]
        
        # If we performed a restoration, manually recalculate the parent totals
        if restored:
            total_taxes_and_charges = sum(
                flt(t.tax_amount) if t.add_deduct_tax == "Add" else -flt(t.tax_amount)
                for t in self.get("taxes")
            )
            self.total_taxes_and_charges = flt(total_taxes_and_charges, self.precision("total_taxes_and_charges"))
            self.base_total_taxes_and_charges = self.total_taxes_and_charges * self.conversion_rate

            self.grand_total = self.paid_amount + self.total_taxes_and_charges
            self.base_grand_total = self.base_paid_amount + self.base_total_taxes_and_charges
            
            # This is a key method to update difference_amount
            self.set_difference_amount()