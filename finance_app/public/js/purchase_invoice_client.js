// Helper function to compare floating point numbers with a tolerance
function areFloatsEqual(a, b, epsilon = 0.001) {
    return Math.abs(a - b) < epsilon;
}

frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        // onload
    },

    refresh: function(frm) {
        // This function now determines whether to show billing-related sections
        // and buttons based on whether the Purchase Invoice is linked to a Purchase Order.

        let po_name_from_items = null;
        // Logic to get PO name remains the same
        if (frm.doc.items && frm.doc.items.length > 0) {
            for (let i = 0; i < frm.doc.items.length; i++) {
                if (frm.doc.items[i].purchase_order) {
                    po_name_from_items = frm.doc.items[i].purchase_order;
                    break;
                }
            }
        }

        if (po_name_from_items) {
            // --- SCENARIO 1: PI IS LINKED TO A PO ---
            frm.set_df_property('sec_warehouse', 'hidden', 1); // Sembunyikan sec_warehouse
            frm.set_df_property('items', 'hidden', 1); // Sembunyikan child table items
            frm.set_df_property('billing_invoice_details', 'hidden', 0); // Tampilkan billing_invoice_details
            frm.set_df_property('billing_details_section', 'hidden', 0); // Tampilkan section untuk billing_invoice_details

            // Logika yang sudah ada untuk PO
            if (frm.doc.docstatus === 0 && !frm.custom_billing_logic_run) {
                setup_get_billing_info_button(frm, po_name_from_items);
                fetch_and_populate_billing_data(frm, po_name_from_items);
            }

        } else {
            // --- SCENARIO 2: STANDALONE PI (NOT LINKED TO A PO) ---
            frm.set_df_property('sec_warehouse', 'hidden', 0); // Tampilkan sec_warehouse
            frm.set_df_property('items', 'hidden', 0); // Tampilkan child table items
            frm.set_df_property('billing_invoice_details', 'hidden', 1); // Sembunyikan billing_invoice_details
            frm.set_df_property('billing_details_section', 'hidden', 1); // Sembunyikan section untuk billing_invoice_details

            // Pastikan field items tidak read-only jika tidak terkait PO
            frm.set_df_property('items', 'read_only', 0);
            frm.set_df_property('total', 'read_only', 0);
        }
    }
});

function setup_get_billing_info_button(frm, po_name_arg) {
    frm.clear_custom_buttons();
    frm.add_custom_button(__('Get Billing Info'), function() {
        fetch_and_populate_billing_data(frm, po_name_arg);
    }, __("Billing Info"));
}

function fetch_and_populate_billing_data(frm, po_name_arg) {
    console.log("DEBUG: Fetching billing data for Float-Safe Update strategy...");
    frappe.call({
        method: 'finance_app.doctype.purchase_invoice.purchase_invoice.get_billing_invoice_data',
        args: {
            po_name: po_name_arg,
            current_pi_name: frm.doc.name // <-- Tambahkan baris ini
        },
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                console.log("DEBUG: Server data received:", data);

                if (data.has_draft_term) {
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
                } else {
                    // If no term is selected by server, hide the field and show a message
                    frm.get_field('custom_payment_schedule_term').df.hidden = 1;
                    frappe.msgprint({
                        title: __('Informasi'),
                        indicator: 'blue',
                        message: __('Tidak ada termin pembayaran yang tersedia untuk Purchase Order ini.')
                    });
                    // Optionally, disable save or other actions if no term is available
                }

                // --- FLOAT-SAFE UPDATE STRATEGY ---
                if (data.selected_term_invoice_portion !== undefined) {
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
                                    console.log(`DEBUG: Updating item ${pi_item.item_code}. Qty changing from ${pi_item.qty} to ${new_qty}`);
                                    frappe.model.set_value(pi_item.doctype, pi_item.name, 'qty', new_qty);
                                }
                            }
                        });
                    }

                    if (changes_made) {
                        frm.refresh_field('items');
                        console.log("DEBUG: 'items' field refreshed because quantities were changed.");
                    } else {
                        console.log("DEBUG: No quantity changes needed, skipping refresh to avoid making form dirty.");
                    }
                }

                // Populate the custom billing details child table
                frm.clear_table('billing_invoice_details');
                data.billing_details.forEach(function(row_data) {
                    frm.add_child('billing_invoice_details', row_data);
                });
                frm.refresh_field('billing_invoice_details');
                frm.set_df_property('billing_invoice_details', 'read_only', 1);
                console.log("DEBUG: Billing details table populated and locked.");

                // --- FLAG LOGIC ---
                // Set the flag to true after the logic has run successfully once.
                frm.custom_billing_logic_run = true;
                console.log("DEBUG: Custom billing logic flag set to true.");

            } else {
                console.error("DEBUG: Invalid or incomplete response from server:", r.message);
                frappe.msgprint({ title: __('Error'), indicator: 'red', message: __('Could not fetch billing data from the server. Response may be missing invoice portion.') });
            }
        }
    })
}
