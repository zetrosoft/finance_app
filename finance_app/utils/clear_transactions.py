import frappe

def run_clear_transactions():
    # Peringatan: Ini akan menghapus SEMUA data transaksional yang disebutkan.
    # HANYA JALANKAN DI SERVER PENGEMBANGAN!

    print("Memulai penghapusan data transaksional...")

    doc_types_to_delete = [
        "Journal Entry",
        "Payment Entry",
        "Purchase Invoice",
        "Sales Invoice",
        "Purchase Receipt",
        "Delivery Note",
        "Purchase Order",
        "Sales Order",
        "Stock Entry",
        # Tambahkan DocType transaksional kustom Anda di sini jika ada
    ]

    for doctype in doc_types_to_delete:
        print(f"\nMenghapus dokumen dari DocType: {doctype}")
        try:
            doc_names = frappe.get_all(doctype, pluck="name")
            
            if doc_names:
                for doc_name in doc_names:
                    try:
                        # Attempt to delete, including cancelling if submitted
                        frappe.delete_doc(doctype, doc_name, ignore_permissions=True, force=True, cancel=True)
                        print(f"  Berhasil menghapus {doctype}: {doc_name}")
                    except Exception as e:
                        print(f"  Gagal menghapus {doctype} {doc_name}: {e}")
                frappe.db.commit()
                print(f"  Semua dokumen {doctype} telah diproses dan perubahan di-commit.")
            else:
                print(f"  Tidak ada dokumen {doctype} yang ditemukan untuk dihapus.")
        except Exception as e:
            print(f"Gagal memproses DocType {doctype}: {e}")
    
    print("\nPenghapusan data transaksional selesai.")

if __name__ == "__main__":
    run_clear_transactions()