#exonware/xwaction/defs.py
"""
XWAction Definitions
Enums and constants for action system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionProfile(Enum):
    """Pre-configured action profiles with smart defaults."""
    ACTION = "action"       # Default: general purpose action
    QUERY = "query"         # Read-only operations with caching
    COMMAND = "command"     # State-changing operations with audit
    TASK = "task"           # Background/scheduled operations
    WORKFLOW = "workflow"   # Multi-step operations with rollback
    ENDPOINT = "endpoint"   # API endpoint operations


class ActionHandlerPhase(Enum):
    """Execution phases for action handlers."""
    BEFORE = "before"       # Before execution
    AFTER = "after"         # After execution
    ERROR = "error"         # On error
    FINALLY = "finally"     # Finally (always executed)
@dataclass


class ParamInfo:
    """Parameter metadata extracted from function signature."""
    name: str
    type: Any  # Type annotation (resolved via get_type_hints)
    default: Any = None  # Default value (None means no default/required)
    has_default: bool = False  # Whether parameter has a default value
    required: bool = True  # Computed from default and Optional type
    kind: Any = None  # Parameter.kind (POSITIONAL_ONLY, KEYWORD_ONLY, VAR_POSITIONAL, VAR_KEYWORD, etc.)

    def __post_init__(self):
        # Determine if required based on default and type
        if self.has_default:
            self.required = False
        elif self.type is not None:
            # Check if Optional[T] or T | None
            origin = getattr(self.type, '__origin__', None)
            args = getattr(self.type, '__args__', None)
            if origin is not None and args is not None:
                # Check for Optional/Union with None
                if type(None) in args:
                    self.required = False


@dataclass(frozen=True)
class ActionParameter:
    """
    Declarative definition of an action/command parameter aligned with XWSchema/JSON Schema.
    Used across xwaction and xwbots. Supports either a full schema override or simple type + options.

    Simple form: name, param_type, required, plus optional description, default, enum, pattern, etc.
    Full form: pass schema= with a dict (JSON Schema) for full XWSchema options (pattern, minLength,
    maximum, items, oneOf, etc.). When schema is set, it is used as-is for in_types; param_type/required
    are ignored for validation but can still be used for /help display.
    """

    name: str
    param_type: type = str
    required: bool = True
    # Full schema override (dict = JSON Schema). When set, used as-is for in_types/XWSchema.
    schema: dict[str, Any] | None = None
    # Common XWSchema/JSON Schema options (used when schema is None)
    description: str | None = None
    default: Any = None
    enum: list[Any] | None = None
    pattern: str | None = None
    minLength: int | None = None
    maxLength: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    example: Any = None
    format: str | None = None  # e.g. "date-time", "email", "uuid"

    def __str__(self) -> str:
        type_str = getattr(self.param_type, "__name__", str(self.param_type))
        return f"{self.name} ({type_str})" + ("" if self.required else " [optional]")

    def _merge_schema_field_overrides(self, out: dict[str, Any]) -> dict[str, Any]:
        """Apply explicit ActionParameter JSON Schema fields onto a base fragment."""
        if self.description is not None:
            out["description"] = self.description
        if self.default is not None:
            out["default"] = self.default
        if self.enum is not None:
            out["enum"] = self.enum
        if self.pattern is not None:
            out["pattern"] = self.pattern
        if self.minLength is not None:
            out["minLength"] = self.minLength
        if self.maxLength is not None:
            out["maxLength"] = self.maxLength
        if self.minimum is not None:
            out["minimum"] = self.minimum
        if self.maximum is not None:
            out["maximum"] = self.maximum
        if self.example is not None:
            out["example"] = self.example
        if self.format is not None:
            out["format"] = self.format
        return out

    def to_schema_dict(self) -> dict[str, Any]:
        """Build a JSON Schema dict from this parameter."""
        if self.schema is not None:
            return dict(self.schema)
        tid = getattr(self.param_type, "__kind_id__", None)
        if isinstance(tid, str) and tid.strip():
            from exonware.xwschema.types_base import kind_for

            spec = kind_for(tid.strip())
            if spec is not None:
                out = dict(spec.to_native())
                return self._merge_schema_field_overrides(out)
        # Plain str with no explicit constraints: reuse built-in kinds from the parameter name.
        if self.param_type is str:
            has_explicit = (
                self.enum is not None
                or self.pattern is not None
                or self.format is not None
                or self.minLength is not None
                or self.maxLength is not None
                or self.minimum is not None
                or self.maximum is not None
            )
            if not has_explicit:
                from exonware.xwschema.types_base import kind_for_param_name, schema_fragment

                kid = kind_for_param_name(self.name)
                if kid:
                    try:
                        out = dict(schema_fragment(kid))
                        return self._merge_schema_field_overrides(out)
                    except KeyError:
                        pass
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        out: dict[str, Any] = {"type": type_map.get(self.param_type, "string")}
        return self._merge_schema_field_overrides(out)
