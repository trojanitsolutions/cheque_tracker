app_name = "cheque_tracker"
app_title = "Cheque Tracker"
app_publisher = "Trojan Technologies"
app_description = "Cheque Tracker"
app_email = "dev3@trojanitsolutions.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "cheque_tracker",
# 		"logo": "/assets/cheque_tracker/logo.png",
# 		"title": "Cheque Tracker",
# 		"route": "/cheque_tracker",
# 		"has_permission": "cheque_tracker.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/cheque_tracker/css/cheque_tracker.css"
# app_include_js = "/assets/cheque_tracker/js/cheque_tracker.js"

# include js, css files in header of web template
# web_include_css = "/assets/cheque_tracker/css/cheque_tracker.css"
# web_include_js = "/assets/cheque_tracker/js/cheque_tracker.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "cheque_tracker/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
	"Payment Entry": "public/js/payment_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "cheque_tracker/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "cheque_tracker.utils.jinja_methods",
# 	"filters": "cheque_tracker.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "cheque_tracker.install.before_install"
# after_install = "cheque_tracker.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "cheque_tracker.uninstall.before_uninstall"
# after_uninstall = "cheque_tracker.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "cheque_tracker.utils.before_app_install"
# after_app_install = "cheque_tracker.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "cheque_tracker.utils.before_app_uninstall"
# after_app_uninstall = "cheque_tracker.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "cheque_tracker.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cheque_tracker.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Payment Entry": {
		"before_submit": "cheque_tracker.cheque_tracker.payment_entry_hooks.validate_cheque_payment",
		"on_submit": "cheque_tracker.cheque_tracker.payment_entry_hooks.on_payment_entry_submit",
	}
}

# Scheduled Tasks
# ---------------

fixtures = [
	{"doctype": "Translation"}
]

scheduler_events = {
	"daily": [
		"cheque_tracker.cheque_tracker.tasks.send_cheque_due_notifications"
	],
}

# Testing
# -------

# before_tests = "cheque_tracker.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "cheque_tracker.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "cheque_tracker.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Sales Invoice": "cheque_tracker.cheque_tracker.overrides.get_sales_invoice_dashboard_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["cheque_tracker.utils.before_request"]
# after_request = ["cheque_tracker.utils.after_request"]

# Job Events
# ----------
# before_job = ["cheque_tracker.utils.before_job"]
# after_job = ["cheque_tracker.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"cheque_tracker.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

