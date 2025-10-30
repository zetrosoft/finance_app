// =================== NEW FUNCTION TO ADD THE BUTTON ===================
function add_info_sumber_button(frm, po_name) {
    // Find the section header
    let section_header = $('[data-fieldname="billing_details_section"] .section-head');
    
    // Explicitly remove any existing button to ensure fresh closure
    section_header.find('.btn-info-sumber').remove();

    // Create and append the button
    let info_button = $(`
        <button class="btn btn-primary btn-sm btn-info-sumber" style="float: right; margin-left: 5px;">
            <i class="fa fa-info-circle"></i> Info Sumber
        </button>
    `).appendTo(section_header);

    // Add click event handler
    info_button.on('click', function() {
        frappe.call({
            method: 'finance_app.doctype.purchase_invoice.purchase_invoice.get_po_summary_data',
            args: { po_name: po_name },
            freeze: true,
            freeze_message: __('Mengambil data sumber terbaru...'),
            callback: function(r) {
                if (r.message) {
                    let data = r.message;
                    
                    // Format data into HTML
                    let html = format_summary_for_dialog(data);

                    // Show dialog
                    let dialog = new frappe.ui.Dialog({
                        title: __('Ringkasan Sumber: ' + data.po_details.name),
                        size: 'large',
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'summary_html'
                            }
                        ],
                        primary_action_label: __('Tutup'),
                        primary_action: function() {
                            dialog.hide();
                        }
                    });                    dialog.get_field('summary_html').$wrapper.html(html);
                    dialog.show();
                    dialog.$wrapper.find('.modal-header').css({
                        'background-color': '#F09A37',
                        'border-top-left-radius': '6px',
                        'border-top-right-radius': '6px'
                    });
                    dialog.$wrapper.find('.modal-content').css('border', '2px solid #F09A37');
                } else {
                    frappe.msgprint(__('Gagal mengambil data ringkasan PO.'));
                }
            }
        });
    });
}

