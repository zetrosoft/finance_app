import frappe
import logging

# This function will be called by `bench execute`

def run_schema_diagnostics():
    # Configure logging to print to the console
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        apps = frappe.get_installed_apps()
        modules = frappe.get_all("Module Def", filters={"app_name": ("in", apps)}, pluck="name")
        all_doctypes = frappe.get_all("DocType", filters={
            "istable": 0,
            "custom": 0,
            "module": ("in", modules)
        }, pluck="name", order_by="name")
    except Exception as e:
        logging.error(f"Failed to retrieve list of DocTypes: {e}")
        return

    logging.info(f"Found {len(all_doctypes)} DocTypes to check...")

    failed_doctypes = []

    for i, doctype in enumerate(all_doctypes):
        if doctype in ["DocType", "Patch Log", "Module Def", "User"]:
            logging.info(f"Skipping known/problematic DocType: {doctype}")
            continue

        frappe.db.begin()
        try:
            logging.info(f"Checking ({i+1}/{len(all_doctypes)}): {doctype}...")
            
            doc = frappe.make_test_doc(doctype)
            doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
            
            frappe.db.rollback() # Always rollback, we are just checking for errors
            logging.info(f"SUCCESS: {doctype} passed.")

        except Exception as e:
            frappe.db.rollback()
            error_message = str(e)
            logging.error(f"--- FAILED on DocType: {doctype} ---")
            logging.error(f"Error: {error_message}")
            failed_doctypes.append({"doctype": doctype, "error": error_message})
            
            if "Unknown column 'reference_doctype'" in error_message:
                logging.warning("Found the target error. Stopping diagnostic script.")
                break

    print("\n--- DIAGNOSTIC COMPLETE ---")
    if failed_doctypes:
        print("The following DocTypes failed during test record creation:")
        for failed in failed_doctypes:
            print(f"- Doctype: {failed['doctype']}\n  Error: {failed['error']}\n")
    else:
        print("All checked DocTypes passed basic record creation.")
