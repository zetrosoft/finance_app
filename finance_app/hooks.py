app_name = "finance_app"
app_title = "Finance App"
app_publisher = "Bijak Technology"
app_description = "Custom Logic For Finance and Payment"
app_email = "support@bijaktechnology.com"
app_license = "mit"

override_doctype_class = {
    "Purchase Invoice": "finance_app.doctype.purchase_invoice.purchase_invoice.PurchaseInvoice",
    "Purchase Order": "finance_app.doctype.purchase_order.purchase_order.CustomPurchaseOrder",
    "Payment Entry": "finance_app.doctype.payment_entry.custom_payment_entry.CustomPaymentEntry"
}

fixtures = ["Custom Field"]

doc_events = {
    "Purchase Invoice": {

        "on_submit": "finance_app.doctype.purchase_invoice.purchase_invoice.update_po_payment_term_status_on_submit",
        "on_cancel": "finance_app.doctype.purchase_invoice.purchase_invoice.update_po_payment_term_status_on_cancel"
    }
}

# patches
# A list of functions that are executed when a site is migrated.
patches = ["finance_app.patches.update_payment_schedule_columns.execute"]

# app_include_js = "/assets/finance_app/js/finance_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "finance_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Purchase Invoice": "public/js/purchase_invoice_client.js",
    "Payment Entry": "public/js/payment_entry_custom.js"
}
# app_include_js = [
#     "/assets/finance_app/js/purchase_invoice_client.js",
#     "/assets/finance_app/js/payment_entry_custom.js"
# ]