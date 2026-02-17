"""
Tests for Role-Based Access Control (RBAC)
"""

import pytest


class TestRBAC:
    """Test RBAC functionality"""

    def test_rbac_import(self):
        """Test RBAC can be imported"""
        from auth.rbac import RBACManager, Role, Permission
        assert RBAC is not None

    def test_check_permission(self):
        """Test checking permissions"""
        from auth.rbac import RBAC
        
        rbac = RBAC()
        
        # Admin should have all permissions
        has_permission = rbac.check_permission(
            user_role="admin",
            required_permission="users:delete"
        )
        
        assert has_permission is True

    def test_role_hierarchy(self):
        """Test role hierarchy"""
        from auth.rbac import RBAC
        
        rbac = RBAC()
        
        # Admin inherits from operator
        admin_perms = rbac.get_role_permissions("admin")
        operator_perms = rbac.get_role_permissions("operator")
        
        assert len(admin_perms) >= len(operator_perms)

    def test_invalid_role(self):
        """Test checking permission for invalid role"""
        from auth.rbac import RBAC
        
        rbac = RBAC()
        
        has_permission = rbac.check_permission(
            user_role="invalid_role",
            required_permission="users:read"
        )
        
        assert has_permission is False

    def test_get_user_permissions(self):
        """Test getting all permissions for a user"""
        from auth.rbac import RBAC
        
        rbac = RBAC()
        permissions = rbac.get_role_permissions("viewer")
        
        assert permissions is not None
        assert isinstance(permissions, list)


class TestPermissionRegistry:
    """Test permission registry"""

    def test_register_permission(self):
        """Test registering a new permission"""
        from auth.rbac import PermissionRegistry
        
        registry = PermissionRegistry()
        registry.register("custom:action", "Custom action permission")
        
        assert "custom:action" in registry.list_permissions()

    def test_get_permission_description(self):
        """Test getting permission description"""
        from auth.rbac import PermissionRegistry
        
        registry = PermissionRegistry()
        registry.register("test:perm", "Test permission")
        
        desc = registry.get_description("test:perm")
        
        assert desc == "Test permission"
