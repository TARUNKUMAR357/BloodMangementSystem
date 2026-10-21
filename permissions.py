
ROLE_PERMISSIONS = {
    "ADMIN": {
        "donor_ui",
        "donation_ui",
        "stock_ui",
        "hospital_ui",
        "blood_request_ui",
        "blood_issue_ui",
        "reports_ui",
    },
    "STAFF": {
        "donor_ui",
        "donation_ui",
        "stock_ui",
        "hospital_ui",
        "reports_ui",
    },
}


def can_access_module(role, module_name):
    return module_name in ROLE_PERMISSIONS.get(role, set())

