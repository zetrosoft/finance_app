# finance_app/finance_app/doctype/purchase_invoice/purchase_invoice.py

import frappe
from frappe import _, throw
from frappe.utils import flt

# Impor kelas PurchaseInvoice asli dari ERPNext
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice as ERPNextPurchaseInvoice

class PurchaseInvoice(ERPNextPurchaseInvoice):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from erpnext.accounts.doctype.advance_tax.advance_tax import AdvanceTax
        from erpnext.accounts.doctype.payment_schedule.payment_schedule import PaymentSchedule
        from erpnext.accounts.doctype.pricing_rule_detail.pricing_rule_detail import PricingRuleDetail
        from erpnext.accounts.doctype.purchase_invoice_advance.purchase_invoice_advance import PurchaseInvoiceAdvance
        from erpnext.accounts.doctype.purchase_invoice_item.purchase_invoice_item import PurchaseInvoiceItem
        from erpnext.accounts.doctype.purchase_taxes_and_charges.purchase_taxes_and_charges import PurchaseTaxesandCharges
        from erpnext.accounts.doctype.tax_withheld_vouchers.tax_withheld_vouchers import TaxWithheldVouchers
        from erpnext.buying.doctype.purchase_receipt_item_supplied.purchase_receipt_item_supplied import PurchaseReceiptItemSupplied
        from frappe.types import DF

        additional_discount_percentage: DF.Float
        address_display: DF.SmallText | None
        advance_tax: DF.Table[AdvanceTax]
        advances: DF.Table[PurchaseInvoiceAdvance]
        against_expense_account: DF.SmallText | None
        allocate_advances_automatically: DF.Check
        amended_from: DF.Link | None
        apply_discount_on: DF.Literal["", "Grand Total", "Net Total"]
        apply_tds: DF.Check
        auto_repeat: DF.Link | None
        base_discount_amount: DF.Currency
        base_grand_total: DF.Currency
        base_in_words: DF.Data | None
        base_net_total: DF.Currency
        base_paid_amount: DF.Currency
        base_rounded_total: DF.Currency
        base_rounding_adjustment: DF.Currency
        base_tax_withholding_net_total: DF.Currency
        base_taxes_and_charges_added: DF.Currency
        base_taxes_and_charges_deducted: DF.Currency
        base_total: DF.Currency
        base_total_taxes_and_charges: DF.Currency
        base_write_off_amount: DF.Currency
        bill_date: DF.Date | None
        bill_no: DF.Data | None
        billing_address: DF.Link | None
        billing_address_display: DF.SmallText | None
        buying_price_list: DF.Link | None
        cash_bank_account: DF.Link | None
        clearance_date: DF.Date | None
        company: DF.Link | None
        contact_display: DF.SmallText | None
        contact_email: DF.SmallText | None
        contact_mobile: DF.SmallText | None
        contact_person: DF.Link | None
        conversion_rate: DF.Float
        cost_center: DF.Link | None
        credit_to: DF.Link
        currency: DF.Link | None
        disable_rounded_total: DF.Check
        discount_amount: DF.Currency
        dispatch_address: DF.Link | None
        dispatch_address_display: DF.TextEditor | None
        due_date: DF.Date | None
        from_date: DF.Date | None
        grand_total: DF.Currency
        group_same_items: DF.Check
        hold_comment: DF.SmallText | None
        ignore_default_payment_terms_template: DF.Check
        ignore_pricing_rule: DF.Check
        in_words: DF.Data | None
        incoterm: DF.Link | None
        inter_company_invoice_reference: DF.Link | None
        is_internal_supplier: DF.Check
        is_old_subcontracting_flow: DF.Check
        is_opening: DF.Literal["No", "Yes"]
        is_paid: DF.Check
        is_return: DF.Check
        is_subcontracted: DF.Check
        items: DF.Table[PurchaseInvoiceItem]
        language: DF.Data | None
        letter_head: DF.Link | None
        mode_of_payment: DF.Link | None
        named_place: DF.Data | None
        naming_series: DF.Literal["ACC-PINV-.YYYY.-", "ACC-PINV-RET-.YYYY.-"]
        net_total: DF.Currency
        on_hold: DF.Check
        only_include_allocated_payments: DF.Check
        other_charges_calculation: DF.TextEditor | None
        outstanding_amount: DF.Currency
        paid_amount: DF.Currency
        party_account_currency: DF.Link | None
        payment_schedule: DF.Table[PaymentSchedule]
        payment_terms_template: DF.Link | None
        per_received: DF.Percent
        plc_conversion_rate: DF.Float
        posting_date: DF.Date
        posting_time: DF.Time | None
        price_list_currency: DF.Link | None
        pricing_rules: DF.Table[PricingRuleDetail]
        project: DF.Link | None
        rejected_warehouse: DF.Link | None
        release_date: DF.Date | None
        remarks: DF.SmallText | None
        represents_company: DF.Link | None
        return_against: DF.Link | None
        rounded_total: DF.Currency
        rounding_adjustment: DF.Currency
        scan_barcode: DF.Data | None
        select_print_heading: DF.Link | None
        set_from_warehouse: DF.Link | None
        set_posting_time: DF.Check
        set_warehouse: DF.Link | None
        shipping_address: DF.Link | None
        shipping_address_display: DF.SmallText | None
        shipping_rule: DF.Link | None
        status: DF.Literal["", "Draft", "Return", "Debit Note Issued", "Submitted", "Paid", "Partly Paid", "Unpaid", "Overdue", "Cancelled", "Internal Transfer"]
        subscription: DF.Link | None
        supplied_items: DF.Table[PurchaseReceiptItemSupplied]
        supplier: DF.Link
        supplier_address: DF.Link | None
        supplier_group: DF.Link | None
        supplier_name: DF.Data | None
        supplier_warehouse: DF.Link | None
        tax_category: DF.Link | None
        tax_id: DF.ReadOnly | None
        tax_withheld_vouchers: DF.Table[TaxWithheldVouchers]
        tax_withholding_category: DF.Link | None
        tax_withholding_net_total: DF.Currency
        taxes: DF.Table[PurchaseTaxesandCharges]
        taxes_and_charges: DF.Link | None
        taxes_and_charges_added: DF.Currency
        taxes_and_charges_deducted: DF.Currency
        tc_name: DF.Link | None
        terms: DF.TextEditor | None
        title: DF.Data | None
        to_date: DF.Date | None
        total: DF.Currency
        total_advance: DF.Currency
        total_net_weight: DF.Float
        total_qty: DF.Float
        total_taxes_and_charges: DF.Currency
        unrealized_profit_loss_account: DF.Link | None
        update_billed_amount_in_purchase_order: DF.Check
        update_billed_amount_in_purchase_receipt: DF.Check
        update_outstanding_for_self: DF.Check
        update_stock: DF.Check
        use_company_roundoff_cost_center: DF.Check
        use_transaction_date_exchange_rate: DF.Check
        write_off_account: DF.Link | None
        write_off_amount: DF.Currency
        write_off_cost_center: DF.Link | None
    # end: auto-generated types
    
    
    def onload(self):
        super().onload()

    def before_save(self):
        # Logika untuk memperbarui status payment schedule menjadi "Draft" saat PI pertama kali disimpan
        # Hanya jika PI adalah baru, dalam status Draft, dan status_invoice term sebelumnya kosong/null
        if self.is_new() and self.docstatus == 0: # docstatus 0 = Draft
            if self.custom_payment_schedule_term and self.items:
                po_name = self.items[0].purchase_order
                term_id = self.custom_payment_schedule_term

                if po_name and term_id:
                    # Periksa status_invoice saat ini dari term
                    current_term_status = frappe.db.get_value("Payment Schedule", term_id, "status_invoice")

                    if not current_term_status or current_term_status == "Pending":
                        frappe.db.set_value(
                            "Payment Schedule", # Child DocType name
                            term_id,          # Child DocType row name
                            {
                                "status_invoice": "Draft",
                                "invoice_reference": self.name
                            }
                        )

        super().before_save() # Pastikan memanggil super().before_save() jika ada

    def on_update(self):
        # Logika pembaruan status payment schedule sudah dipindahkan ke before_save
        pass

    def before_insert(self):
        if self.is_new():
            po_name = None
            if frappe.form_dict.get('doc'):
                import json
                raw_doc_string = frappe.form_dict.get('doc')
                try:
                    doc_data = json.loads(raw_doc_string)
                    if doc_data.get('items'):
                        for item in doc_data['items']:
                            if item.get('purchase_order'):
                                po_name = item.get('purchase_order')
                                break
                except json.JSONDecodeError as e:
                    pass

            if po_name:
                po_doc = frappe.get_doc("Purchase Order", po_name)
                
                selected_term_from_po = None
                for term in po_doc.payment_schedule:
                    if not term.invoice_reference or frappe.db.get_value("Purchase Invoice", term.invoice_reference, "docstatus") == 2:
                        selected_term_from_po = term
                        break
                
                if selected_term_from_po:
                    self.custom_payment_schedule_term = selected_term_from_po.name
                    self.remarks = (_("Invoice untuk Term Pembayaran: {0} (ID: {1})".format(selected_term_from_po.name, selected_term_from_po.name)) + "\\n" + (self.remarks or ""))

                    for pi_term in self.payment_schedule:
                        if pi_term.payment_term == selected_term_from_po.payment_term and pi_term.idx == selected_term_from_po.idx:
                            pi_term.invoice_basis = selected_term_from_po.invoice_basis
                            pi_term.status_invoice = selected_term_from_po.status_invoice
                            pi_term.invoice_reference = selected_term_from_po.invoice_reference
                            pi_term.related_delivery_id = selected_term_from_po.related_delivery_id
                            break
            
