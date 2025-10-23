import frappe

def recalculate_pi_outstanding(pi_name):
    try:
        pi_doc = frappe.get_doc("Purchase Invoice", pi_name)
        pi_doc.set_status(update=True)
        frappe.db.commit()
        print(f"Successfully recalculated outstanding amount for {pi_name}")
    except Exception as e:
        print(f"Failed to recalculate outstanding amount for {pi_name}: {e}")

def recalculate_all():
    recalculate_pi_outstanding("ACC-PINV-2025-00029")

def debug_ple():
    pi_name = "ACC-PINV-2025-00029"
    ple = frappe.get_all("Payment Ledger Entry",
        filters={"voucher_no": pi_name, "voucher_type": "Purchase Invoice"},
        fields=["*"]
    )

    if ple:
        for entry in ple:
            print(frappe.as_json(entry))
    else:
        print(f"No Payment Ledger Entry found for {pi_name}")