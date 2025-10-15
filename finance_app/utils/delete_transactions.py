import frappe

def delete_all_po_pi(doctype_name, confirm_all_deletion=False):
    """
    Menghapus SEMUA dokumen transaksi Purchase Order atau Purchase Invoice.
    PERINGATAN: Ini adalah operasi SANGAT DESTRUKTIF dan tidak dapat dibatalkan.
    Hanya gunakan di lingkungan pengembangan/pengujian.

    Args:
        doctype_name (str): Nama DocType yang akan dihapus (misal: "Purchase Order", "Purchase Invoice").
        confirm_all_deletion (bool): Setel ke True untuk mengkonfirmasi penghapusan SEMUA dokumen.
                                     Jika False, script hanya akan menampilkan apa yang akan dihapus (mode simulasi).
    """
    if doctype_name not in ["Purchase Order", "Purchase Invoice"]:
        frappe.msgprint("DocType tidak valid. Hanya 'Purchase Order' atau 'Purchase Invoice' yang diizinkan.", title="ERROR", indicator="red")
        return

    all_doc_names = frappe.get_all(doctype_name, pluck="name")

    if not all_doc_names:
        frappe.msgprint(f"Tidak ada dokumen {doctype_name} yang ditemukan untuk dihapus.", title="INFO", indicator="blue")
        return

    if not confirm_all_deletion:
        frappe.msgprint(f"MODE SIMULASI: Jika 'confirm_all_deletion=True', SEMUA {len(all_doc_names)} dokumen {doctype_name} berikut akan dihapus: {', '.join(all_doc_names[:10])}{'...' if len(all_doc_names) > 10 else ''}", title="SIMULASI PENGHAPUSAN MASSAL", indicator="orange")
        frappe.msgprint("Untuk melanjutkan penghapusan massal, jalankan script dengan parameter 'confirm_all_deletion=True'.", title="PERINGATAN", indicator="orange")
        return

    frappe.msgprint(f"PERINGATAN KERAS: Anda akan menghapus SEMUA {len(all_doc_names)} dokumen {doctype_name} secara permanen.", title="KONFIRMASI PENGHAPUSAN MASSAL", indicator="red")
    frappe.msgprint("Penghapusan ini tidak dapat dibatalkan dan akan menghapus SEMUA data transaksi ini.", title="PERINGATAN KERAS", indicator="red")

    for name in all_doc_names:
        try:
            doc = frappe.get_doc(doctype_name, name)
            
            if doc.docstatus == 1: # Jika statusnya Submitted
                frappe.msgprint(f"Dokumen {doctype_name}: {name} berstatus Submitted. Mencoba membatalkan...", indicator="orange")
                print(f"[DEBUG] Cancelling {doctype_name}: {name}")
                doc.cancel() # Membatalkan dokumen (mengubah docstatus menjadi 2)
                doc.save() # Menyimpan perubahan status
                frappe.msgprint(f"Dokumen {doctype_name}: {name} berhasil dibatalkan.", indicator="green")
                print(f"[DEBUG] {doctype_name}: {name} cancelled.")
            
            # Sekarang hapus dokumen (statusnya seharusnya sudah 0 atau 2)
            frappe.delete_doc(doctype_name, name, ignore_permissions=True, force=True)
            frappe.msgprint(f"Dokumen {doctype_name}: {name} berhasil dihapus.", indicator="green")
            print(f"[DEBUG] Deleted {doctype_name}: {name}")
        except Exception as e:
            frappe.msgprint(f"Gagal menghapus dokumen {doctype_name}: {name}. Error: {e}", title="ERROR PENGHAPUSAN", indicator="red")
            frappe.log_error(frappe.get_traceback(), f"Failed to delete {doctype_name} {name}")
            print(f"[DEBUG] Failed to delete {doctype_name}: {name}. Error: {e}")
    
    frappe.db.commit()
    frappe.msgprint(f"Penghapusan SEMUA dokumen {doctype_name} selesai.", indicator="blue")