@frappe.whitelist()
def get_billing_invoice_data(po_name, current_pi_name=None, is_from_gr=False):
    billing_details = []
    po_items = []
    selected_term_invoice_portion = 0
    selected_term_payment_amount = 0
    selected_term_description = ""
    has_draft_term = False
    selected_term_name_for_client = None

    if not po_name:
        return {
            "billing_details": [],
            "selected_term_payment_amount": 0,
            "po_items": [],
            "selected_term_invoice_portion": 0,
            "selected_term_description": "",
            "has_draft_term": False,
        }

    try:
        po_doc = frappe.get_doc("Purchase Order", po_name)

        # --- GR Quantity Validation ---
        if not is_from_gr:
            for term in po_doc.payment_schedule:
                if term.invoice_basis == 'GR Quantity':
                    return {
                        "validation_failed": True,
                        "message": _("Pembuatan PI dari PO ini tidak diizinkan karena basis tagihan adalah 'GR Quantity'. Harap buat PI melalui Tanda Terima Pembelian (Purchase Receipt).")
                    }
        # --- End of GR Quantity Validation ---

        po_items = [item.as_dict() for item in po_doc.items]

        selected_term = None
        has_draft_term = False

        if is_from_gr:
            selected_term_invoice_portion = 100
            selected_term_description = _("Tagihan berdasarkan Kuantitas Goods Receipt")
            selected_term_payment_amount = 0  # Biarkan klien yang menghitung dari item GR
            selected_term_name_for_client = None
        else:
            # Logika pencarian termin yang ada hanya berjalan jika bukan dari GR
            linked_pi_names = frappe.get_all(
                "Purchase Invoice Item",
                filters={"purchase_order": po_name},
                pluck="parent",
                distinct=True
            )

            filters_existing_pis = {"name": ("in", linked_pi_names), "docstatus": ("!=", 2)}
            if current_pi_name:
                filters_existing_pis["name"] = ("!=", current_pi_name)

            existing_active_pis_count = frappe.db.count("Purchase Invoice", filters=filters_existing_pis)

            if existing_active_pis_count == 0:
                for term in po_doc.payment_schedule:
                    if not term.invoice_reference or frappe.db.get_value("Purchase Invoice", term.invoice_reference, "docstatus") == 2:
                        selected_term = term
                        break
            else:
                for term in po_doc.payment_schedule:
                    if term.status_invoice == "Draft":
                        if current_pi_name and term.invoice_reference == current_pi_name:
                            selected_term = term
                            break
                        else:
                            has_draft_term = True
                            selected_term = term
                            break
                    elif not term.invoice_reference or frappe.db.get_value("Purchase Invoice", term.invoice_reference, "docstatus") == 2:
                        selected_term = term
                        break

            if selected_term:
                selected_term_name_for_client = selected_term.name
                selected_term_invoice_portion = selected_term.invoice_portion
                selected_term_description = selected_term.description

                if po_doc.net_total is not None and selected_term_invoice_portion is not None:
                    selected_term_payment_amount = flt(po_doc.net_total * (selected_term_invoice_portion / 100))
                else:
                    selected_term_payment_amount = 0

                if selected_term.invoice_reference and selected_term.invoice_reference != current_pi_name and frappe.db.get_value("Purchase Invoice", selected_term.invoice_reference, "docstatus") != 2:
                    selected_term = None
                    selected_term_name_for_client = None
                    selected_term_payment_amount = 0
                    selected_term_invoice_portion = 0
                    selected_term_description = ""
                    has_draft_term = True

        total_billed_amount = frappe.db.get_value(
            "Purchase Invoice Item",
            {"purchase_order": po_name, "docstatus": 1},
            "sum(amount)"
        ) or 0

        outstanding_amount = po_doc.net_total - total_billed_amount

        billing_details.append({
            "no": 1,
            "description": "Outstanding PO",
            "po_amount": po_doc.grand_total,
            "portion": None,
            "total_amount": outstanding_amount
        })
        
        if is_from_gr:
            # For GR-based invoices, the amount is the total of the items.
            # The outstanding amount of the PO is a good representation of the current invoice value.
            billing_details.append({
                "no": 2,
                "description": _("Tagihan berdasarkan Kuantitas Goods Receipt"),
                "po_amount": None,
                "portion": 100,
                "total_amount": outstanding_amount
            })
        elif selected_term:
            billing_details.append({
                "no": 2,
                "description": selected_term_description,
                "po_amount": None,
                "portion": selected_term_invoice_portion,
                "total_amount": selected_term_payment_amount
            })

    except Exception as e:
        frappe.throw(f"Error fetching billing invoice data: {e}")

    return {
        "billing_details": billing_details,
        "selected_term_payment_amount": selected_term_payment_amount,
        "po_items": po_items,
        "selected_term_invoice_portion": selected_term_invoice_portion,
        "selected_term_description": selected_term_description,
        "has_draft_term": has_draft_term,
        "selected_term_idx": selected_term_name_for_client
    }        



