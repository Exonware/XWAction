#!/usr/bin/env python3
"""
🎯 xAction Validation Engine
Input/output validation and contract management for actions.
"""

import re
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass

from src.xlib.xdata import xSchema
from src.xlib.xwsystem import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation."""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ActionValidator:
    """
    🌟 Action Validator
    
    Handles input/output validation and contract management for actions.
    """
    
    def __init__(self):
        self._validation_cache = {}
        self._contract_cache = {}
    
    def validate_inputs(self, action: 'xAction', inputs: Dict[str, Any]) -> ValidationResult:
        """
        Validate input parameters for an action.
        
        Args:
            action: The action to validate
            inputs: Input parameters
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(valid=True)
        
        try:
            # Check if we have input validation schemas
            if not hasattr(action, 'in_types') or not action.in_types:
                return result
            
            # Validate each input parameter
            for param_name, param_value in inputs.items():
                if param_name in action.in_types:
                    schema = action.in_types[param_name]
                    if isinstance(schema, xSchema):
                        # Use xSchema validation
                        if not schema.validate(param_value):
                            result.valid = False
                            result.errors.append(f"Input validation failed for parameter {param_name}")
                    else:
                        # Basic type validation
                        if not isinstance(param_value, schema):
                            result.valid = False
                            result.errors.append(f"Type validation failed for parameter {param_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            result.valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result
    
    def validate_outputs(self, action: 'xAction', output: Any) -> ValidationResult:
        """
        Validate output result for an action.
        
        Args:
            action: The action to validate
            output: Output result
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(valid=True)
        
        try:
            # Check if we have output validation schemas
            if not hasattr(action, 'out_types') or not action.out_types:
                return result
            
            # Validate output
            for schema_name, schema in action.out_types.items():
                if isinstance(schema, xSchema):
                    # Use xSchema validation
                    if not schema.validate(output):
                        result.valid = False
                        result.errors.append(f"Output validation failed for schema {schema_name}")
                else:
                    # Basic type validation
                    if not isinstance(output, schema):
                        result.valid = False
                        result.errors.append(f"Output type validation failed for schema {schema_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Output validation error: {e}")
            result.valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result
    
    def build_validation_schema(self, action: 'xAction') -> Optional[xSchema]:
        """
        Build validation schema from action configuration.
        
        Args:
            action: The action to build schema for
            
        Returns:
            xSchema instance or None
        """
        try:
            # Check if we have contract configuration
            if not hasattr(action, 'contracts') or not action.contracts:
                return None
            
            contract_config = action.contracts
            if isinstance(contract_config, dict):
                input_contracts = contract_config.get("input", {})
            else:
                input_contracts = getattr(contract_config, 'input', {})
            
            if not input_contracts:
                return None
            
            # Build schema from contracts
            schema_data = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for field_name, constraint in input_contracts.items():
                field_schema = self._parse_contract_constraint(constraint)
                schema_data["properties"][field_name] = field_schema
                
                # Add to required if not optional
                if not constraint.endswith("?"):
                    schema_data["required"].append(field_name)
            
            return xSchema(schema_data)
            
        except Exception as e:
            logger.error(f"Failed to build validation schema: {e}")
            return None
    
    def build_contract_schema(self, action: 'xAction') -> Optional[xSchema]:
        """
        Build contract schema from action configuration.
        
        Args:
            action: The action to build schema for
            
        Returns:
            xSchema instance or None
        """
        try:
            # Check if we have contract configuration
            if not hasattr(action, 'contracts') or not action.contracts:
                return None
            
            contract_config = action.contracts
            if isinstance(contract_config, dict):
                output_contracts = contract_config.get("output", {})
            else:
                output_contracts = getattr(contract_config, 'output', {})
            
            if not output_contracts:
                return None
            
            # Build schema from contracts
            schema_data = {
                "type": "object",
                "properties": {}
            }
            
            for field_name, constraint in output_contracts.items():
                field_schema = self._parse_contract_constraint(constraint)
                schema_data["properties"][field_name] = field_schema
            
            return xSchema(schema_data)
            
        except Exception as e:
            logger.error(f"Failed to build contract schema: {e}")
            return None
    
    def _parse_contract_constraint(self, constraint: str) -> Dict[str, Any]:
        """
        Parse contract constraint string into schema definition.
        
        Args:
            constraint: Constraint string (e.g., "string:email", "integer:min:1")
            
        Returns:
            Schema definition dictionary
        """
        try:
            parts = constraint.split(":")
            base_type = parts[0]
            
            schema = {"type": base_type}
            
            # Handle specific constraints
            if base_type == "string":
                if len(parts) > 1:
                    format_type = parts[1]
                    if format_type in ["email", "uri", "date", "datetime"]:
                        schema["format"] = format_type
                    elif format_type == "pattern" and len(parts) > 2:
                        schema["pattern"] = parts[2]
                    elif format_type == "min" and len(parts) > 2:
                        schema["minLength"] = int(parts[2])
                    elif format_type == "max" and len(parts) > 2:
                        schema["maxLength"] = int(parts[2])
            
            elif base_type == "integer":
                if len(parts) > 1:
                    constraint_type = parts[1]
                    if constraint_type == "min" and len(parts) > 2:
                        schema["minimum"] = int(parts[2])
                    elif constraint_type == "max" and len(parts) > 2:
                        schema["maximum"] = int(parts[2])
            
            elif base_type == "number":
                if len(parts) > 1:
                    constraint_type = parts[1]
                    if constraint_type == "min" and len(parts) > 2:
                        schema["minimum"] = float(parts[2])
                    elif constraint_type == "max" and len(parts) > 2:
                        schema["maximum"] = float(parts[2])
            
            elif base_type == "array":
                if len(parts) > 1:
                    item_type = parts[1]
                    schema["items"] = {"type": item_type}
                    if len(parts) > 2:
                        constraint_type = parts[2]
                        if constraint_type == "min" and len(parts) > 3:
                            schema["minItems"] = int(parts[3])
                        elif constraint_type == "max" and len(parts) > 3:
                            schema["maxItems"] = int(parts[3])
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to parse constraint '{constraint}': {e}")
            return {"type": "string"}  # Fallback to string


# Global validator instance
action_validator = ActionValidator()
