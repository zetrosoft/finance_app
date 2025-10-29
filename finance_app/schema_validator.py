
import frappe
import os
import json
import logging

def run_validation():
    """Finds doctypes that have `reference_doctype` in their JSON but not in the DB schema."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    installed_apps = frappe.get_installed_apps()
    mismatched_doctypes = []

    logging.info(f"Scanning apps: {', '.join(installed_apps)}")

    for app in installed_apps:
        app_path = frappe.get_app_path(app)
        doctype_path = os.path.join(app_path, 'doctype')

        if not os.path.exists(doctype_path):
            continue

        for doctype_folder in os.listdir(doctype_path):
            json_path = os.path.join(doctype_path, doctype_folder, f"{doctype_folder}.json")
            
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    doctype_name = data.get('name')
                    fields = data.get('fields', [])
                    is_table = data.get('istable', 0)

                    # Skip table DocTypes as they don't have their own 'tab' table
                    if is_table == 1:
                        continue

                    has_ref_doctype_field = any(field.get('fieldname') == 'reference_doctype' for field in fields)

                    if has_ref_doctype_field:
                        logging.info(f"Found 'reference_doctype' in JSON for: {doctype_name}. Verifying against DB...")
                        
                        table_name = f"tab{doctype_name}"
                        if not frappe.db.table_exists(table_name):
                            logging.warning(f"Table '{table_name}' does not exist for DocType '{doctype_name}'. Skipping.")
                            continue

                        db_columns = frappe.db.get_table_columns(doctype_name)
                        
                        if 'reference_doctype' not in db_columns:
                            logging.error(f"MISMATCH FOUND! DocType: {doctype_name}")
                            mismatched_doctypes.append(doctype_name)

                except Exception as e:
                    logging.error(f"Could not process {json_path}: {e}")

    print("\n--- VALIDATION COMPLETE ---")
    if mismatched_doctypes:
        print("The following DocTypes have a 'reference_doctype' field in their JSON definition, but NOT in the database table:")
        for dt in mismatched_doctypes:
            print(f"- {dt}")
    else:
        print("No schema mismatches found for the 'reference_doctype' field.")

