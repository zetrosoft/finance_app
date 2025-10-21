// Helper function to compare floating point numbers with a tolerance
function areFloatsEqual(a, b, epsilon = 0.001) {
    return Math.abs(a - b) < epsilon;
}

frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        // onload
    },

    refresh: function(frm) {
        console.log("DEBUG: refresh - START");
        let po_name_from_items = null;
        let is_from_gr = false; // Flag to check if PI is created from GR

        // Logic to get PO name and check for GR link
        if (frm.doc.items && frm.doc.items.length > 0) {
            console.log("DEBUGGING GR->PI: First item data is:", frm.doc.items[0]);
            for (let i = 0; i < frm.doc.items.length; i++) {
                if (frm.doc.items[i].purchase_order) {
                    po_name_from_items = frm.doc.items[i].purchase_order;
                    if (frm.doc.items[i].purchase_receipt) {
                        is_from_gr = true;
                    }
                    break; // Assume all items are from the same source
                }
            }
        }

        frm.is_from_gr = is_from_gr;
        console.log("DEBUG: refresh - po_name_from_items:", po_name_from_items);
        console.log("DEBUG: refresh - frm.is_from_gr:", frm.is_from_gr);

        // If the PI is linked to a PO in any way (direct or via GR), run the custom logic.
        if (po_name_from_items) {
            // --- SCENARIO 1: PI IS LINKED TO A PO (DIRECTLY OR VIA GR) ---
            frm.set_df_property('sec_warehouse', 'hidden', 1);
            frm.set_df_property('items', 'hidden', 1);
            frm.set_df_property('billing_invoice_details', 'hidden', 0);
            frm.set_df_property('billing_details_section', 'hidden', 0);

            if (frm.doc.docstatus === 0 && !frm.custom_billing_logic_run) {
                setup_get_billing_info_button(frm, po_name_from_items);
                // Pass the is_from_gr flag to the data fetching function
                fetch_and_populate_billing_data(frm, po_name_from_items, is_from_gr);
            }

        } else {
            // --- SCENARIO 2: STANDALONE PI (NOT LINKED TO A PO) ---
            frm.set_df_property('sec_warehouse', 'hidden', 0);
            frm.set_df_property('items', 'hidden', 0);
            frm.set_df_property('billing_invoice_details', 'hidden', 1);
            frm.set_df_property('billing_details_section', 'hidden', 1);

            frm.set_df_property('items', 'read_only', 0);
            frm.set_df_property('total', 'read_only', 0);
        }
    }
});

function setup_get_billing_info_button(frm, po_name_arg) {
    frm.clear_custom_buttons();
    frm.add_custom_button(__('Get Billing Info'), function() {
        fetch_and_populate_billing_data(frm, po_name_arg, frm.is_from_gr);
    }, __("Billing Info"));
}

function fetch_and_populate_billing_data(frm, po_name_arg, is_from_gr_arg) {
            const args = {
                po_name: po_name_arg,
                is_from_gr: is_from_gr_arg
            };

            // Only add current_pi_name if the document is not new
            if (!frm.is_new()) {
                args.current_pi_name = frm.doc.name;
            }

            console.log("DEBUG: Arguments sent to server:", args);
            frappe.call({
                method: 'finance_app.doctype.purchase_invoice.purchase_invoice.get_billing_invoice_data',
                args: args,
    
        callback: function(r) {
            if (r.message && r.message.validation_failed) {
                frm.disable_save();
                frappe.msgprint({
                    title: __('Aksi Tidak Diizinkan'),
                    indicator: 'red',
                    message: __(r.message.message),
                    primary_action: {
                        label: __('Kembali ke Purchase Order'),
                        action: () => frappe.set_route('Form', 'Purchase Order', po_name_arg)
                    }
                });
                return; // Stop processing
            }

            if (r.message) {
                let data = r.message;
                console.log("DEBUG: Server response data.billing_details:", data.billing_details);

                // Only show warning and redirect if it's a NEW PI being created from a PO that has a draft term
                if (frm.is_new() && data.has_draft_term) {
                    frappe.msgprint({
                        title: __('Peringatan'),
                        indicator: 'orange',
                        message: __('Masih ada termin pembayaran yang berstatus Draft atau belum disubmit untuk Purchase Order ini. Harap selesaikan atau batalkan Purchase Invoice sebelumnya.')
                    });
                    frappe.set_route('List', 'Purchase Order'); // Redirect back to PO list
                    return; // Stop further processing
                }

                // Set custom_payment_schedule_term based on server's selection
                if (data.selected_term_idx) {
                    frm.set_value('custom_payment_schedule_term', data.selected_term_idx);
                    frm.get_field('custom_payment_schedule_term').df.hidden = 1; // Hide after setting
                } else { // data.selected_term_idx is null/undefined
                    // If no term is selected, only show a message if it's a NEW PI AND not a GR-based invoice.
                    // For existing PIs or GR-based PIs, this message should not stop processing.
                    if (frm.is_new() && !frm.is_from_gr) {
                        frm.get_field('custom_payment_schedule_term').df.hidden = 1;
                        frappe.msgprint({
                            title: __('Informasi'),
                            indicator: 'blue',
                            message: __('Tidak ada termin pembayaran yang tersedia untuk Purchase Order ini.')
                                                
                            });
                            return
                    }
                    // Optionally, disable save or other actions if no term is available
                }
                // --- FLOAT-SAFE UPDATE STRATEGY ---
                // Only run quantity recalculation if NOT creating from a GR
                if (!frm.is_from_gr && data.selected_term_invoice_portion !== undefined) {
                    const portion = data.selected_term_invoice_portion / 100;
                    let changes_made = false;

                    if (portion > 0 && data.po_items && data.po_items.length > 0) {
                        frm.doc.items.forEach(pi_item => {
                            const original_po_item = data.po_items.find(po_item => po_item.name === pi_item.po_detail);
                            if (original_po_item) {
                                const new_qty = original_po_item.qty * portion;
                                
                                // *** THE FIX: Compare with tolerance to avoid float precision issues ***
                                if (!areFloatsEqual(pi_item.qty, new_qty)) {
                                    changes_made = true;
                                    frappe.model.set_value(pi_item.doctype, pi_item.name, 'qty', new_qty);
                                }
                            }
                        });
                    }

                    if (changes_made) {
                        frm.refresh_field('items');
                    }
                }
                console.log("DEBUB:frm",frm.data)
                // Correct the total_amount for GR-based invoice before rendering
                if (frm.is_from_gr) {
                    data.billing_details.forEach(function(row) {
                    // The GR-based row has a 100% portion
                        if (row.portion === 100) {
                            row.total_amount = frm.doc.grand_total;
                        }
                    });
                }
                
                // Populate the custom billing details child table
                frm.clear_table('billing_invoice_details');
                                    data.billing_details.forEach(function(row_data) {
                                        frm.add_child('billing_invoice_details', row_data);
                                    });
                                    console.log("DEBUG: frm.doc.billing_invoice_details length after add_child:", frm.doc.billing_invoice_details.length);
                                    frm.refresh_field('billing_invoice_details');
                                    frm.set_df_property('billing_invoice_details', 'read_only', 1);

                // --- FLAG LOGIC ---
                // Set the flag to true after the logic has run successfully once.
                frm.custom_billing_logic_run = true;

            } else {
                frappe.msgprint({ title: __('Error'), indicator: 'red', message: __('Could not fetch billing data from the server. Response may be missing invoice portion.') });
            }
        }
    })
}
