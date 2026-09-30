import os


# ---------------------------------------------------------
# ROLES
# ---------------------------------------------------------

ROLES = {
    "admin": {
        "kb_read",
        "kb_write",
        "kb_quarantine",
        "kb_rollback",
        "kb_schedule",
        "kb_reports",
    },
    "kb_editor": {
        "kb_read",
        "kb_write",
        "kb_quarantine",
        "kb_reports",
    },
    "kb_viewer": {
        "kb_read",
        "kb_reports",
    },
    "system": {
        "kb_read",
        "kb_write",
        "kb_quarantine",
        "kb_rollback",
        "kb_schedule",
        "kb_reports",
    },
}


# ---------------------------------------------------------
# DEFAULT ROLE
# ---------------------------------------------------------

DEFAULT_ROLE = "system"


# ---------------------------------------------------------
# GET CURRENT ROLE
# ---------------------------------------------------------

def get_current_role():
    """
    Get the current pipeline role from the environment.

    Environment variable:
        KB_PIPELINE_ROLE

    Example:
        KB_PIPELINE_ROLE=kb_editor
    """

    role = os.getenv("KB_PIPELINE_ROLE", DEFAULT_ROLE).strip().lower()

    if role not in ROLES:
        raise PermissionError(
            f"Unknown pipeline role: '{role}'. "
            f"Allowed roles: {', '.join(ROLES.keys())}"
        )

    return role


# ---------------------------------------------------------
# CHECK ROLE
# ---------------------------------------------------------

def role_exists(role):
    """Return True if the role is configured."""

    if not isinstance(role, str):
        return False

    return role.strip().lower() in ROLES


# ---------------------------------------------------------
# CHECK PERMISSION
# ---------------------------------------------------------

def has_permission(role, permission):
    """
    Check whether a role has a specific permission.
    """

    if not role_exists(role):
        return False

    role = role.strip().lower()

    return permission in ROLES[role]


# ---------------------------------------------------------
# REQUIRE PERMISSION
# ---------------------------------------------------------

def require_permission(role, permission):
    """
    Enforce a permission.

    Raises:
        PermissionError if access is denied.
    """

    if not role_exists(role):
        raise PermissionError(
            f"Access denied: unknown role '{role}'."
        )

    if not has_permission(role, permission):
        raise PermissionError(
            f"Access denied: role '{role}' does not have "
            f"permission '{permission}'."
        )

    return True


# ---------------------------------------------------------
# PERMISSION LIST
# ---------------------------------------------------------

def get_role_permissions(role):
    """
    Return all permissions assigned to a role.
    """

    if not role_exists(role):
        raise PermissionError(
            f"Unknown pipeline role: '{role}'."
        )

    role = role.strip().lower()

    return sorted(ROLES[role])


# ---------------------------------------------------------
# ACCESS SUMMARY
# ---------------------------------------------------------

def get_access_summary(role=None):
    """
    Return a safe summary of the current access configuration.
    """

    if role is None:
        role = get_current_role()

    return {
        "role": role,
        "permissions": get_role_permissions(role),
        "access_control_enabled": True,
    }


# ---------------------------------------------------------
# TEST FUNCTION
# ---------------------------------------------------------

if __name__ == "__main__":

    print("KNOWLEDGE BASE ACCESS CONTROL TEST")
    print("----------------------------------")

    for role in ROLES:
        print(f"\nRole: {role}")
        print("Permissions:")

        for permission in get_role_permissions(role):
            print(f"  - {permission}")

    print("\nPermission Tests")
    print("----------------")

    tests = [
        ("admin", "kb_rollback"),
        ("kb_editor", "kb_write"),
        ("kb_editor", "kb_rollback"),
        ("kb_viewer", "kb_read"),
        ("kb_viewer", "kb_write"),
        ("system", "kb_schedule"),
    ]

    for role, permission in tests:

        allowed = has_permission(role, permission)

        print(
            f"{role:12} | "
            f"{permission:15} | "
            f"{'ALLOWED' if allowed else 'DENIED'}"
        )