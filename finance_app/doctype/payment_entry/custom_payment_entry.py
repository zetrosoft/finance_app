import frappe
from frappe import _
from frappe.utils import flt, cint
#from frappe.utils.data import get_field_precision 
# ATAU jika ini tidak berhasil, coba:
from frappe.model.meta import get_field_precision 
# (Namun, frappe.utils.data adalah lokasi yang lebih umum di versi modern)
# Import the original PaymentEntry class from ERPNext
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as ERPNextPaymentEntry

# Tambahkan fungsi get_payment_entry kustom di luar kelas
@frappe.whitelist()
def get_payment_entry(dt, dn, party_amount=None, bank_account=None, bank_amount=None, party_type=None, payment_type=None, reference_date=None, ignore_permissions=False, created_from_payment_request=False):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry as erpnext_get_payment_entry

    if dt == "Purchase Invoice":
        try:
            pi_doc = frappe.get_doc("Purchase Invoice", dn)
            
            # 1. Before load check Outstanding PI
            if flt(pi_doc.outstanding_amount) <= 0:
                frappe.throw(_("Purchase Invoice {0} is already fully paid.").format(dn))

            # Ambil detail termin yang diperlukan
            po_name = pi_doc.items[0].purchase_order if pi_doc.items else None
            term_row_name = pi_doc.get("custom_payment_schedule_term")
            target_term_name = None
            if po_name and term_row_name:
                target_term_name = frappe.db.get_value("Payment Schedule", term_row_name, "payment_term")

            # Create PE against the Purchase Invoice
            pe = erpnext_get_payment_entry(
                "Purchase Invoice", dn,
                party_amount=pi_doc.grand_total, 
                bank_account=bank_account, bank_amount=bank_amount, party_type=party_type,
                payment_type=payment_type, reference_date=reference_date,
                ignore_permissions=ignore_permissions, created_from_payment_request=created_from_payment_request
            )

            # 2. Filter references dan override amounts untuk memaksa alokasi penuh
            final_references = []
            if pe.get("references"):
                for ref in pe.get("references"):
                    if ref.reference_doctype == "Purchase Invoice" and ref.reference_name == dn:
                        
                        # --- KOREKSI TERMIN DAN ALOKASI ---
                        # Paksa Outstanding Amount pada baris referensi ini menjadi Grand Total PI
                        ref.outstanding_amount = pi_doc.grand_total    
                        ref.allocated_amount = pi_doc.grand_total      # Alokasikan Grand Total
                        ref.payment_term_outstanding = pi_doc.grand_total # Paksa Outstanding Termin
                        ref.total_amount = pi_doc.grand_total          
                        # --- END KOREKSI TERMIN DAN ALOKASI ---
                        
                        # Set the payment_term (jika diperlukan)
                        ref.payment_term = target_term_name
                        
                        # Add other PI details
                        ref.due_date = pi_doc.due_date
                        ref.bill_no = pi_doc.bill_no

                        final_references.append(ref)
                        break
            
            # 3. Set references baru dan update total parent
            if final_references:
                final_references[0].idx = 1 # Reset the index to 1 for clean display
                pe.set("references", final_references)

                # Set parent amounts agar sesuai dengan alokasi (Grand Total PI)
                pe.paid_amount = pi_doc.grand_total 
                if pe.source_exchange_rate:
                    pe.base_paid_amount = pi_doc.grand_total * pe.source_exchange_rate
                else:
                    pe.base_paid_amount = pi_doc.grand_total

                # Recalculate all parent totals based on the clean state.
                pe.set_total_allocated_amount()
                pe.set_unallocated_amount()
                pe.set_difference_amount() 

            return pe

        except frappe.exceptions.ValidationError as e:
            raise
        except Exception as e:
            frappe.log_error(f"Error in custom get_payment_entry for PI: {e}", "Payment Entry Debug")
            return erpnext_get_payment_entry(dt, dn, party_amount, bank_account, bank_amount, party_type, payment_type, reference_date, ignore_permissions, created_from_payment_request=False)
    
    # Fallback for non-PI calls
    return erpnext_get_payment_entry(dt, dn, party_amount, bank_account, bank_amount, party_type, payment_type, reference_date, ignore_permissions, created_from_payment_request=False)


