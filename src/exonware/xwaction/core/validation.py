#exonware/xwaction/core/validation.py
"""
XWAction Validation Engine
Input/output validation and contract management for actions.
This module fully reuses ecosystem libraries:
- xwschema: For all validation operations
  - Uses XWSchema.validate_sync() for input/output validation
  - Uses XWSchema() constructor for schema building from contracts
  - No manual validation logic - all validation delegated to xwschema
- xwsystem: For logging (get_logger)
"""

import re
from typing import Any
from dataclasses import dataclass, field
# Fully reuse xwschema for validation
from exonware.xwschema import XWSchema, XWSchemaValidationError
# Fully reuse xwsystem for logging
from exonware.xwsystem import get_logger
logger = get_logger(__name__)

# Default context-injected params: framework provides these, skip schema validation.
# Override per action via @XWAction(context_params=("session", "message", "context", ...))
DEFAULT_CONTEXT_PARAMS = frozenset({"session", "message", "context"})


def coerce_explicit_none_to_defaults(action: Any, kwargs: dict[str, Any]) -> None:
    """
    OpenAPI/JSON clients and some bridges pass JSON null for omitted optional fields.
    Those values arrive as Python None with the key still present, so inspect.bind()
    merge logic does not replace them with signature defaults. Normalize before schema
    validation and before calling the underlying function.
    """
    params = getattr(action, "_parameters", None) or {}
    changed: list[str] = []
    for pname, pinfo in params.items():
        if pname == "self":
            continue
        if getattr(pinfo, "has_default", False) and kwargs.get(pname) is None:
            kwargs[pname] = pinfo.default
            changed.append(pname)
    if not changed:
        return
    # #region agent log
    try:
        import json
        import time
        from pathlib import Path

        payload = {
            "sessionId": "817459",
            "hypothesisId": "H-null-default",
            "location": "xwaction/core/validation.coerce_explicit_none_to_defaults",
            "message": "coerced None to signature default",
            "data": {
                "action": getattr(action, "api_name", None),
                "params": changed,
            },
            "timestamp": int(time.time() * 1000),
        }
        with Path("debug-817459.log").open("a", encoding="utf-8") as _df:
            _df.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # #endregion


def _get_context_params(action: Any) -> frozenset[str]:
    """Resolve context params for action (per-action override or default)."""
    val = getattr(action, "context_params", None) or getattr(action, "_context_params", None)
    if val is not None:
        return frozenset(val) if not isinstance(val, frozenset) else val
    return DEFAULT_CONTEXT_PARAMS


@dataclass
class ValidationResult:
    """Result of validation operation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ActionValidator:
    """
    Action Validator
    Handles input/output validation and contract management for actions.
    Fully reuses XWSchema for all validation operations:
    - Uses XWSchema.validate_sync() for input/output validation
    - Uses XWSchema() constructor for schema building from contracts
    - No manual validation logic - all validation delegated to xwschema
    - XWSchema provides: type checking, constraints, formats, nested validation
    """

    def __init__(self):
        self._validation_cache = {}
        self._contract_cache = {}

    def validate_inputs(self, action: Any, inputs: dict[str, Any]) -> ValidationResult:
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
            context_params = _get_context_params(action)
            for param_name, param_value in inputs.items():
                if param_name in context_params:
                    continue  # Skip: framework-injected (session, message, context, etc.)
                if param_name in action.in_types:
                    schema = action.in_types[param_name]
                    if isinstance(schema, XWSchema):
                        # Fully reuse XWSchema validation - uses validate_sync() which provides:
                        # - Type checking
                        # - Constraint validation (min, max, pattern, etc.)
                        # - Format validation (email, uri, date, etc.)
                        # - Nested object validation
                        # - Array validation
                        is_valid, issues = schema.validate_sync(param_value)
                        if not is_valid:
                            result.valid = False
                            error_messages: list[str] = []
                            for issue in issues:
                                if isinstance(issue, dict):
                                    error_messages.append(str(issue.get("message", "Validation failed")))
                                else:
                                    error_messages.append(str(issue))
                            result.errors.append(f"Input validation failed for parameter {param_name}: {', '.join(error_messages)}")
                    else:
                        # Fallback: Basic type validation for non-XWSchema schemas
                        # Note: Prefer using XWSchema for comprehensive validation
                        if not isinstance(param_value, schema):
                            result.valid = False
                            result.errors.append(f"Type validation failed for parameter {param_name}")
            return result
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            result.valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result

    def validate_outputs(self, action: Any, output: Any) -> ValidationResult:
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
                if isinstance(schema, XWSchema):
                    # Fully reuse XWSchema validation - uses validate_sync() which provides:
                    # - Type checking
                    # - Constraint validation (min, max, pattern, etc.)
                    # - Format validation (email, uri, date, etc.)
                    # - Nested object validation
                    # - Array validation
                    is_valid, issues = schema.validate_sync(output)
                    if not is_valid:
                        result.valid = False
                        error_messages: list[str] = []
                        for issue in issues:
                            if isinstance(issue, dict):
                                error_messages.append(str(issue.get("message", "Validation failed")))
                            else:
                                error_messages.append(str(issue))
                        result.errors.append(f"Output validation failed for schema {schema_name}: {', '.join(error_messages)}")
                else:
                    # Fallback: Basic type validation for non-XWSchema schemas
                    # Note: Prefer using XWSchema for comprehensive validation
                    if not isinstance(output, schema):
                        result.valid = False
                        result.errors.append(f"Output type validation failed for schema {schema_name}")
            return result
        except Exception as e:
            logger.error(f"Output validation error: {e}")
            result.valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result

    def build_validation_schema(self, action: Any) -> XWSchema | None:
        """
        Build validation schema from action configuration.
        Args:
            action: The action to build schema for
        Returns:
            XWSchema instance or None
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
            return XWSchema(schema_data)
        except Exception as e:
            logger.error(f"Failed to build validation schema: {e}")
            return None

    def build_contract_schema(self, action: Any) -> XWSchema | None:
        """
        Build contract schema from action configuration.
        Args:
            action: The action to build schema for
        Returns:
            XWSchema instance or None
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
            # Fully reuse XWSchema - create schema instance using xwschema capabilities
            # XWSchema provides comprehensive validation including type checking, constraints, formats
            return XWSchema(schema_data)
        except Exception as e:
            logger.error(f"Failed to build contract schema: {e}")
            return None

    def _parse_contract_constraint(self, constraint: str) -> dict[str, Any]:
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
            # Guard against empty / malformed constraints like "" or ":" (MIGRAT robustness)
            if not base_type:
                raise ValueError("Empty base type")
            # Support optional marker suffix used by contracts, e.g. "string?"
            if base_type.endswith("?"):
                base_type = base_type[:-1]
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
                    if not item_type:
                        raise ValueError("Array item type is required")
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
