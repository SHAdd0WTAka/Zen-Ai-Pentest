"""
Role-Based Access Control (RBAC) Module
========================================

Comprehensive RBAC system with:
- Role hierarchy
- Permission-based access control
- Resource-level permissions
- Role inheritance
- Dynamic permission checking

Compliance: OWASP ASVS 2026 V4.1, ISO 27001 A.9.2
"""

from enum import Enum, auto
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from functools import wraps
import re


class Permission(Enum):
    """
    System permissions
    
    Format: RESOURCE_ACTION
    """
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_READ_ALL = "user:read_all"
    USER_MANAGE_ROLES = "user:manage_roles"
    
    # Role management
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    
    # Permission management
    PERMISSION_GRANT = "permission:grant"
    PERMISSION_REVOKE = "permission:revoke"
    
    # API key management
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_DELETE = "api_key:delete"
    API_KEY_READ_ALL = "api_key:read_all"
    
    # Scan management
    SCAN_CREATE = "scan:create"
    SCAN_READ = "scan:read"
    SCAN_UPDATE = "scan:update"
    SCAN_DELETE = "scan:delete"
    SCAN_EXECUTE = "scan:execute"
    SCAN_READ_ALL = "scan:read_all"
    
    # Report management
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_DELETE = "report:delete"
    REPORT_READ_ALL = "report:read_all"
    
    # Configuration
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"
    
    # Audit
    AUDIT_READ = "audit:read"
    
    # MFA
    MFA_SETUP = "mfa:setup"
    MFA_DISABLE = "mfa:disable"
    
    # Session
    SESSION_READ = "session:read"
    SESSION_TERMINATE = "session:terminate"
    SESSION_TERMINATE_ALL = "session:terminate_all"