class CustomPaymentEntry(ERPNextPaymentEntry):
    # --- KOREKSI VALIDASI ALOKASI (Nomor 2) ---
    def validate_allocated_amount_with_latest_data(self):
        # Cek apakah Payment Entry ini dibuat untuk Purchase Invoice
        is_pi_allocation = any(
            r.reference_doctype == "Purchase Invoice" 
            for r in self.get("references")
        )

        if is_pi_allocation:
            # Lewati validasi core ERPNext untuk PI, karena logika kustom di atas sudah menangani
            # masalah outstanding_amount yang salah akibat termin pembayaran.
            return
        
        # Jika bukan alokasi PI kustom, jalankan validasi standar.
        super().validate_allocated_amount_with_latest_data()
    # --- END KOREKSI VALIDASI ALOKASI ---



    # Metode yang berfungsi menonaktifkan alokasi berbasis termin untuk PI
    def term_based_allocation_enabled_for_reference(self, reference_doctype: str, reference_name: str) -> bool:
        if reference_doctype == "Purchase Invoice":
            return False
        return super().term_based_allocation_enabled_for_reference(reference_doctype, reference_name)

    def update_payment_schedule(self, cancel=0):
        is_pi_payment = any(ref.reference_doctype == "Purchase Invoice" for ref in self.get("references"))

        if is_pi_payment:
            # Replicate original update_payment_schedule logic, but remove the problematic frappe.throw
            invoice_payment_amount_map = {}
            invoice_paid_amount_map = {}

            for ref in self.get("references"):
                if not ref.payment_term or not ref.reference_name:
                    continue

                key = (ref.payment_term, ref.reference_name, ref.reference_doctype)
                invoice_payment_amount_map.setdefault(key, 0.0)
                invoice_payment_amount_map[key] += ref.allocated_amount

                if not invoice_paid_amount_map.get(key):
                    payment_schedule = frappe.get_all(
                        "Payment Schedule",
                        filters={"parent": ref.reference_name},
                        fields=[
                            "paid_amount",
                            "payment_amount",
                            "payment_term",
                            "discount",
                            "outstanding",
                            "discount_type",
                        ],
                    )
                    for term in payment_schedule:
                        invoice_key = (term.payment_term, ref.reference_name, ref.reference_doctype)
                        invoice_paid_amount_map.setdefault(invoice_key, {})
                        invoice_paid_amount_map[invoice_key]["outstanding"] = term.outstanding
                        if not (term.discount_type and term.discount):
                            continue

                        if term.discount_type == "Percentage":
                            invoice_paid_amount_map[invoice_key]["discounted_amt"] = ref.total_amount * (
                                term.discount / 100
                            )
                        else:
                            invoice_paid_amount_map[invoice_key]["discounted_amt"] = term.discount

            for idx, (key, allocated_amount) in enumerate(invoice_payment_amount_map.items(), 1):
                if not invoice_paid_amount_map.get(key):
                    frappe.throw(_("Payment term {0} not used in {1}").format(key[0], key[1]))

                allocated_amount = self.get_allocated_amount_in_transaction_currency(
                    allocated_amount, key[2], key[1]
                )

                outstanding = flt(invoice_paid_amount_map.get(key, {}).get("outstanding"))
                discounted_amt = flt(invoice_paid_amount_map.get(key, {}).get("discounted_amt"))

                conversion_rate = frappe.db.get_value(key[2], {"name": key[1]}, "conversion_rate")
                base_paid_amount_precision = get_field_precision(
                    frappe.get_meta("Payment Schedule").get_field("base_paid_amount")
                )
                base_outstanding_precision = get_field_precision(
                    frappe.get_meta("Payment Schedule").get_field("base_outstanding")
                )

                base_paid_amount = flt(
                    (allocated_amount - discounted_amt) * conversion_rate, base_paid_amount_precision
                )
                base_outstanding = flt(allocated_amount * conversion_rate, base_outstanding_precision)

                if cancel:
                    frappe.db.sql(
                        """
                        UPDATE `tabPayment Schedule`
                        SET
                            paid_amount = `paid_amount` - %s,
                            base_paid_amount = `base_paid_amount` - %s,
                            discounted_amount = `discounted_amount` - %s,
                            outstanding = `outstanding` + %s,
                            base_outstanding = `base_outstanding` - %s
                        WHERE parent = %s and payment_term = %s""",
                        (
                            allocated_amount - discounted_amt,
                            base_paid_amount,
                            discounted_amt,
                            allocated_amount,
                            base_outstanding,
                            key[1],
                            key[0],
                        ),
                    )
                else:
                    # REMOVED: if allocated_amount > outstanding: frappe.throw(...)

                    if allocated_amount and outstanding:
                        frappe.db.sql(
                            """
                            UPDATE `tabPayment Schedule`
                            SET
                                paid_amount = `paid_amount` + %s,
                                base_paid_amount = `base_paid_amount` + %s,
                                discounted_amount = `discounted_amount` + %s,
                                outstanding = `outstanding` - %s,
                                base_outstanding = `base_outstanding` - %s
                            WHERE parent = %s and payment_term = %s""",
                            (
                                allocated_amount - discounted_amt,
                                base_paid_amount,
                                discounted_amt,
                                allocated_amount,
                                base_outstanding,
                                key[1],
                                key[0],
                            ),
                        )
        else:
            # For non-PI payments, use the original method
            super(CustomPaymentEntry, self).update_payment_schedule(cancel)

    # --- KOREKSI ATTRIBUTEERROR (Nomor 3) ---
    def before_insert(self):
        def get_current_tax_amount(self, tax):
            tax_rate = tax.rate

            if tax.charge_type in ["On Previous Row Amount", "On Previous Row Total"]:
                if tax.idx == 1:
                    frappe.throw(
                        _("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row")
                    )
                if not tax.row_id:
                    tax.row_id = tax.idx - 1

            current_tax_amount = 0.0 

            if tax.charge_type == "Actual":
                current_tax_amount = flt(tax.tax_amount, self.precision("tax_amount", tax))
            elif tax.charge_type == "On Paid Amount":
                current_tax_amount = (tax_rate / 100.0) * self.paid_amount_after_tax
            elif tax.charge_type == "On Net Total": 
                current_tax_amount = (tax_rate / 100.0) * self.paid_amount_after_tax
            elif tax.charge_type == "On Previous Row Amount":
                current_tax_amount = (tax_rate / 100.0) * self.get("taxes")[cint(tax.row_id) - 1].tax_amount
            elif tax.charge_type == "On Previous Row Total":
                current_tax_amount = (tax_rate / 100.0) * self.get("taxes")[cint(tax.row_id) - 1].total
            else:
                current_tax_amount = 0.0 

            return current_tax_amount

    def calculate_taxes(self):
        original_actual_taxes = {}
        for tax in self.get("taxes"):
            if tax.charge_type == "Actual":
                original_actual_taxes[tax.name] = {
                    "tax_amount": tax.tax_amount,
                    "base_tax_amount": tax.base_tax_amount,
                    "total": tax.total,
                    "base_total": tax.base_total,
                    "rate": tax.rate 
                }
        
        super().calculate_taxes()

        restored = False
        for tax in self.get("taxes"):
            if tax.charge_type == "Actual" and tax.name in original_actual_taxes:
                restored = True
                tax.tax_amount = original_actual_taxes[tax.name]["tax_amount"]
                tax.base_tax_amount = original_actual_taxes[tax.name]["base_tax_amount"]
                tax.total = original_actual_taxes[tax.name]["total"]
                tax.base_total = original_actual_taxes[tax.name]["base_total"]
                tax.rate = original_actual_taxes[tax.name]["rate"]
        
        if restored:
            total_taxes_and_charges = sum(
                flt(t.tax_amount) if t.add_deduct_tax == "Add" else -flt(t.tax_amount)
                for t in self.get("taxes")
            )
            self.total_taxes_and_charges = flt(total_taxes_and_charges, self.precision("total_taxes_and_charges"))
            
            conversion_rate = flt(getattr(self, 'conversion_rate', 1.0))
            self.base_total_taxes_and_charges = self.total_taxes_and_charges * conversion_rate
            
            self.grand_total = self.paid_amount + self.total_taxes_and_charges
            self.base_grand_total = self.base_paid_amount + self.base_total_taxes_and_charges
                
            self.set_difference_amount()

    def apply_taxes(self):
        pi_name = None
        for ref in self.get("references"):
            if ref.reference_doctype == "Purchase Invoice":
                pi_name = ref.reference_name
                break

        if pi_name:
            pi_has_taxes = frappe.call(
                "finance_app.doctype.payment_entry.custom_payment_entry.check_purchase_invoice_has_taxes",
                pi_name=pi_name
            )
            
            if pi_has_taxes:
                self.total_taxes_and_charges = 0
                self.base_total_taxes_and_charges = 0
                self.taxes = []
            else:
                super().apply_taxes()
        else:
            super().apply_taxes()

        
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