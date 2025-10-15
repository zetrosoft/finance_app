import frappe

def execute():
    doctype_name = "Payment Schedule"
    fields_to_update = {
        "payment_term": {"in_list_view": 1, "columns": 2},
        "description": {"in_list_view": 1, "columns": 2},
        "invoice_portion": {"in_list_view": 1, "columns": 1},
        "invoice_basis": {"in_list_view": 1, "columns": 2}, # in_list_view already 1 from custom field
        "due_date": {"in_list_view": 1, "columns": 1},
        "status_invoice": {"in_list_view": 1, "columns": 2} # in_list_view already 1 from custom field
    }

    # Get the DocType object
    doctype_doc = frappe.get_doc("DocType", doctype_name)

    for field_name, properties in fields_to_update.items():
        # Find the field in the DocType
        for df in doctype_doc.fields:
            if df.fieldname == field_name:
                # Update properties
                for prop, value in properties.items():
                    setattr(df, prop, value)
                frappe.msgprint(f"Updated {field_name} in {doctype_name}: {properties}")
                break
        else:
            frappe.msgprint(f"Field {field_name} not found in {doctype_name}.", indicator="red")

    # Save the DocType to apply changes
    doctype_doc.save()
    frappe.db.commit()
    frappe.msgprint(f"DocType {doctype_name} properties updated successfully.")