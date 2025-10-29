frappe.ui.form.on('Payment Entry', {
    onload: function(frm) {
        custom_payment_entry_logic(frm);
    },

    refresh: function(frm) {
        custom_payment_entry_logic(frm);
    },

    before_save: function(frm) {
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
        // Hide 'Get Outstanding Invoices' and 'Get Outstanding Orders' buttons
        frm.set_df_property('get_outstanding_invoices', 'hidden', 1);
        frm.set_df_property('get_outstanding_orders', 'hidden', 1);

        // Make 'references' child table read-only and prevent adding/deleting rows
        frm.set_df_property('references', 'read_only', 1);
        frm.set_df_property('references', 'cannot_add_rows', 1);
        frm.set_df_property('references', 'cannot_delete_rows', 1);

        // Make specific fields in the references child table read-only to prevent client-side overrides
        frm.set_df_property('references.total_amount', 'read_only', 1);
        frm.set_df_property('references.outstanding_amount', 'read_only', 1);
        frm.set_df_property('references.allocated_amount', 'read_only', 1);

        // Check if PI has taxes and adjust 'taxes' table accordingly
        frappe.call({
            method: 'finance_app.doctype.payment_entry.custom_payment_entry.check_purchase_invoice_has_taxes',
            args: {
                pi_name: pi_name
            },
            callback: function(r) {
                let pi_has_taxes = r.message;
                if (pi_has_taxes) {
                    // If PI has taxes, make 'taxes' table visible and read-only
                    frm.set_df_property('taxes', 'hidden', 0);
                    frm.set_df_property('taxes', 'read_only', 1);
                    frm.set_df_property('taxes', 'cannot_add_rows', 1);
                    frm.set_df_property('taxes', 'cannot_delete_rows', 1);
                    // Populate taxes from PI if PE is new and taxes are empty
                    if (frm.is_new() && frm.doc.docstatus === 0 && (!frm.doc.taxes || frm.doc.taxes.length === 0)) {
                        frappe.call({
                            method: 'finance_app.payment_utils.populate_taxes_from_purchase_invoice',
                            args: {
                                pe_doc_dict_json: frm.doc,
                                pi_name: pi_name
                            },
                            callback: function(r_populate) {
                                if (r_populate.message) {
                                    frm.set_value('taxes', r_populate.message.taxes);
                                    frm.refresh_field('taxes');
                                }
                            }
                        });
                    }
                } else {
                    // If PI has no taxes, make 'taxes' table visible and editable
                    frm.set_df_property('taxes', 'hidden', 0);
                    frm.set_df_property('taxes', 'read_only', 0);
                    frm.set_df_property('taxes', 'cannot_add_rows', 0);
                    frm.set_df_property('taxes', 'cannot_delete_rows', 0);
                    // If PI has no taxes, PE taxes should be editable and empty by default.
                    // No need to call populate_taxes_from_purchase_invoice here.
                }
            }
        });
    } else {
        // --- Logic for Payment Entry NOT linked to PI (default behavior) --- 
        // Ensure buttons are visible if not linked to PI
        frm.set_df_property('get_outstanding_invoices', 'hidden', 0);
        frm.set_df_property('get_outstanding_orders', 'hidden', 0);
        
        // Ensure tables are editable if not linked to PI
        frm.set_df_property('taxes', 'hidden', 0);
        frm.set_df_property('taxes', 'read_only', 0);
        frm.set_df_property('taxes', 'cannot_add_rows', 0);
        frm.set_df_property('taxes', 'cannot_delete_rows', 0);

        frm.set_df_property('references', 'read_only', 0);
        frm.set_df_property('references', 'cannot_add_rows', 0);
        frm.set_df_property('references', 'cannot_delete_rows', 0);

    }
}