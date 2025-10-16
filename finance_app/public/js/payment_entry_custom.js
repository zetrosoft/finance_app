frappe.ui.form.on('Payment Entry', {
    onload: function(frm) {
        custom_payment_entry_logic(frm);
    },

    refresh: function(frm) {
        custom_payment_entry_logic(frm);
    },

    before_save: function(frm) { // Add this event handler
        if (frm.doc.references && frm.doc.references.length > 0) {
            let pi_linked = false;
            for (let i = 0; i < frm.doc.references.length; i++) {
                if (frm.doc.references[i].reference_doctype === 'Purchase Invoice') {
                    pi_linked = true;
                    break;
                }
            }
            if (pi_linked) {
            }
        }
    }
});

function custom_payment_entry_logic(frm) {
    // Only run if Payment Entry is new (not yet saved) and not submitted
    // Or if it's an existing document but linked to a PI, to maintain UI state
    let pi_name = null;
    if (frm.doc.references && frm.doc.references.length > 0) {
        for (let i = 0; i < frm.doc.references.length; i++) {
            if (frm.doc.references[i].reference_doctype === 'Purchase Invoice') {
                pi_name = frm.doc.references[i].reference_name;
                break;
            }
        }
    }

    if (pi_name) {
        // --- Logic for Payment Entry linked to PI --- 

        // Populate taxes if new and taxes are empty
        if (frm.is_new() && frm.doc.docstatus === 0 && (!frm.doc.taxes || frm.doc.taxes.length === 0)) {
            frappe.call({
                method: 'finance_app.payment_utils.populate_taxes_from_purchase_invoice',
                args: {
                    pe_doc_dict_json: frm.doc,
                    pi_name: pi_name
                },
                callback: function(r) {
                    if (r.message) {
                        // Update the taxes child table specifically using frm.set_value
                        frm.set_value('taxes', r.message.taxes);
                        frm.refresh_field('taxes'); // Refresh only the taxes field
                    } else {
                    }
                }
            });
        }

        // Hide 'Get Outstanding Invoices' and 'Get Outstanding Orders' buttons
        frm.set_df_property('get_outstanding_invoices', 'hidden', 1);
        frm.set_df_property('get_outstanding_orders', 'hidden', 1);

        // Make 'taxes' child table read-only and prevent adding/deleting rows
        frm.set_df_property('taxes', 'read_only', 1);
        frm.set_df_property('taxes', 'cannot_add_rows', 1);
        frm.set_df_property('taxes', 'cannot_delete_rows', 1);

        // Make 'references' child table read-only and prevent adding/deleting rows
        frm.set_df_property('references', 'read_only', 1);
        frm.set_df_property('references', 'cannot_add_rows', 1);
        frm.set_df_property('references', 'cannot_delete_rows', 1);

    } else {
        // --- Logic for Payment Entry NOT linked to PI (default behavior) --- 

        // Ensure buttons are visible if not linked to PI
        frm.set_df_property('get_outstanding_invoices', 'hidden', 0);
        frm.set_df_property('get_outstanding_orders', 'hidden', 0);
        
        // Ensure tables are editable if not linked to PI
        frm.set_df_property('taxes', 'read_only', 0);
        frm.set_df_property('taxes', 'cannot_add_rows', 0);
        frm.set_df_property('taxes', 'cannot_delete_rows', 0);

        frm.set_df_property('references', 'read_only', 0);
        frm.set_df_property('references', 'cannot_add_rows', 0);
        frm.set_df_property('references', 'cannot_delete_rows', 0);

    }
}