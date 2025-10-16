import frappe
import json
from frappe.model.document import Document
from frappe.utils import flt, cint # Import flt and cint for float and int conversion

@frappe.whitelist()
def populate_taxes_from_purchase_invoice(pe_doc_dict_json, pi_name):
    if not pe_doc_dict_json or not pi_name:
        frappe.throw("Payment Entry document dictionary (JSON string) and Purchase Invoice name are required.")

    pe_doc_dict = json.loads(pe_doc_dict_json)

    if "doctype" not in pe_doc_dict:
        pe_doc_dict["doctype"] = "Payment Entry"
    pe_doc = frappe.get_doc(pe_doc_dict)

    pi_doc = frappe.get_doc("Purchase Invoice", pi_name)

    if not pi_doc.taxes:
        return pe_doc.as_dict() # No taxes on PI, return current PE doc

    pe_doc.set("taxes", [])

    for tax_item in pi_doc.taxes:
        # Explicitly get values with fallbacks for all relevant fields
        # charge_type will be set to "Actual" to preserve amount
        account_head = tax_item.account_head or ""
        description = tax_item.description or ""
        add_deduct_tax = tax_item.add_deduct_tax or ""
        
        # Mandatory fields check
        if not account_head or not description or not add_deduct_tax:
            frappe.throw(f"Mandatory tax field missing in Purchase Invoice {pi_name} for tax item: {tax_item.name}. "
                        f"Missing: account_head={account_head}, description={description}, add_deduct_tax={add_deduct_tax}")

        # Determine currency for the tax item
        tax_currency = tax_item.account_currency if tax_item.account_currency else pi_doc.currency or ""
        
        # Determine cost_center for the tax item
        tax_cost_center = tax_item.cost_center if tax_item.cost_center else pe_doc.cost_center or ""

        # Numeric fields should default to 0.0 if None
        rate = flt(tax_item.rate) # Keep original rate for reference, but calculation will use Actual
        tax_amount = flt(tax_item.tax_amount) # Preserve original tax amount
        total = flt(tax_item.total) # Preserve original total
        base_tax_amount = flt(tax_item.base_tax_amount) # Preserve original base tax amount
        base_total = flt(tax_item.base_total) # Preserve original base total
        
        # Other fields
        row_id = tax_item.row_id or ""
        included_in_paid_amount = cint(tax_item.included_in_paid_amount) # Ensure 0 or 1

        category = tax_item.category or ""
        included_in_print_rate = cint(tax_item.included_in_print_rate)
        is_tax_withholding_account = cint(tax_item.is_tax_withholding_account)

        # --- DEBUG LOGGING START ---
        frappe.log_error(f"DEBUG: tax_item.name: {tax_item.name}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: tax_item.account_currency: {tax_item.account_currency}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: pi_doc.currency: {pi_doc.currency}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: Determined tax_currency: {tax_currency}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: tax_item.cost_center: {tax_item.cost_center}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: Determined tax_cost_center: {tax_cost_center}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: rate (from PI): {tax_item.rate}, tax_amount (from PI): {tax_item.tax_amount}, total (from PI): {tax_item.total}", "Populate Taxes Debug") # Added tax_item.rate
        frappe.log_error(f"DEBUG: row_id: {row_id}, included_in_paid_amount: {included_in_paid_amount}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: category: {category}, included_in_print_rate: {included_in_print_rate}, is_tax_withholding_account: {is_tax_withholding_account}", "Populate Taxes Debug")
        frappe.log_error(f"DEBUG: Original charge_type: {tax_item.charge_type}, Final charge_type: Actual", "Populate Taxes Debug")
        # --- DEBUG LOGGING END ---

        pe_doc.append("taxes", {
            "charge_type": "Actual", # Set to Actual to preserve the tax_amount
            "row_id": row_id,
            "account_head": account_head,
            "description": description,
            "included_in_paid_amount": included_in_paid_amount,
            "cost_center": tax_cost_center,
            "rate": rate, # Keep original rate for display/reference
            "currency": tax_currency,
            "tax_amount": tax_amount, # Use original tax amount from PI
            "total": total,
            "base_tax_amount": base_tax_amount, # Use original base tax amount from PI
            "base_total": base_total, # Use original base total from PI
            "add_deduct_tax": add_deduct_tax,
            "allocated_amount": 0,
            "category": category,
            "included_in_print_rate": included_in_print_rate,
            "is_tax_withholding_account": is_tax_withholding_account,
        })
    
    # --- DEBUG LOGGING START ---
    frappe.log_error(f"DEBUG: Final pe_doc.taxes before return: {pe_doc.get('taxes')}", "Populate Taxes Debug")
    # --- DEBUG LOGGING END ---

    return pe_doc.as_dict()
