#!/usr/bin/env python3
"""
🎯 xAction OpenAPI Generator
OpenAPI 3.1 specification generation for actions.
"""

import inspect
from typing import Any, Dict, List, Optional, Union, get_type_hints
from dataclasses import dataclass

from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


@dataclass
class OpenAPISpec:
    """OpenAPI specification for an action."""
    operation_id: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = None
    security: List[Dict[str, List[str]]] = None
    deprecated: bool = False
    
    def __post_init__(self):
        if self.responses is None:
            self.responses = {
                "200": {
                    "description": "Successful operation",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            }
        if self.security is None:
            self.security = []


class OpenAPIGenerator:
    """
    🌟 OpenAPI Generator
    
    Generates OpenAPI 3.1 specifications for actions.
    """
    
    def __init__(self):
        self._type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            tuple: "array",
            set: "array"
        }
    
    def generate_spec(self, action: 'xAction') -> Dict[str, Any]:
        """
        Generate OpenAPI specification for an action.
        
        Args:
            action: The action to generate spec for
            
        Returns:
            OpenAPI specification dictionary
        """
        try:
            spec = OpenAPISpec(
                operation_id=action.operationId or action.api_name,
                summary=action.summary or f"Execute {action.api_name}",
                description=action.description or f"Action: {action.api_name}",
                tags=action.tags or ["actions"],
                parameters=self._extract_parameters(action),
                request_body=self._extract_request_body(action),
                responses=self._extract_responses(action),
                security=self._extract_security_schemes(action),
                deprecated=action.deprecated
            )
            
            return self._to_dict(spec)
            
        except Exception as e:
            logger.error(f"Failed to generate OpenAPI spec: {e}")
            return self._generate_fallback_spec(action)
    
    def _extract_parameters(self, action: 'xAction') -> List[Dict[str, Any]]:
        """Extract OpenAPI parameters from action."""
        parameters = []
        
        try:
            if not action.func:
                return parameters
            
            sig = inspect.signature(action.func)
            
            for param_name, param in sig.parameters.items():
                # Skip 'self' parameter
                if param_name == 'self':
                    continue
                
                param_spec = {
                    "name": param_name,
                    "in": "query",  # Default to query parameter
                    "required": param.default == inspect.Parameter.empty,
                    "schema": self._python_type_to_openapi(param.annotation)
                }
                
                # Add description if available
                if hasattr(action, 'examples') and action.examples:
                    example = action.examples.get("request", {}).get(param_name)
                    if example:
                        param_spec["example"] = example
                
                parameters.append(param_spec)
            
            return parameters
            
        except Exception as e:
            logger.error(f"Failed to extract parameters: {e}")
            return parameters
    
    def _extract_request_body(self, action: 'xAction') -> Optional[Dict[str, Any]]:
        """Extract OpenAPI request body from action."""
        try:
            # For now, we'll generate a basic request body
            # In the future, this could be enhanced based on action configuration
            return {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
            }
        except Exception as e:
            logger.error(f"Failed to extract request body: {e}")
            return None
    
    def _extract_responses(self, action: 'xAction') -> Dict[str, Dict[str, Any]]:
        """Extract OpenAPI responses from action."""
        try:
            responses = action.responses.copy() if hasattr(action, 'responses') and action.responses else {}
            
            # Ensure we have basic responses
            if "200" not in responses:
                responses["200"] = {
                    "description": "Successful operation",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            
            if "400" not in responses:
                responses["400"] = {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            
            if "500" not in responses:
                responses["500"] = {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            
            return responses
            
        except Exception as e:
            logger.error(f"Failed to extract responses: {e}")
            return {
                "200": {"description": "Successful operation"},
                "400": {"description": "Bad request"},
                "500": {"description": "Internal server error"}
            }
    
    def _extract_security_schemes(self, action: 'xAction') -> List[Dict[str, List[str]]]:
        """Extract OpenAPI security schemes from action."""
        try:
            security_config = action.security_config
            if not security_config:
                return []
            
            schemes = []
            
            if isinstance(security_config, dict):
                for scheme_name, scopes in security_config.items():
                    if isinstance(scopes, list):
                        schemes.append({scheme_name: scopes})
                    else:
                        schemes.append({scheme_name: [scopes]})
            elif isinstance(security_config, str):
                schemes.append({security_config: []})
            elif isinstance(security_config, list):
                for scheme in security_config:
                    if isinstance(scheme, str):
                        schemes.append({scheme: []})
                    elif isinstance(scheme, dict):
                        schemes.append(scheme)
            
            return schemes
            
        except Exception as e:
            logger.error(f"Failed to extract security schemes: {e}")
            return []
    
    def _python_type_to_openapi(self, python_type) -> Dict[str, Any]:
        """Convert Python type to OpenAPI schema."""
        try:
            # Handle basic types
            if python_type in self._type_mapping:
                return {"type": self._type_mapping[python_type]}
            
            # Handle Optional types
            if hasattr(python_type, '__origin__') and python_type.__origin__ is Union:
                args = python_type.__args__
                if type(None) in args:
                    # This is Optional[T]
                    non_none_args = [arg for arg in args if arg is not type(None)]
                    if non_none_args:
                        return self._python_type_to_openapi(non_none_args[0])
            
            # Handle List types
            if hasattr(python_type, '__origin__') and python_type.__origin__ is list:
                args = python_type.__args__
                if args:
                    item_type = self._python_type_to_openapi(args[0])
                    return {
                        "type": "array",
                        "items": item_type
                    }
            
            # Handle Dict types
            if hasattr(python_type, '__origin__') and python_type.__origin__ is dict:
                return {"type": "object"}
            
            # Default to string
            return {"type": "string"}
            
        except Exception as e:
            logger.error(f"Failed to convert Python type to OpenAPI: {e}")
            return {"type": "string"}
    
    def _to_dict(self, spec: OpenAPISpec) -> Dict[str, Any]:
        """Convert OpenAPISpec to dictionary."""
        return {
            "operationId": spec.operation_id,
            "summary": spec.summary,
            "description": spec.description,
            "tags": spec.tags,
            "parameters": spec.parameters,
            "requestBody": spec.request_body,
            "responses": spec.responses,
            "security": spec.security,
            "deprecated": spec.deprecated
        }
    
    def _generate_fallback_spec(self, action: 'xAction') -> Dict[str, Any]:
        """Generate fallback OpenAPI specification."""
        return {
            "operationId": action.api_name,
            "summary": f"Execute {action.api_name}",
            "description": f"Action: {action.api_name}",
            "tags": ["actions"],
            "parameters": [],
            "responses": {
                "200": {"description": "Successful operation"},
                "400": {"description": "Bad request"},
                "500": {"description": "Internal server error"}
            },
            "security": [],
            "deprecated": False
        }


# Global generator instance
openapi_generator = OpenAPIGenerator()
