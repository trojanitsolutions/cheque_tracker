import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_custom_fields():
    custom_fields = {
        "HR Settings": [
            {
                "fieldname": "qatar_id_notification",
                "fieldtype": "Table MultiSelect",
                "label": "Qatar ID Notification",
                "insert_after": "retirement_age",
                "reqd": 0,
                "options": "Cheque Tracker Settings User",   
            },
            {
                "fieldname": "qatar_id_notify_employee",
                "fieldtype": "Check",
                "label": "Qatar ID Notify Employees",
                "insert_after": "qatar_id_notification",
                "reqd": 0,
            },
            {
                "fieldname": "qatar_id_notify_days",
                "fieldtype": "Int",
                "label": "Qatar ID Notify Days",
                "insert_after": "qatar_id_notify_employee",
                "reqd": 0,
            }
        ]
    }

    for doctype, fields in custom_fields.items(): 
        for field in fields: 
            if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
                create_custom_field(doctype, field) 
                frappe.db.commit() 
                frappe.clear_cache(doctype=doctype)

def delete_custom_fields(): 
    custom_fields_to_delete = { "HR Settings": ["qatar_id_notification","qatar_id_notify_employee", "qatar_id_notify_days"] }  

    for doctype, fields in custom_fields_to_delete.items(): 
        for field_name in fields: 
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}): 
                frappe.delete_doc("Custom Field", f"{doctype}-{field_name}", ignore_missing=True) 
                frappe.db.commit() 
                frappe.clear_cache(doctype=doctype)      