@frappe.whitelist()
def update_po_payment_term_status_on_submit(doc, method):
    if doc.custom_payment_schedule_term and doc.items:
        po_name = doc.items[0].purchase_order
        term_id = doc.custom_payment_schedule_term

        if po_name and term_id:
            try:
                po = frappe.get_doc("Purchase Order", po_name)
                
                term_found = False
                for term in po.payment_schedule:
                    if term.name == term_id:
                        frappe.db.set_value(
                            "Payment Schedule",
                            term.name,
                            {
                                "status_invoice": "Invoiced",
                                "invoice_reference": doc.name
                            }
                        )
                        term_found = True
                        break
                
                if not term_found:
                    pass

            except Exception as e:
                pass
    else:
        pass

@frappe.whitelist()
def update_po_payment_term_status_on_cancel(doc, method):
    if doc.custom_payment_schedule_term and doc.items:
        po_name = doc.items[0].purchase_order
        term_id = doc.custom_payment_schedule_term

        if po_name and term_id:
            try:
                po = frappe.get_doc("Purchase Order", po_name)
                
                term_found = False
                for term in po.payment_schedule:
                    if term.name == term_id:
                        frappe.db.set_value(
                            "Payment Schedule",
                            term.name,
                            {
                                "status_invoice": "Pending",
                                "invoice_reference": None
                            }
                        )
                        term_found = True
                        break
                
                if not term_found:
                    pass

            except Exception as e:
                pass
    else:
        pass