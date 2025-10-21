import frappe

def run_clear_transactions():
    # Peringatan: Ini akan menghapus SEMUA data transaksional yang disebutkan.
    # HANYA JALANKAN DI SERVER PENGEMBANGAN!

    print("Memulai penghapusan data transaksional...")

    doc_types_to_delete = [
        "Payment Entry",
        "Purchase Invoice",
        "Purchase Receipt",
        "Purchase Order",
        "Sales Invoice",
        "Delivery Note",
        "Sales Order",
        "Journal Entry",
        # Tambahkan DocType transaksional kustom Anda di sini jika ada
    ]

    for doctype in doc_types_to_delete:
        print(f"\nMenghapus dokumen dari DocType: {doctype}")
        try:
            # Ambil semua nama dokumen untuk DocType ini
            doc_names = frappe.get_all(doctype, pluck="name")
            
            if doc_names:
                for doc_name in doc_names:
                    try:
                        frappe.delete_doc(doctype, doc_name, ignore_permissions=True, force=True)
                        print(f"  Berhasil menghapus {doctype}: {doc_name}")
                    except Exception as e:
                        print(f"  Gagal menghapus {doctype} {doc_name}: {e}")
                frappe.db.commit()
                print(f"  Semua dokumen {doctype} telah dihapus dan perubahan di-commit.")
            else:
                print(f"  Tidak ada dokumen {doctype} yang ditemukan untuk dihapus.")
        except Exception as e:
            print(f"Gagal memproses DocType {doctype}: {e}")
    
    print("\nPenghapusan data transaksional selesai.")

if __name__ == "__main__":
    # Ini akan dijalankan jika skrip dieksekusi langsung
    # Namun, untuk Frappe, lebih baik menggunakan bench execute
    run_clear_transactions()