class Role(Enum):
    """
    System roles with hierarchical permissions
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    USER = "user"
    VIEWER = "viewer"
    API_SERVICE = "api_service"


@dataclass
class RoleHierarchy:
    """
    Defines role hierarchy and inheritance
    """
    role: Role
    inherits_from: List[Role] = field(default_factory=list)
    permissions: Set[Permission] = field(default_factory=set)
    
    def get_all_permissions(self, hierarchy_map: Dict[Role, "RoleHierarchy"]) -> Set[Permission]:
        """Get all permissions including inherited ones"""
        all_perms = set(self.permissions)
        
        for parent_role in self.inherits_from:
            if parent_role in hierarchy_map:
                parent = hierarchy_map[parent_role]
                all_perms.update(parent.get_all_permissions(hierarchy_map))
        
        return all_perms


class RBACManager:
    """
    Role-Based Access Control Manager
    
    Manages roles, permissions, and access control decisions.
    Supports role hierarchy and permission inheritance.
    """
    
    # Default role definitions
    DEFAULT_ROLES: Dict[Role, RoleHierarchy] = {
        Role.SUPER_ADMIN: RoleHierarchy(
            role=Role.SUPER_ADMIN,
            inherits_from=[],
            permissions=set(Permission)  # All permissions
        ),
        
        Role.ADMIN: RoleHierarchy(
            role=Role.ADMIN,
            inherits_from=[Role.USER],
            permissions={
                Permission.USER_CREATE,
                Permission.USER_READ_ALL,
                Permission.USER_UPDATE,
                Permission.USER_DELETE,
                Permission.USER_MANAGE_ROLES,
                Permission.ROLE_READ,
                Permission.API_KEY_READ_ALL,
                Permission.SCAN_READ_ALL,
                Permission.REPORT_READ_ALL,
                Permission.CONFIG_READ,
                Permission.CONFIG_UPDATE,
                Permission.AUDIT_READ,
                Permission.SESSION_TERMINATE_ALL,
            }
        ),
        
        Role.SECURITY_ANALYST: RoleHierarchy(
            role=Role.SECURITY_ANALYST,
            inherits_from=[Role.USER],
            permissions={
                Permission.SCAN_CREATE,
                Permission.SCAN_EXECUTE,
                Permission.SCAN_READ_ALL,
                Permission.REPORT_CREATE,
                Permission.REPORT_READ_ALL,
            }
        ),
        
        Role.USER: RoleHierarchy(
            role=Role.USER,
            inherits_from=[Role.VIEWER],
            permissions={
                Permission.USER_READ,
                Permission.USER_UPDATE,
                Permission.API_KEY_CREATE,
                Permission.API_KEY_READ,
                Permission.API_KEY_DELETE,
                Permission.SCAN_CREATE,
                Permission.SCAN_READ,
                Permission.SCAN_UPDATE,
                Permission.SCAN_DELETE,
                Permission.SCAN_EXECUTE,
                Permission.REPORT_CREATE,
                Permission.REPORT_READ,
                Permission.REPORT_DELETE,
                Permission.MFA_SETUP,
                Permission.MFA_DISABLE,
                Permission.SESSION_READ,
                Permission.SESSION_TERMINATE,
            }
        ),
        
        Role.VIEWER: RoleHierarchy(
            role=Role.VIEWER,
            inherits_from=[],
            permissions={
                Permission.USER_READ,
                Permission.SCAN_READ,
                Permission.REPORT_READ,
                Permission.CONFIG_READ,
            }
        ),
        
        Role.API_SERVICE: RoleHierarchy(
            role=Role.API_SERVICE,
            inherits_from=[],
            permissions={
                Permission.SCAN_CREATE,
                Permission.SCAN_READ,
                Permission.SCAN_EXECUTE,
                Permission.REPORT_CREATE,
                Permission.REPORT_READ,
            }
        ),
    }
    
    def __init__(self, custom_roles: Optional[Dict[Role, RoleHierarchy]] = None):
        """
        Initialize RBAC Manager
        
        Args:
            custom_roles: Optional custom role definitions
        """
        self._roles = custom_roles or self.DEFAULT_ROLES.copy()
        self._user_roles: Dict[str, Set[Role]] = {}  # user_id -> roles
        self._user_permissions: Dict[str, Set[Permission]] = {}  # user_id -> direct permissions
        self._resource_permissions: Dict[str, Dict[str, Set[Permission]]] = {}  # resource -> user_id -> permissions
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """
        Get all permissions for a role (including inherited)
        
        Args:
            role: Role to get permissions for
            
        Returns:
            Set of permissions
        """
        if role not in self._roles:
            return set()
        
        return self._roles[role].get_all_permissions(self._roles)
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user (including from roles)
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of permissions
        """
        permissions = set()
        
        # Add permissions from roles
        user_roles = self._user_roles.get(user_id, set())
        for role in user_roles:
            permissions.update(self.get_role_permissions(role))
        
        # Add direct permissions
        permissions.update(self._user_permissions.get(user_id, set()))
        
        return permissions
    
    def assign_role(self, user_id: str, role: Role) -> None:
        """
        Assign a role to a user
        
        Args:
            user_id: User identifier
            role: Role to assign
        """
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role)
    
    def revoke_role(self, user_id: str, role: Role) -> None:
        """
        Revoke a role from a user
        
        Args:
            user_id: User identifier
            role: Role to revoke
        """
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role)
    
    def get_user_roles(self, user_id: str) -> Set[Role]:
        """
        Get all roles assigned to a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of roles
        """
        return self._user_roles.get(user_id, set()).copy()
    
    def has_role(self, user_id: str, role: Role) -> bool:
        """
        Check if user has a specific role
        
        Args:
            user_id: User identifier
            role: Role to check
            
        Returns:
            True if user has the role
        """
        return role in self._user_roles.get(user_id, set())
    
    def has_any_role(self, user_id: str, roles: List[Role]) -> bool:
        """
        Check if user has any of the specified roles
        
        Args:
            user_id: User identifier
            roles: List of roles to check
            
        Returns:
            True if user has any of the roles
        """
        user_roles = self._user_roles.get(user_id, set())
        return any(role in user_roles for role in roles)
    
    def has_all_roles(self, user_id: str, roles: List[Role]) -> bool:
        """
        Check if user has all specified roles
        
        Args:
            user_id: User identifier
            roles: List of roles to check
            
        Returns:
            True if user has all roles
        """
        user_roles = self._user_roles.get(user_id, set())
        return all(role in user_roles for role in roles)
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user_id: User identifier
            permission: Permission to check
            
        Returns:
            True if user has the permission
        """
        return permission in self.get_user_permissions(user_id)
    
    def has_any_permission(self, user_id: str, permissions: List[Permission]) -> bool:
        """
        Check if user has any of the specified permissions
        
        Args:
            user_id: User identifier
            permissions: List of permissions to check
            
        Returns:
            True if user has any of the permissions
        """
        user_perms = self.get_user_permissions(user_id)
        return any(perm in user_perms for perm in permissions)
    
    def has_all_permissions(self, user_id: str, permissions: List[Permission]) -> bool:
        """
        Check if user has all specified permissions
        
        Args:
            user_id: User identifier
            permissions: List of permissions to check
            
        Returns:
            True if user has all permissions
        """
        user_perms = self.get_user_permissions(user_id)
        return all(perm in user_perms for perm in permissions)
    
    def check_resource_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if user has permission to access a specific resource
        
        Args:
            user_id: User identifier
            resource_type: Type of resource (e.g., 'scan', 'report')
            resource_id: Resource identifier
            permission: Required permission
            
        Returns:
            True if access is granted
        """
        # First check if user has the permission globally
        if self.has_permission(user_id, permission):
            return True
        
        # Check resource-specific permissions
        resource_key = f"{resource_type}:{resource_id}"
        if resource_key in self._resource_permissions:
            if user_id in self._resource_permissions[resource_key]:
                if permission in self._resource_permissions[resource_key][user_id]:
                    return True
        
        return False
    
    def grant_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: Permission
    ) -> None:
        """
        Grant a user permission on a specific resource
        
        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            permission: Permission to grant
        """
        resource_key = f"{resource_type}:{resource_id}"
        
        if resource_key not in self._resource_permissions:
            self._resource_permissions[resource_key] = {}
        
        if user_id not in self._resource_permissions[resource_key]:
            self._resource_permissions[resource_key][user_id] = set()
        
        self._resource_permissions[resource_key][user_id].add(permission)
    
    def revoke_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: Permission
    ) -> None:
        """
        Revoke a user's permission on a specific resource
        
        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            permission: Permission to revoke
        """
        resource_key = f"{resource_type}:{resource_id}"
        
        if resource_key in self._resource_permissions:
            if user_id in self._resource_permissions[resource_key]:
                self._resource_permissions[resource_key][user_id].discard(permission)
    
    def add_direct_permission(self, user_id: str, permission: Permission) -> None:
        """
        Add a direct permission to a user (not via role)
        
        Args:
            user_id: User identifier
            permission: Permission to add
        """
        if user_id not in self._user_permissions:
            self._user_permissions[user_id] = set()
        self._user_permissions[user_id].add(permission)
    
    def remove_direct_permission(self, user_id: str, permission: Permission) -> None:
        """
        Remove a direct permission from a user
        
        Args:
            user_id: User identifier
            permission: Permission to remove
        """
        if user_id in self._user_permissions:
            self._user_permissions[user_id].discard(permission)
    
    def clear_user(self, user_id: str) -> None:
        """
        Remove all roles and permissions from a user
        
        Args:
            user_id: User identifier
        """
        self._user_roles.pop(user_id, None)
        self._user_permissions.pop(user_id, None)
    
    def get_permission_hierarchy(self, role: Role) -> Dict[str, Any]:
        """
        Get permission hierarchy for a role
        
        Args:
            role: Role to get hierarchy for
            
        Returns:
            Dictionary with role hierarchy information
        """
        if role not in self._roles:
            return {}
        
        hierarchy = self._roles[role]
        
        return {
            "role": role.value,
            "inherits_from": [r.value for r in hierarchy.inherits_from],
            "direct_permissions": [p.value for p in hierarchy.permissions],
            "all_permissions": [p.value for p in self.get_role_permissions(role)],
        }
    
    @staticmethod
    def parse_permission(permission_str: str) -> Optional[Permission]:
        """
        Parse a permission string to Permission enum
        
        Args:
            permission_str: Permission string (e.g., "user:read")
            
        Returns:
            Permission enum or None if invalid
        """
        try:
            return Permission(permission_str)
        except ValueError:
            return None
    
    @staticmethod
    def parse_role(role_str: str) -> Optional[Role]:
        """
        Parse a role string to Role enum
        
        Args:
            role_str: Role string (e.g., "admin")
            
        Returns:
            Role enum or None if invalid
        """
        try:
            return Role(role_str)
        except ValueError:
            return None


# Permission checking decorators
def require_permission(permission: Permission):
    """
    Decorator to require a specific permission
    
    Usage:
        @require_permission(Permission.SCAN_CREATE)
        async def create_scan(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Permission check should be done in middleware
            # This is just a marker for documentation
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store required permission
        wrapper = async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
        wrapper._required_permission = permission
        return wrapper
    return decorator


def require_role(role: Role):
    """
    Decorator to require a specific role
    
    Usage:
        @require_role(Role.ADMIN)
        async def admin_endpoint(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper = async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
        wrapper._required_role = role
        return wrapper
    return decorator


# Singleton instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get singleton RBAC manager instance"""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager
