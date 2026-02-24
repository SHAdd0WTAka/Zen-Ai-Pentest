"""
Tests for Role-Based Access Control (RBAC)
"""


class TestRBACManager:
    """Test RBACManager functionality"""

    def test_rbac_manager_import(self):
        """Test RBACManager can be imported"""
        from auth.rbac import RBACManager

        assert RBACManager is not None

    def test_check_permission(self):
        """Test checking permissions"""
        from auth.rbac import Permission, RBACManager, Role

        rbac = RBACManager()

        # Assign admin role to user
        rbac.assign_role("user1", Role.ADMIN)

        # Admin should have user:delete permission
        has_permission = rbac.has_permission("user1", Permission.USER_DELETE)

        assert has_permission is True

    def test_role_hierarchy(self):
        """Test role hierarchy"""
        from auth.rbac import RBACManager, Role

        rbac = RBACManager()

        # Admin has more permissions than operator
        admin_perms = rbac.get_role_permissions(Role.ADMIN)
        operator_perms = rbac.get_role_permissions(Role.SECURITY_ANALYST)

        assert len(admin_perms) >= len(operator_perms)

    def test_no_role_no_permission(self):
        """Test user without role has no permissions"""
        from auth.rbac import Permission, RBACManager

        rbac = RBACManager()

        # User without any role assignment
        has_permission = rbac.has_permission(
            "unknown_user", Permission.USER_READ
        )

        assert has_permission is False

    def test_get_user_permissions(self):
        """Test getting all permissions for a user"""
        from auth.rbac import RBACManager, Role

        rbac = RBACManager()
        rbac.assign_role("user1", Role.VIEWER)

        permissions = rbac.get_user_permissions("user1")

        assert permissions is not None
        assert isinstance(permissions, set)

    def test_assign_and_revoke_role(self):
        """Test assigning and revoking roles"""
        from auth.rbac import RBACManager, Role

        rbac = RBACManager()

        # Assign role
        rbac.assign_role("user1", Role.SECURITY_ANALYST)
        assert rbac.has_role("user1", Role.SECURITY_ANALYST) is True

        # Revoke role
        rbac.revoke_role("user1", Role.SECURITY_ANALYST)
        assert rbac.has_role("user1", Role.SECURITY_ANALYST) is False

    def test_has_any_role(self):
        """Test checking if user has any of the roles"""
        from auth.rbac import RBACManager, Role

        rbac = RBACManager()
        rbac.assign_role("user1", Role.SECURITY_ANALYST)

        has_any = rbac.has_any_role(
            "user1", [Role.ADMIN, Role.SECURITY_ANALYST]
        )

        assert has_any is True

    def test_has_all_roles(self):
        """Test checking if user has all roles"""
        from auth.rbac import RBACManager, Role

        rbac = RBACManager()
        rbac.assign_role("user1", Role.SECURITY_ANALYST)

        # User only has OPERATOR, not ADMIN
        has_all = rbac.has_all_roles(
            "user1", [Role.ADMIN, Role.SECURITY_ANALYST]
        )

        assert has_all is False


class TestRoleAndPermissionEnums:
    """Test Role and Permission enums"""

    def test_role_enum_values(self):
        """Test Role enum values"""
        from auth.rbac import Role

        assert Role.SUPER_ADMIN is not None
        assert Role.ADMIN is not None
        assert Role.SECURITY_ANALYST is not None
        assert Role.VIEWER is not None

    def test_permission_enum_values(self):
        """Test Permission enum values"""
        from auth.rbac import Permission

        assert Permission.USER_READ is not None
        assert Permission.USER_CREATE is not None
        assert Permission.USER_DELETE is not None
        assert Permission.SCAN_CREATE is not None
