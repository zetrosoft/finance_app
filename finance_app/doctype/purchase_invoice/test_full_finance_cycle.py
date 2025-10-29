import frappe
import unittest
from frappe.utils import flt, nowdate
from frappe.tests.utils import FrappeTestCase
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice as make_pi_from_pr

def create_test_supplier(supplier_name="Test Supplier Finance Cycle"):
    if not frappe.db.exists("Supplier", supplier_name):
        frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": supplier_name,
            "supplier_group": "All Supplier Groups"
        }).insert()
    return supplier_name

def create_test_item(item_code="Test Item Finance Cycle"):
    if not frappe.db.exists("Item", item_code):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_code,
            "item_group": "All Item Groups",
            "is_stock_item": 1,
        }).insert()
    return item_code

def create_percentage_payment_terms(template_name="Test Percentage Terms 40-35-25"):
    if not frappe.db.exists("Payment Terms Template", template_name):
        frappe.get_doc({
            "doctype": "Payment Terms Template",
            "template_name": template_name,
            "terms": [
                {"doctype": "Payment Terms Template Detail", "invoice_portion": 40.0, "credit_days": 0, "description": "Down Payment"},
                {"doctype": "Payment Terms Template Detail", "invoice_portion": 35.0, "credit_days": 30, "description": "On Progress"},
                {"doctype": "Payment Terms Template Detail", "invoice_portion": 25.0, "credit_days": 45, "description": "Final Payment"},
            ]
        }).insert()
    return template_name

class TestFullFinanceCycle(FrappeTestCase):
    def setUp(self):
        # Clean up previous test data to ensure a clean slate
        for doctype in ["Purchase Order", "Purchase Invoice", "Purchase Receipt", "Payment Entry"]:
            frappe.db.delete(doctype, {"supplier": "_Test Supplier Finance Cycle"})

        self.supplier = create_test_supplier("_Test Supplier Finance Cycle")
        self.item = create_test_item("_Test Item Finance Cycle")
        self.ptt = create_percentage_payment_terms()
        self.company = frappe.defaults.get_user_default("company")
        self.credit_account = frappe.db.get_value("Company", self.company, "default_payable_account")
        self.cash_account = frappe.db.get_value("Company", self.company, "default_cash_account")


    def test_percentage_po_full_cycle(self):
        # 1. Create Purchase Order
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "company": self.company,
            "supplier": self.supplier,
            "currency": "IDR",
            "posting_date": nowdate(),
            "payment_terms_template": self.ptt,
            "items": [{
                "item_code": self.item,
                "qty": 10,
                "rate": 100000, # Net Rate
            }]
        })
        po.insert()
        po.submit()
        self.assertEqual(po.docstatus, 1)
        self.assertEqual(po.net_total, 1000000)
        self.assertEqual(len(po.payment_schedule), 3)

        # 2. Create PI for Term 1 (40%)
        pi1 = frappe.get_doc(po.make_purchase_invoice())
        pi1.posting_date = nowdate()
        pi1.credit_to = self.credit_account
        pi1.insert()
        pi1.submit()
        self.assertEqual(pi1.docstatus, 1)
        self.assertAlmostEqual(pi1.net_total, 400000, places=0)
        self.assertEqual(frappe.db.get_value("Payment Schedule", po.payment_schedule[0].name, "invoice_reference"), pi1.name)

        # 3. Create PI for Term 2 (35%)
        pi2 = frappe.get_doc(po.make_purchase_invoice())
        pi2.posting_date = nowdate()
        pi2.credit_to = self.credit_account
        pi2.insert()
        pi2.submit()
        self.assertEqual(pi2.docstatus, 1)
        self.assertAlmostEqual(pi2.net_total, 350000, places=0)
        self.assertEqual(frappe.db.get_value("Payment Schedule", po.payment_schedule[1].name, "invoice_reference"), pi2.name)

        # 4. Create Purchase Receipt (80% Qty)
        pr = frappe.get_doc(po.make_purchase_receipt())
        pr.items[0].qty = 8 # 80% of 10
        pr.insert()
        pr.submit()
        self.assertEqual(pr.docstatus, 1)
        self.assertEqual(pr.items[0].qty, 8)

        # 5. Create Final PI (recalculated)
        # The logic should pick up the last term and recalculate
        pi3 = frappe.get_doc(po.make_purchase_invoice())
        pi3.posting_date = nowdate()
        pi3.credit_to = self.credit_account
        pi3.insert()
        pi3.submit()
        
        # Verification:
        # Total GR Amount (net) = 8 qty * 100,000 rate = 800,000
        # Total Previous PI Amount (net) = 400,000 + 350,000 = 750,000
        # Expected PI3 Amount = 800,000 - 750,000 = 50,000
        self.assertEqual(pi3.docstatus, 1)
        self.assertAlmostEqual(pi3.net_total, 50000, places=0)
        self.assertEqual(frappe.db.get_value("Payment Schedule", po.payment_schedule[2].name, "invoice_reference"), pi3.name)

        # 6. Create Payment Entries for all PIs
        # Payment for PI 1
        pe1 = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "company": self.company,
            "posting_date": nowdate(),
            "paid_from": self.cash_account,
            "party_type": "Supplier",
            "party": self.supplier,
            "paid_amount": pi1.grand_total,
            "references": [{"reference_doctype": "Purchase Invoice", "reference_name": pi1.name}]
        })
        pe1.insert()
        pe1.submit()
        self.assertEqual(pe1.docstatus, 1)
        self.assertEqual(frappe.db.get_value("Purchase Invoice", pi1.name, "status"), "Paid")

        # Payment for PI 2
        pe2 = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "company": self.company,
            "posting_date": nowdate(),
            "paid_from": self.cash_account,
            "party_type": "Supplier",
            "party": self.supplier,
            "paid_amount": pi2.grand_total,
            "references": [{"reference_doctype": "Purchase Invoice", "reference_name": pi2.name}]
        })
        pe2.insert()
        pe2.submit()
        self.assertEqual(pe2.docstatus, 1)
        self.assertEqual(frappe.db.get_value("Purchase Invoice", pi2.name, "status"), "Paid")

        # Payment for PI 3
        pe3 = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "company": self.company,
            "posting_date": nowdate(),
            "paid_from": self.cash_account,
            "party_type": "Supplier",
            "party": self.supplier,
            "paid_amount": pi3.grand_total,
            "references": [{"reference_doctype": "Purchase Invoice", "reference_name": pi3.name}]
        })
        pe3.insert()
        pe3.submit()
        self.assertEqual(pe3.docstatus, 1)
        self.assertEqual(frappe.db.get_value("Purchase Invoice", pi3.name, "status"), "Paid")