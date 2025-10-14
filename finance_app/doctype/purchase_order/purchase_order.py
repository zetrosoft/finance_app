import frappe
from frappe import _
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder

class CustomPurchaseOrder(PurchaseOrder):
    def make_purchase_invoice(self):
        # Validation: Check for existing draft PIs for any payment term
        for term in self.payment_schedule:
            if term.invoice_reference:
                try:
                    pi_status = frappe.db.get_value("Purchase Invoice", term.invoice_reference, "docstatus")
                    # If a PI is linked and it's still a draft, block creation of a new one.
                    if pi_status == 0:
                        frappe.throw(
                            _("Terdapat Purchase Invoice (<b>{0}</b>) yang masih berstatus Draft untuk termin pembayaran ini. Lakukan Submit atau Cancel PI tersebut terlebih dahulu.").format(term.invoice_reference),
                            title=_("Draft Purchase Invoice Exists")
                        )
                except frappe.DoesNotExistError:
                    # If the linked PI doesn't exist for some reason, ignore and proceed.
                    pass
        
        # If validation passes, call the original method to create the PI
        return super(CustomPurchaseOrder, self).make_purchase_invoice()
