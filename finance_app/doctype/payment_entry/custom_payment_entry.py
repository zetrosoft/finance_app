import frappe
from frappe import _
from frappe.utils import flt, cint

# Import the original PaymentEntry class from ERPNext
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as ERPNextPaymentEntry

# Tambahkan fungsi get_payment_entry kustom di luar kelas
@frappe.whitelist()
def get_payment_entry(dt, dn, party_amount=None, bank_account=None, bank_amount=None, party_type=None, payment_type=None, reference_date=None, ignore_permissions=False, created_from_payment_request=False):
    frappe.log_error(f"DEBUG: get_payment_entry called for dt={dt}, dn={dn}", "Payment Entry Debug")
    
    # Panggil fungsi get_payment_entry standar dari ERPNext
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry as erpnext_get_payment_entry
    
    pe = erpnext_get_payment_entry(dt, dn, party_amount, bank_account, bank_amount, party_type, payment_type, reference_date, ignore_permissions, created_from_payment_request)

    # Log outstanding_amount dari PI yang direferensikan oleh PE
    if dt == "Purchase Invoice":
        try:
            pi_doc = frappe.get_doc("Purchase Invoice", dn)
        except Exception as e:
            frappe.log_error(f"DEBUG: Could not get PI {dn} for logging outstanding_amount: {e}", "Payment Entry Debug")

        # Terapkan logika penggabungan referensi jika Payment Entry dibuat dari Purchase Invoice
        if dt == "Purchase Invoice":
            # Always clear existing PI references and add a single consolidated one
            
            # Get all existing references that are NOT Purchase Invoices
            non_pi_references = [
                ref for ref in pe.get("references")
                if not (ref.reference_doctype == "Purchase Invoice" and ref.reference_name == dn)
            ]
    
            # Fetch the actual outstanding amount of the PI
            actual_pi_outstanding = frappe.db.get_value("Purchase Invoice", dn, "outstanding_amount")
            if actual_pi_outstanding is None:
                actual_pi_outstanding = 0.0
    
            # Get the first PI reference from the original list to extract other fields
            # This assumes erpnext_get_payment_entry always returns at least one PI reference if dt is Purchase Invoice
            first_pi_ref = None
            for ref in pe.get("references"):
                if ref.reference_doctype == "Purchase Invoice" and ref.reference_name == dn:
                    first_pi_ref = ref
                    break
            
            if first_pi_ref: # Only append if a PI reference was found initially
                # Create the single consolidated PI reference
                consolidated_pi_reference = frappe._dict({
                    "reference_doctype": "Purchase Invoice",
                    "reference_name": dn, # Use dn directly as it's the PI name
                    "outstanding_amount": actual_pi_outstanding,
                    "allocated_amount": actual_pi_outstanding, # Initially allocate the full outstanding amount
                    "bill_no": first_pi_ref.bill_no,
                    "due_date": first_pi_ref.due_date,
                    "total_amount": first_pi_ref.total_amount,
                    "payment_term": None,
                    "payment_term_outstanding": 0
                })
                non_pi_references.append(consolidated_pi_reference)
            
            pe.set("references", non_pi_references)
            # Perbarui total_allocated_amount di Payment Entry
            pe.set_total_allocated_amount()
            pe.set_unallocated_amount()
            pe.set_difference_amount()

    return pe

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
            
            # Ensure conversion_rate is not None before using it
            conversion_rate = flt(getattr(self, 'conversion_rate', 1.0))
            self.base_total_taxes_and_charges = self.total_taxes_and_charges * conversion_rate
            
            self.grand_total = self.paid_amount + self.total_taxes_and_charges
            self.base_grand_total = self.base_paid_amount + self.base_total_taxes_and_charges
            
            # This is a key method to update difference_amount
            self.set_difference_amount()

    def apply_taxes(self):
        pi_name = None
        for ref in self.get("references"):
            if ref.reference_doctype == "Purchase Invoice":
                pi_name = ref.reference_name
                break

        if pi_name:
            # Check if the linked PI has taxes
            pi_has_taxes = frappe.call(
                "finance_app.doctype.payment_entry.custom_payment_entry.check_purchase_invoice_has_taxes",
                pi_name=pi_name
            )
            
            if pi_has_taxes:
                # If PI has taxes, ensure PE taxes are zeroed out for ledger purposes
                self.total_taxes_and_charges = 0
                self.base_total_taxes_and_charges = 0
                self.taxes = [] # Clear the taxes child table
                # No need to call super().apply_taxes() as we're overriding the tax application
            else:
                # If PI has no taxes, allow manual taxes in PE to be applied
                super().apply_taxes()
        else:
            # If no PI is linked, allow manual taxes in PE to be applied
            super().apply_taxes()

    def term_based_allocation_enabled_for_reference(self, reference_doctype: str, reference_name: str) -> bool:
        if reference_doctype == "Purchase Invoice":
            return False # Selalu kembalikan False untuk Purchase Invoice
        return super().term_based_allocation_enabled_for_reference(reference_doctype, reference_name)

    def validate_allocated_amount_with_latest_data(self):
        if not self.references:
            return

        for idx, d in enumerate(self.get("references"), start=1):
            if d.reference_doctype == "Purchase Invoice":
                # For Purchase Invoices, directly fetch the actual outstanding amount
                actual_pi_outstanding = frappe.db.get_value("Purchase Invoice", d.reference_name, "outstanding_amount")
                if actual_pi_outstanding is None:
                    actual_pi_outstanding = 0.0

                # Validate allocated amount against the actual PI outstanding amount
                if flt(d.allocated_amount) > 0 and flt(d.allocated_amount) > flt(actual_pi_outstanding):
                    frappe.throw(
                        _("Row #{0}: Allocated Amount cannot be greater than outstanding amount.").format(d.idx)
                    )
                # Check for negative outstanding invoices as well
                if flt(d.allocated_amount) < 0 and flt(d.allocated_amount) < flt(actual_pi_outstanding):
                    frappe.throw(
                        _("Row #{0}: Allocated Amount cannot be greater than outstanding amount.").format(d.idx)
                    )
            else:
                # For other doctypes, call the original ERPNext validation
                super().validate_allocated_amount_with_latest_data()




@frappe.whitelist()
def check_purchase_invoice_has_taxes(pi_name):
    if not pi_name:
        return False


    try:
        pi_doc = frappe.get_doc("Purchase Invoice", pi_name)
        if pi_doc.taxes and len(pi_doc.taxes) > 0:
            return True
        return False
    except Exception as e:
        return False

        

    @frappe.whitelist()
    def get_pi_outstanding_amount(pi_name):
        if not pi_name:
            return 0.0

        try:
            pi_doc = frappe.get_doc("Purchase Invoice", pi_name)
            return pi_doc.outstanding_amount

        except Exception as e:
            frappe.log_error(f"Error getting outstanding amount for PI {pi_name}: {e}")
            return 0.0