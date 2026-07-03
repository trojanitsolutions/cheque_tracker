import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_custom_fields():
    custom_fields = {
        "Employee": [
            {
                "fieldname": "qatar_id",
                "fieldtype": "Data",
                "label": "Qatar ID",
                "insert_after": "valid_upto",
                "reqd": 1
                
            },
                {
                "fieldname": "qatar_id_expiry_date",
                "fieldtype": "Date",
                "label": "Qatar ID Expiry Date",
                "insert_after": "qatar_id",
                "reqd": 1
                
            },
            {
                "fieldname":"visa_type",
                "fieldtype":"Data",
                "label":"Visa Type",
                "insert_after":"qatar_id_expiry_date",
                "reqd":1
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
    custom_fields_to_delete = { "Employee": ["qatar_id","qatar_id_expiry_date","visa_type"] }  

    for doctype, fields in custom_fields_to_delete.items(): 
        for field_name in fields: 
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}): 
                frappe.delete_doc("Custom Field", f"{doctype}-{field_name}", ignore_missing=True) 
                frappe.db.commit() 
                frappe.clear_cache(doctype=doctype)      