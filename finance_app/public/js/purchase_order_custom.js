// This script is loaded for the Purchase Order doctype.
// It adds custom buttons and fixes a core ERPNext bug.

// 1. Fix for the core ERPNext bug: `frm.toggle_print_button is not a function`
// We define the function during the 'setup' event, which runs before 'refresh'.
frappe.ui.form.on('Purchase Order', 'setup', function(frm) {
    frm.toggle_print_button = function(show) {
        if (show) {
            frm.page.show_button('Print');
        } else {
            frm.page.wrapper.find('[data-label="Print"]').hide();
        }
    };

    // NEW PATCH for set_action_btn_display
    frm.page.set_action_btn_display = function(btn_label, show) {
        // This is a patch for a deprecated function.
        // We will try to find the button group and show/hide it.
        // Action buttons are typically inside the inner_toolbar.
        var btn_group = frm.page.inner_toolbar.find('.btn-group[data-label="'+ btn_label +'"]');
        if (btn_group.length) { // Check if the button group exists
            if (show) {
                btn_group.show();
            } else {
                btn_group.hide();
            }
        } else {
            // If not found in inner_toolbar, try other common places or log a warning
            console.warn("Frappe Patch: Could not find action button group for label:", btn_label);
            // Fallback: try to find a button directly by label if it's not a group
            var single_button = frm.page.wrapper.find('button[data-label="'+ btn_label +'"]');
            if (single_button.length) {
                if (show) {
                    single_button.show();
                } else {
                    single_button.hide();
                }
            }
        }
    };
});

// 2. Add custom buttons without overriding the main refresh controller.
// We hook into the 'refresh' event. Frappe runs all handlers for an event,
// so this will run alongside the standard refresh logic and other custom scripts.
frappe.ui.form.on('Purchase Order', 'refresh', function(frm) {
    // --- Tombol "Get items from" ---
    if (frm.doc.docstatus === 0 && !frm.is_dirty()) {
        frm.add_custom_button(__('Get items from Material Request'), function() {
            erpnext.utils.map_current_doc({
                method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_order",
                source_doctype: "Material Request",
                target: frm,
                setters: { supplier: frm.doc.supplier || undefined },
                get_query_filters: {
                    docstatus: 1,
                    status: ["!=", "Stopped"],
                    per_ordered: ["<", 100],
                    company: frm.doc.company
                }
            });
        }, __("Get items from"));

        frm.add_custom_button(__('Get items from Supplier Quotation'), function() {
            erpnext.utils.map_current_doc({
                method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_order",
                source_doctype: "Supplier Quotation",
                target: frm,
                setters: { supplier: frm.doc.supplier || undefined },
                get_query_filters: {
                    docstatus: 1,
                    status: ["!=", "Stopped"],
                    company: frm.doc.company,
                    order_type: frm.doc.order_type
                }
            });
        }, __("Get items from"));
    }

    // --- Item Menu "Tools" ---
    // This check prevents the menu item from being added multiple times on refresh.
    if (!frm.custom_tools_menu_added) {
        frm.page.add_menu_item(__("Update Rate as per Last Purchase"), function() {
            frappe.call({
                method: "erpnext.buying.doctype.purchase_order.purchase_order.update_rate_from_last_purchase",
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (r.message) {
                        frm.refresh_field('items');
                        frappe.msgprint(__('Rates updated successfully.'));
                    } else {
                        frappe.msgprint(__('No previous purchase found for the selected items.'));
                    }
                }
            });
        });
        frm.custom_tools_menu_added = true; // Set a flag
    }
});