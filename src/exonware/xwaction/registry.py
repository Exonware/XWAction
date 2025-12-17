#exonware/xwaction/registry.py
"""
XWAction Registry
Enhanced Global Registry for COMBINED Action Management
"""

from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from datetime import datetime
from collections import defaultdict

if TYPE_CHECKING:
    from .facade import XWAction  # Import XWAction for type hints only
    from .defs import ActionProfile


class ActionRegistry:
    """
    Enhanced Global Registry for COMBINED Action Management
    
    Provides comprehensive action discovery, management, and export capabilities
    including OpenAPI 3.1 specification generation, profile-based organization,
    metrics tracking, and security analysis.
    """
    
    # Core storage
    _actions: Dict[str, Dict[str, 'XWAction']] = {}
    _profiles: Dict[str, Set[str]] = defaultdict(set)  # profile -> action_names
    _tags: Dict[str, Set[str]] = defaultdict(set)      # tag -> action_names
    _security_schemes: Set[str] = set()
    _metrics: Dict[str, Any] = {
        "total_actions": 0,
        "total_entities": 0,
        "profiles": defaultdict(int),
        "security_schemes": defaultdict(int),
        "last_updated": None
    }
    
    @classmethod
    def register(cls, entity_type: str, action: 'XWAction'):
        """Register a COMBINED action with enhanced metadata tracking."""
        if entity_type not in cls._actions:
            cls._actions[entity_type] = {}
            cls._metrics["total_entities"] += 1
        
        # Register the action
        cls._actions[entity_type][action.api_name] = action
        cls._metrics["total_actions"] += 1
        cls._metrics["last_updated"] = datetime.now()
        
        # Track profile usage
        if hasattr(action, 'profile') and action.profile:
            profile_name = action.profile.value if hasattr(action.profile, 'value') else str(action.profile)
            cls._profiles[profile_name].add(f"{entity_type}.{action.api_name}")
            cls._metrics["profiles"][profile_name] += 1
        
        # Track tags
        if hasattr(action, 'tags') and action.tags:
            for tag in action.tags:
                cls._tags[tag].add(f"{entity_type}.{action.api_name}")
        
        # Track security schemes
        if hasattr(action, 'security_config') and action.security_config:
            security = action.security_config
            if isinstance(security, str):
                cls._security_schemes.add(security)
                cls._metrics["security_schemes"][security] += 1
            elif isinstance(security, list):
                for scheme in security:
                    cls._security_schemes.add(scheme)
                    cls._metrics["security_schemes"][scheme] += 1
            elif isinstance(security, dict):
                for scheme in security.keys():
                    cls._security_schemes.add(scheme)
                    cls._metrics["security_schemes"][scheme] += 1
    
    @classmethod
    def get_actions_for(cls, entity_type: str) -> Dict[str, 'XWAction']:
        """Get all actions for an entity type."""
        return cls._actions.get(entity_type, {})
    
    @classmethod
    def get_actions_by_profile(cls, profile: str) -> List['XWAction']:
        """Get all actions using a specific profile."""
        actions = []
        action_names = cls._profiles.get(profile, set())
        
        for action_name in action_names:
            entity_type, api_name = action_name.split('.', 1)
            if entity_type in cls._actions and api_name in cls._actions[entity_type]:
                actions.append(cls._actions[entity_type][api_name])
        
        return actions
    
    @classmethod
    def get_actions_by_tag(cls, tag: str) -> List['XWAction']:
        """Get all actions with a specific tag."""
        actions = []
        action_names = cls._tags.get(tag, set())
        
        for action_name in action_names:
            entity_type, api_name = action_name.split('.', 1)
            if entity_type in cls._actions and api_name in cls._actions[entity_type]:
                actions.append(cls._actions[entity_type][api_name])
        
        return actions
    
    @classmethod
    def get_security_schemes(cls) -> Set[str]:
        """Get all unique security schemes used."""
        return cls._security_schemes.copy()
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Get registry metrics and statistics."""
        return cls._metrics.copy()
    
    @classmethod
    def clear(cls):
        """Clear all registered actions and reset metrics."""
        cls._actions.clear()
        cls._profiles.clear()
        cls._tags.clear()
        cls._security_schemes.clear()
        cls._metrics = {
            "total_actions": 0,
            "total_entities": 0,
            "profiles": defaultdict(int),
            "security_schemes": defaultdict(int),
            "last_updated": None
        }
    
    @classmethod
    def export_all(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Export all registered actions for documentation."""
        export = {}
        for entity_type, actions in cls._actions.items():
            export[entity_type] = []
            for action in actions.values():
                export[entity_type].append(action.to_descriptor())
        return export
    
    @classmethod
    def export_openapi_spec(cls, 
                           title: str = "XWAction API",
                           version: str = "1.0.0",
                           description: Optional[str] = None) -> Dict[str, Any]:
        """
        Export complete OpenAPI 3.1 specification for all registered actions.
        
        Args:
            title: API title
            version: API version
            description: API description
            
        Returns:
            Complete OpenAPI 3.1 specification
        """
        spec = {
            "openapi": "3.1.0",
            "info": {
                "title": title,
                "version": version,
                "description": description or f"API generated from {cls._metrics['total_actions']} registered actions"
            },
            "paths": {},
            "components": {
                "securitySchemes": cls._generate_security_schemes(),
                "schemas": {}
            },
            "tags": cls._generate_openapi_tags()
        }
        
        # Generate paths from actions
        for entity_type, actions in cls._actions.items():
            for action in actions.values():
                if hasattr(action, 'to_openapi'):
                    # Generate path from action
                    path = f"/{entity_type.lower()}/{action.api_name}"
                    method = "post"  # Default to POST for actions
                    
                    if path not in spec["paths"]:
                        spec["paths"][path] = {}
                    
                    spec["paths"][path][method] = action.to_openapi()
        
        return spec
    
    @classmethod
    def _generate_security_schemes(cls) -> Dict[str, Any]:
        """Generate OpenAPI security schemes from registered actions."""
        schemes = {}
        
        for scheme_name in cls._security_schemes:
            if scheme_name == "api_key":
                schemes["apiKeyAuth"] = {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            elif scheme_name == "oauth2":
                schemes["oauth2"] = {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": "/oauth/authorize",
                            "tokenUrl": "/oauth/token",
                            "scopes": {
                                "read": "Read access",
                                "write": "Write access",
                                "admin": "Admin access"
                            }
                        }
                    }
                }
            elif scheme_name == "bearer":
                schemes["bearerAuth"] = {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
        
        return schemes
    
    @classmethod
    def _generate_openapi_tags(cls) -> List[Dict[str, str]]:
        """Generate OpenAPI tags from registered actions."""
        tags = []
        
        # Add entity-based tags
        for entity_type in cls._actions.keys():
            tags.append({
                "name": entity_type.lower(),
                "description": f"Operations for {entity_type} entities"
            })
        
        # Add custom tags from actions
        for tag_name in cls._tags.keys():
            if tag_name not in [t["name"] for t in tags]:
                tags.append({
                    "name": tag_name,
                    "description": f"Operations tagged with {tag_name}"
                })
        
        return tags
    
    @classmethod
    def find_actions(cls, 
                    entity_type: Optional[str] = None,
                    profile: Optional[str] = None,
                    tag: Optional[str] = None,
                    security_scheme: Optional[str] = None,
                    readonly: Optional[bool] = None,
                    audit_enabled: Optional[bool] = None) -> List['XWAction']:
        """
        Advanced action search with multiple filters.
        
        Args:
            entity_type: Filter by entity type
            profile: Filter by action profile
            tag: Filter by tag
            security_scheme: Filter by security scheme
            readonly: Filter by readonly status
            audit_enabled: Filter by audit status
            
        Returns:
            List of matching actions
        """
        results = []
        
        # Start with all actions or filter by entity type
        if entity_type:
            actions_to_check = cls._actions.get(entity_type, {}).values()
        else:
            actions_to_check = []
            for entity_actions in cls._actions.values():
                actions_to_check.extend(entity_actions.values())
        
        # Apply filters
        for action in actions_to_check:
            # Profile filter
            if profile and hasattr(action, 'profile'):
                action_profile = action.profile.value if hasattr(action.profile, 'value') else str(action.profile)
                if action_profile != profile:
                    continue
            
            # Tag filter
            if tag and hasattr(action, 'tags'):
                if tag not in action.tags:
                    continue
            
            # Security scheme filter
            if security_scheme and hasattr(action, 'security_config'):
                security = action.security_config
                scheme_found = False
                
                if isinstance(security, str) and security == security_scheme:
                    scheme_found = True
                elif isinstance(security, list) and security_scheme in security:
                    scheme_found = True
                elif isinstance(security, dict) and security_scheme in security:
                    scheme_found = True
                
                if not scheme_found:
                    continue
            
            # Readonly filter
            if readonly is not None and hasattr(action, 'readonly'):
                if action.readonly != readonly:
                    continue
            
            # Audit filter
            if audit_enabled is not None and hasattr(action, 'audit_enabled'):
                if action.audit_enabled != audit_enabled:
                    continue
            
            results.append(action)
        
        return results