// =================== NEW FUNCTION TO FORMAT HTML FOR DIALOG ===================
function format_summary_for_dialog(data) {
    let po_details = data.po_details;
    let pi_list = data.pi_list;
    let pr_list = data.pr_list;
    let mr_list = data.mr_list;
    let po_items = data.po_items || [];
    let pe_list = data.pe_list; // NEW
    let total_pe_amount = data.total_pe_amount; // NEW
    let outstanding_details = data.outstanding_details;
    let total_pr_amount = data.total_pr_amount;
    let total_pi_amount = data.total_pi_amount;
    let total_pr_qty = data.total_pr_qty;
    let currency = po_details.currency;
    let user_permissions = data.user_permissions || {};

    const createLink = (doctype, name, has_permission) => {
        if (has_permission && name) {
            return `<a href="/app/${frappe.router.slug(doctype)}/${name}" target="_blank">${name}</a>`;
        }
        return name || '';
    };

    // Calculate Tax
    let tax_amount = po_details.grand_total - po_details.net_total;

    // PO Details HTML
    let po_html = `
        <h4>Detail Purchase Order</h4>
        <table class="table table-bordered table-sm" style="margin-bottom: 0;">
            <tbody>
                <tr>
                    <td style="width: 15%;">No. PO</td>
                    <td style="width: 35%;">${createLink('Purchase Order', po_details.name, user_permissions.PurchaseOrder)}</td>
                    <td style="width: 15%;">Tanggal PO</td>
                    <td style="width: 35%;">${po_details.transaction_date ? frappe.datetime.str_to_user(po_details.transaction_date) : ''}</td>
                </tr>
                <tr>
                    <td>Total Kuantitas</td>
                    <td colspan="3">${po_details.total_qty_str || ''}</td>
                </tr>
                <tr>
                    <td>Total Net</td>
                    <td>${frappe.format(po_details.net_total, {fieldtype: 'Currency', currency: currency})}</td>
                    <td>Total Pajak</td>
                    <td>${frappe.format(tax_amount, {fieldtype: 'Currency', currency: currency})}</td>
                </tr>
                 <tr>
                    <td>Total Bruto</td>
                    <td colspan="3" style="font-weight: bold;">${frappe.format(po_details.grand_total, {fieldtype: 'Currency', currency: currency})}</td>
                </tr>
            </tbody>
        </table>
    `;

    // PO Items HTML (Collapsible) - Moved
    let items_html = '';
    if (po_items.length > 0) {
        items_html = `
            <p class="mb-2 mt-2">
                <a class="btn btn-secondary btn-xs" data-toggle="collapse" data-target="#poItemsCollapse" role="button" aria-expanded="false" aria-controls="poItemsCollapse">
                    View Items
                </a>
            </p>
            <div class="collapse" id="poItemsCollapse">
                <table class="table table-bordered table-sm">
                    <thead>
                        <tr>
                            <th>Kode Item</th>
                            <th>Nama Item</th>
                            <th>Tgl. Kirim</th>
                            <th style="text-align: right;">Qty</th>
                            <th>UOM</th>
                            <th style="text-align: right;">Rate</th>
                            <th style="text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${po_items.map(item => `
                            <tr>
                                <td>${item.item_code}</td>
                                <td>${item.item_name}</td>
                                <td>${item.delivery_date ? frappe.datetime.str_to_user(item.delivery_date) : ''}</td>
                                <td style="text-align: right;">${item.qty}</td>
                                <td>${item.uom}</td>
                                <td style="text-align: right;">${frappe.format(item.rate, {fieldtype: 'Currency', currency: currency})}</td>
                                <td style="text-align: right;">${frappe.format(item.amount, {fieldtype: 'Currency', currency: currency})}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // Payment Schedule HTML
    let payment_schedule_html = '';
    if (po_details.payment_schedule && po_details.payment_schedule.length > 0) {
        payment_schedule_html += '<h5 class="mt-3">Jadwal Pembayaran</h5>';
        payment_schedule_html += `
            <table class="table table-bordered table-sm">
                <thead><tr><th>Termin</th><th>Basis Invoice</th><th>Jatuh Tempo</th><th style="text-align: right;">Porsi</th><th style="text-align: right;">Nilai</th></tr></thead>
                <tbody>
                    ${po_details.payment_schedule.map(term => `
                        <tr>
                            <td class="term-cell" data-description="${escapeHtml(term.description || '')}">${term.payment_term}</td>
                            <td>${term.invoice_basis || ''}</td>
                            <td>${frappe.datetime.str_to_user(term.due_date) || ''}</td>
                            <td style="text-align: right;">${term.invoice_portion}%</td>
                            <td style="text-align: right;">${frappe.format(term.amount, {fieldtype: 'Currency', currency: currency})}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    // Material Request List HTML
    let mr_html = '<h4 class="mt-3">Riwayat Material Request</h4>';
    if (mr_list && mr_list.length > 0) {
        mr_html += `
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>No. Material Request</th>
                        <th>Tanggal</th>
                        <th style="text-align: right;">Total Kuantitas</th>
                    </tr>
                </thead>
                <tbody>
                    ${mr_list.map(mr => `
                        <tr>
                            <td>${createLink('Material Request', mr.name, user_permissions.MaterialRequest)}</td>
                            <td>${frappe.datetime.str_to_user(mr.transaction_date)}</td>
                            <td style="text-align: right;">${mr.total_quantity_str || ''}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else {
        mr_html += '<p>Purchase Order ini tidak dibuat dari Material Request.</p>';
    }

    // PI List HTML
    let pi_html = '<h4>Riwayat Purchase Invoice</h4>';
    if (pi_list && pi_list.length > 0) {
        pi_html += `
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>No. Invoice</th>
                        <th>Status</th>
                        <th style="text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${pi_list.map(pi => `
                        <tr>
                            <td>${createLink('Purchase Invoice', pi.name, user_permissions.PurchaseInvoice)}</td>
                            <td>${pi.status}</td>
                            <td style="text-align: right;">${frappe.format(pi.grand_total, {fieldtype: 'Currency', currency: currency})}</td>
                        </tr>
                    `).join('')}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="text-align: right;"><b>Total Nilai Invoice</b></td>
                        <td style="text-align: right;"><b>${frappe.format(total_pi_amount, {fieldtype: 'Currency', currency: currency})}</b></td>
                    </tr>
                </tfoot>
            </table>
        `;
    } else {
        pi_html += '<p>Belum ada Purchase Invoice yang dibuat untuk PO ini.</p>';
    }

    // PR List HTML
    let pr_html = '<h4>Riwayat Purchase Receipt</h4>';
    if (pr_list && pr_list.length > 0) {
        pr_html += `
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>No. Receipt</th>
                        <th>Tanggal</th>
                        <th style="text-align: right;">Kuantitas</th>
                        <th style="text-align: right;">Nilai</th>
                    </tr>
                </thead>
                <tbody>
                    ${pr_list.map(pr => `
                        <tr>
                            <td>${createLink('Purchase Receipt', pr.name, user_permissions.PurchaseReceipt)}</td>
                            <td>${frappe.datetime.str_to_user(pr.posting_date)}</td>
                            <td style="text-align: right;">${pr.total_qty}</td>
                            <td style="text-align: right;">${frappe.format(pr.amount, {fieldtype: 'Currency', currency: currency})}</td>
                        </tr>
                    `).join('')}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="text-align: right;"><b>Total</b></td>
                        <td style="text-align: right;"><b>${total_pr_qty}</b></td>
                        <td style="text-align: right;"><b>${frappe.format(total_pr_amount, {fieldtype: 'Currency', currency: currency})}</b></td>
                    </tr>
                </tfoot>
            </table>
        `;
    } else {
        pr_html += '<p>Belum ada Purchase Receipt yang dibuat untuk PO ini.</p>';
    }

    // Payment Entry List HTML
    let pe_html = '<h4>Riwayat Payment Entry</h4>';
    if (pe_list && pe_list.length > 0) {
        pe_html += `
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>No. Payment</th>
                        <th>Tanggal</th>
                        <th>Mode Pembayaran</th>
                        <th style="text-align: right;">Jumlah Dibayar</th>
                    </tr>
                </thead>
                <tbody>
                    ${pe_list.map(pe => `
                        <tr>
                            <td>${createLink('Payment Entry', pe.name, user_permissions.PaymentEntry)}</td>
                            <td>${frappe.datetime.str_to_user(pe.posting_date)}</td>
                            <td>${pe.mode_of_payment || ''}</td>
                            <td style="text-align: right;">${frappe.format(pe.paid_amount, {fieldtype: 'Currency', currency: currency})}</td>
                        </tr>
                    `).join('')}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="3" style="text-align: right;"><b>Total Pembayaran</b></td>
                        <td style="text-align: right;"><b>${frappe.format(total_pe_amount, {fieldtype: 'Currency', currency: currency})}</b></td>
                    </tr>
                </tfoot>
            </table>
        `;
    } else {
        pe_html += '<p>Belum ada pembayaran yang tercatat untuk PO ini.</p>';
    }

    // Outstanding HTML
    let outstanding_html = `
        <h4 class="mt-3">Informasi Outstanding</h4>
        <table class="table table-bordered table-sm">
            <tbody>
                <tr><td style="width: 30%;">Outstanding Kuantitas</td><td style="text-align: right;">${outstanding_details.outstanding_qty}</td></tr>
                <tr><td>Outstanding Nilai</td><td style="text-align: right;">${frappe.format(outstanding_details.outstanding_amount, {fieldtype: 'Currency', currency: currency})}</td></tr>
            </tbody>
        </table>
    `;

    return po_html + items_html + payment_schedule_html + mr_html + pr_html + pi_html + pe_html + outstanding_html;
}

// Helper function to escape HTML for tooltips
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Add event listener for tooltips after dialog is shown
$(document).on('dialog-show', function(e, dialog) {
    if (dialog.title.includes('Ringkasan Sumber')) {
        dialog.$wrapper.find('.term-cell').tooltip({
            title: function() { return $(this).data('description'); },
            placement: 'top',
            container: 'body'
        });
    }
});

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
        
        if (po_name_from_items) {
            // This is a PO-linked invoice
            frm.set_df_property('sec_warehouse', 'hidden', 1);
            frm.set_df_property('items', 'hidden', 1);
            frm.set_df_property('billing_invoice_details', 'hidden', 0);
            frm.set_df_property('billing_details_section', 'hidden', 0);
            // Hide the standard payment schedule table as requested
            frm.set_df_property('payment_schedule', 'hidden', 1);

            // === MODIFICATION: Call the function to add the button ===
            add_info_sumber_button(frm, po_name_from_items);

            if (frm.doc.docstatus === 0 && !frm.custom_billing_logic_run) {
                setup_get_billing_info_button(frm, po_name_from_items);
                fetch_and_populate_billing_data(frm, po_name_from_items, is_from_gr);
            }

        } else {
            // This is a Standalone PI
            frm.set_df_property('sec_warehouse', 'hidden', 0);
            frm.set_df_property('items', 'hidden', 0);
            frm.set_df_property('billing_invoice_details', 'hidden', 1);
            frm.set_df_property('billing_details_section', 'hidden', 1);
            frm.set_df_property('payment_schedule', 'hidden', 0);

            frm.set_df_property('items', 'read_only', 0);
            frm.set_df_property('total', 'read_only', 0);
        }
    }
});

// New onchange trigger for the child table to implement "proxy" logic
frappe.ui.form.on('Billing Invoice Detail', {
    total_amount: function(frm, cdt, cdn) {
        let child_row = locals[cdt][cdn];
        // Pastikan frm.po_total ada dan tidak nol
        if (frm.po_total && frm.po_total > 0 && child_row.idx > 1) { 
            let new_portion = (child_row.total_amount / frm.po_total) * 100;
            
            if (frm.po_items && frm.po_items.length > 0) {
                frm.doc.items.forEach(pi_item => {
                    const original_po_item = frm.po_items.find(po_item => po_item.name === pi_item.po_detail);
                    if (original_po_item) {
                        const new_qty = original_po_item.qty * (new_portion / 100);
                        if (!areFloatsEqual(pi_item.qty, new_qty)) {
                            frappe.model.set_value(pi_item.doctype, pi_item.name, 'qty', new_qty);
                        }
                    }
                });
                frm.refresh_field('items');
            }
        }
    }
});

function setup_get_billing_info_button(frm, po_name_arg) {
    if (frappe.user.has_role('Administrator')) {
        frm.clear_custom_buttons();
        frm.add_custom_button(__('Get Billing Info'), function() {
            fetch_and_populate_billing_data(frm, po_name_arg, frm.is_from_gr);
        }, __("Billing Info"));
    }
}

function fetch_and_populate_billing_data(frm, po_name_arg, is_from_gr_arg) {
    const args = {
        po_name: po_name_arg,
        is_from_gr: is_from_gr_arg
    };

    if (!frm.is_new()) {
        args.current_pi_name = frm.doc.name;
    }

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
                return;
            }

            if (r.message) {
                let data = r.message;
                // Store PO items and total on the form object for later use (e.g., in onchange)
                frm.po_items = data.po_items;
                frm.po_total = data.po_total;

                if (frm.is_new() && data.has_draft_term) {
                    frappe.msgprint({
                        title: __('Peringatan'),
                        indicator: 'orange',
                        message: __('Masih ada termin pembayaran yang berstatus Draft atau belum disubmit untuk Purchase Order ini. Harap selesaikan atau batalkan Purchase Invoice sebelumnya.')
                    });
                    frappe.set_route('List', 'Purchase Order');
                    return;
                }

                if (!data.selected_term_idx && frm.is_new() && !frm.is_from_gr) {
                    frappe.msgprint({
                        title: __('Informasi'),
                        indicator: 'blue',
                        message: __('Tidak ada termin pembayaran yang tersedia untuk Purchase Order ini.')
                    });
                    return;
                }

                // --- CORRECT LOGIC BLOCK ---
                // 1. Adjust item quantities on load based on the final calculated amount from server
                if (frm.po_total > 0 && data.selected_term_payment_amount !== undefined) {
                    let portion = data.selected_term_payment_amount / frm.po_total;
                    let changes_made = false;
                    frm.doc.items.forEach(pi_item => {
                        const original_po_item = frm.po_items.find(po_item => po_item.name === pi_item.po_detail);
                        if (original_po_item) {
                            const new_qty = original_po_item.qty * portion;
                            if (!areFloatsEqual(pi_item.qty, new_qty)) {
                                frappe.model.set_value(pi_item.doctype, pi_item.name, 'qty', new_qty);
                                changes_made = true;
                            }
                        }
                    });
                    if (changes_made) {
                        // Use a timeout to ensure totals are calculated before refreshing other fields
                        setTimeout(() => frm.refresh_field('items'), 200);
                    }
                }

                // Use a timeout to allow grand_total to recalculate before populating display tables
                setTimeout(() => {
                    // Populate the visible billing_invoice_details table
                    frm.clear_table('billing_invoice_details');
                    // Update amount in billing_details with the now-correct grand_total if needed
                    if (data.billing_details) {
                        const term_detail = data.billing_details.find(d => d.no === 2);
                        if (term_detail) {
                            // The grand_total should now reflect the adjusted item quantities
                            term_detail.total_amount = frm.doc.net_total; // CORRECTED: Use net_total to show pre-tax amount
                        }
                    }
                    data.billing_details.forEach(function(row_data) {
                        frm.add_child('billing_invoice_details', row_data);
                    });
                    frm.refresh_field('billing_invoice_details');
                    
                    // Hide the "Add New" button for billing_invoice_details
                    frm.set_df_property('billing_invoice_details', 'cannot_add_rows', true);

                    frm.custom_billing_logic_run = true;

                    // Attach event listener to grid for row rendering
                    frm.fields_dict.billing_invoice_details.grid.grid_rows.forEach(row => {
                        // Set permissions for editing 'total_amount'
                        // For the first row (Outstanding PO), it should always be read-only
                        if (row.doc.no === 1) {
                            row.toggle_editable('total_amount', false);
                        }
                        // For the second row (Term Detail), apply conditional editing
                        else if (row.doc.no === 2) {
                            if (frm.perm[0].write && data.is_last_term && data.selected_term_invoice_basis === 'Percentage') {
                                row.toggle_editable('total_amount', true);
                            } else {
                                row.toggle_editable('total_amount', false);
                            }
                        }
                    });

                    // Hide the delete button in the grid toolbar if any row is selected
                    // This needs to be done after the grid is rendered
                    const grid = frm.fields_dict.billing_invoice_details.grid;
                    if (grid) {
                        // Use grid_buttons_filter to prevent delete buttons from appearing
                        grid.grid_buttons_filter = function(buttons) {
                            return buttons.filter(button => {
                                return !['Delete', 'Delete All'].includes(button.label);
                            });
                        };
                        // Refresh the grid to apply the filter
                        grid.refresh(); // Ensure the filter is applied immediately
                    }

                }, 300);
            } else {
                    frappe.msgprint({ title: __('Error'), indicator: 'red', message: __('Could not fetch billing data from the server.') });
            }
        }
    });
}

