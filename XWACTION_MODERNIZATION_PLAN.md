# XWAction Modernization Plan

**Company:** eXonware.com  
**Author:** Eng. Muhammad AlShehri  
**Email:** connect@exonware.com  
**Version:** 1.0.0  
**Date:** December 2025

---

## Executive Summary

This plan outlines the modernization of `xwaction` to bring it back to life using the new `xwschema` and `xwdata` libraries, while preserving all features from the MIGRAT implementation. The modernization will ensure full integration with the eXonware ecosystem and adherence to `GUIDE_DEV.md` and `GUIDE_TEST.md`.

---

## Current State Analysis

### MIGRAT Implementation Features

The existing MIGRAT implementation includes:

1. **Core Decorator (`xAction`)**
   - Comprehensive decorator with 40+ configuration options
   - Smart inference mode (`@xAction("smart")`)
   - Profile-based configuration (query, command, task, workflow, endpoint)
   - OpenAPI 3.1 compliance
   - Security integration (OAuth2, API keys, MFA, rate limiting, audit)
   - Workflow orchestration with rollback
   - Contract validation
   - FastAPI-style dependencies
   - Background execution
   - Retry and circuit breaker
   - Caching with TTL
   - Timeout management

2. **Action Profiles**
   - `ACTION` - Default general purpose
   - `QUERY` - Read-only with caching
   - `COMMAND` - State-changing with audit
   - `TASK` - Background/scheduled operations
   - `WORKFLOW` - Multi-step with rollback
   - `ENDPOINT` - API endpoint operations

3. **Engine System**
   - `NativeActionEngine` - In-process execution
   - `FastAPIActionEngine` - Web API endpoints
   - `CeleryActionEngine` - Distributed task queue
   - `PrefectActionEngine` - Workflow orchestration
   - Pluggable engine registry

4. **Handler System**
   - `ValidationActionHandler` - Input/output validation
   - `SecurityActionHandler` - Authentication, authorization, rate limiting
   - `MonitoringActionHandler` - Performance metrics and alerts
   - `WorkflowActionHandler` - Workflow orchestration and rollback
   - Phase-based execution (BEFORE, AFTER, ERROR, FINALLY)

5. **Action Registry**
   - Global action discovery
   - Profile-based organization
   - Tag-based filtering
   - Security scheme tracking
   - OpenAPI spec export
   - Metrics and statistics

6. **Execution Context**
   - `ActionContext` - Execution metadata
   - `ActionResult` - Standardized results
   - Trace ID generation
   - Metadata management

7. **OpenAPI Generation**
   - Full OpenAPI 3.1 specification
   - Operation definitions
   - Security schemes
   - Request/response schemas
   - Examples and documentation

8. **Validation System**
   - Input validation using `xSchema` (old)
   - Output validation using `xSchema` (old)
   - Contract-based validation
   - Caching for performance

### Integration Points with New Libraries

**Current Dependencies (MIGRAT):**
- `src.xlib.xdata.xSchema` → **Replace with** `exonware.xwschema.XWSchema`
- `src.xlib.xdata.xData` → **Replace with** `exonware.xwdata.XWData`
- `src.xlib.xwsystem` → **Replace with** `exonware.xwsystem` (already modernized)
- `src.xlib.xdata.core.exceptions.SchemaValidationError` → **Replace with** `exonware.xwschema.XWSchemaValidationError`

**New Integration Opportunities:**

**Core Libraries (Required):**
- **`exonware.xwschema.XWSchema`** - Input/output validation, OpenAPI schema generation, contract validation
- **`exonware.xwdata.XWData`** - Action metadata storage, workflow state management, serialization
- **`exonware.xwsystem`** - Core utilities (logging, async operations, validation interfaces, serialization, caching, security)
  - `exonware.xwsystem.io.serialization.AutoSerializer` - Format-agnostic serialization
  - `exonware.xwsystem.validation.contracts.ISchemaValidator` - Validation interfaces
  - `exonware.xwsystem.logging` - Logging utilities
  - `exonware.xwsystem.async_utils` - Async operations

**Supporting Libraries (As Needed):**
- **`exonware.xwnode.XWNode`** - If needed for complex action metadata navigation and querying
- **`exonware.xwformats`** - If needed for format-specific handling beyond AutoSerializer
- **`exonware.xwsyntax`** - If needed for parsing action definitions from various formats (e.g., OpenAPI, GraphQL)
- **`exonware.xwquery`** - If needed for querying action registries or filtering actions

**Preservation Strategy:**
- **Minimal Changes**: Preserve all MIGRAT features and behavior exactly as they were
- **Drop-in Replacement**: Only replace imports, keep all logic and structure identical
- **Backward Compatibility**: Maintain all existing APIs and behavior
- **Feature Parity**: Ensure 100% feature parity with MIGRAT implementation

---

## Modernization Strategy

**⚠️ CRITICAL: Preservation First**
- The MIGRAT implementation was working perfectly - **DO NOT CHANGE** the logic or structure
- Only replace imports and dependencies
- Maintain 100% feature parity
- Follow GUIDE_DEV.md and GUIDE_TEST.md strictly
- Use root cause analysis for any issues (never use workarounds)

### Phase 1: Foundation Setup

**Goal:** Establish modern project structure and core interfaces while preserving MIGRAT structure

#### 1.1 Project Structure
```
xwaction/
├── src/
│   └── exonware/
│       └── xwaction/
│           ├── __init__.py
│           ├── version.py
│           ├── contracts.py          # Interfaces (iAction, iActionEngine, iActionHandler)
│           ├── base.py                # Abstract base classes
│           ├── errors.py              # Error classes
│           ├── defs.py                # Enums and constants
│           ├── config.py              # Configuration classes
│           ├── facade.py              # Main xAction decorator
│           ├── engine.py              # Action execution engine
│           ├── registry.py            # Action registry
│           ├── context.py             # ActionContext and ActionResult
│           ├── core/
│           │   ├── __init__.py
│           │   ├── profiles.py        # Action profiles
│           │   ├── validation.py     # Validation engine (uses XWSchema)
│           │   ├── openapi.py         # OpenAPI generator (uses XWSchema)
│           │   └── execution.py      # Execution orchestrator
│           ├── engines/
│           │   ├── __init__.py
│           │   ├── abc.py            # Engine interfaces
│           │   ├── native.py         # Native engine
│           │   ├── fastapi.py        # FastAPI engine
│           │   ├── celery.py         # Celery engine
│           │   └── prefect.py        # Prefect engine
│           └── handlers/
│               ├── __init__.py
│               ├── abc.py            # Handler interfaces
│               ├── validation.py     # Validation handler (uses XWSchema)
│               ├── security.py       # Security handler
│               ├── monitoring.py    # Monitoring handler
│               └── workflow.py       # Workflow handler (uses XWData)
├── tests/
│   ├── 0.core/
│   ├── 1.unit/
│   └── 2.integration/
├── examples/
└── docs/
```

#### 1.2 Core Interfaces (`contracts.py`)

**Reuse Pattern:**
- **Preserve MIGRAT interfaces exactly** - only update import paths
- Follow `xwschema` and `xwdata` patterns for consistency
- Use `Protocol` for interfaces (from `xwsystem` patterns)
- Use `ABC` for abstract base classes
- **Maintain all existing method signatures and behavior**

**Key Interfaces:**
```python
# iAction - Main action interface
@runtime_checkable
class iAction(Protocol):
    # Core properties
    api_name: str
    operationId: Optional[str]
    profile: ActionProfile
    roles: List[str]
    in_types: Optional[Dict[str, XWSchema]]
    out_types: Optional[Dict[str, XWSchema]]
    
    # Methods
    def execute(context: ActionContext, instance: Any, **kwargs) -> ActionResult: ...
    def validate_input(**kwargs) -> bool: ...
    def check_permissions(context: ActionContext) -> bool: ...
    def to_openapi() -> Dict[str, Any]: ...
    def to_native() -> Dict[str, Any]: ...

# iActionEngine - Engine interface
class iActionEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    def can_execute(action_profile: ActionProfile) -> bool: ...
    
    @abstractmethod
    def execute(action: iAction, context: ActionContext, instance: Any, **kwargs) -> ActionResult: ...

# iActionHandler - Handler interface
class iActionHandler(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def supported_phases(self) -> Set[ActionHandlerPhase]: ...
    
    @abstractmethod
    def before_execution(action: iAction, context: ActionContext, **kwargs) -> bool: ...
    
    @abstractmethod
    def after_execution(action: iAction, context: ActionContext, result: Any) -> bool: ...
    
    @abstractmethod
    def on_error(action: iAction, context: ActionContext, error: Exception) -> bool: ...
```

#### 1.3 Configuration (`config.py`)

**Reuse Pattern:**
- **Preserve MIGRAT configuration structure exactly**
- Follow `XWSchemaConfig` and `XWDataConfig` patterns for consistency
- Use dataclasses for configuration (as in MIGRAT)
- Support deep copying (as in MIGRAT)
- **Maintain all existing configuration options and defaults**

**Key Classes:**
```python
@dataclass
class XWActionConfig:
    default_profile: ActionProfile = ActionProfile.ACTION
    auto_detect_profile: bool = True
    default_security: Union[str, List[str]] = "default"
    default_engine: Union[str, List[str]] = "native"
    default_handlers: List[str] = field(default_factory=lambda: ["validation"])
    enable_openapi: bool = True
    enable_metrics: bool = True
    enable_caching: bool = True
    cache_ttl: int = 300
    max_retry_attempts: int = 3
    default_timeout: Optional[float] = None
    
    def copy(self) -> 'XWActionConfig': ...

@dataclass
class ValidationConfig:
    mode: ValidationMode = ValidationMode.STRICT
    enable_caching: bool = True
    cache_ttl: int = 300
    use_xwschema: bool = True  # Use XWSchema for validation

@dataclass
class SecurityConfig:
    default_scheme: str = "api_key"
    enable_rate_limiting: bool = True
    enable_audit: bool = True
    enable_mfa: bool = False
    rate_limit_default: str = "1000/hour"
```

#### 1.4 Error Classes (`errors.py`)

**Reuse Pattern:**
- Follow `XWSchemaError` pattern
- Include context and details

**Key Classes:**
```python
class XWActionError(Exception):
    """Base exception for all xwaction errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None): ...

class XWActionValidationError(XWActionError):
    """Raised when action validation fails."""
    def __init__(self, message: str, issues: List[Dict[str, Any]] = None, ...): ...

class XWActionPermissionError(XWActionError):
    """Raised when permission check fails."""
    def __init__(self, action_name: str, required_roles: List[str], user_roles: List[str]): ...

class XWActionExecutionError(XWActionError):
    """Raised when action execution fails."""
    def __init__(self, action_name: str, original_error: Exception): ...
```

---

### Phase 2: Core Implementation

**Goal:** Implement core components with XWSchema and XWData integration

#### 2.1 Facade (`facade.py`)

**Modernization (Minimal Changes):**
- **Preserve MIGRAT facade structure and logic exactly**
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Replace `xData` imports with `XWData` (drop-in replacement)
- Replace `src.xlib.xwsystem` imports with `exonware.xwsystem`
- Replace `SchemaValidationError` with `XWSchemaValidationError`
- **Maintain all 40+ configuration options**
- **Maintain all existing methods and behavior**
- **No logic changes - only import replacements**

**Key Changes:**
```python
class XWAction(aAction):
    def __init__(
        self,
        # ... all existing parameters ...
        in_types: Optional[Dict[str, XWSchema]] = None,  # Changed from xSchema
        out_types: Optional[Dict[str, XWSchema]] = None,  # Changed from xSchema
        # ... rest of parameters ...
    ):
        # Store XWSchema instances
        self._in_types = in_types or {}
        self._out_types = out_types or {}
        
        # Use XWData for metadata storage
        self._metadata = XWData.from_native({
            "operationId": operationId,
            "api_name": api_name,
            # ... other metadata ...
        })
    
    @property
    def in_types(self) -> Optional[Dict[str, XWSchema]]:
        """Get input type schemas (XWSchema instances)."""
        return self._in_types
    
    @property
    def out_types(self) -> Optional[Dict[str, XWSchema]]:
        """Get output type schemas (XWSchema instances)."""
        return self._out_types
    
    def to_native(self) -> Dict[str, Any]:
        """Export to native format using XWData."""
        # Convert XWSchema to native
        in_types_native = {}
        for key, schema in self._in_types.items():
            if isinstance(schema, XWSchema):
                in_types_native[key] = schema.to_native()
            else:
                in_types_native[key] = schema
        
        # Use XWData for serialization
        metadata = self._metadata.to_native()
        metadata.update({
            "in_types": in_types_native,
            # ... other fields ...
        })
        return metadata
    
    @classmethod
    def from_native(cls, data: Dict[str, Any]) -> 'XWAction':
        """Create from native format using XWData."""
        # Load metadata using XWData
        metadata = XWData.from_native(data)
        
        # Convert native schemas to XWSchema
        in_types = {}
        if "in_types" in data:
            for key, schema_dict in data["in_types"].items():
                in_types[key] = XWSchema(schema_dict)
        
        out_types = {}
        if "out_types" in data:
            for key, schema_dict in data["out_types"].items():
                out_types[key] = XWSchema(schema_dict)
        
        return cls(
            # ... extract from metadata ...
            in_types=in_types,
            out_types=out_types,
            # ... rest of parameters ...
        )
```

#### 2.2 Validation Engine (`core/validation.py`)

**Modernization (Minimal Changes):**
- **Preserve MIGRAT validation logic exactly**
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Use `XWSchema.validate_sync()` and `XWSchema.validate_issues_sync()` (maintain sync API)
- **Maintain all caching logic exactly as in MIGRAT**
- **Maintain all validation rules and behavior**
- **No logic changes - only import replacements and API method name updates**

**Key Changes:**
```python
class ActionValidator:
    def __init__(self):
        self._validation_cache = {}
        self._cache_ttl = 300
    
    def validate_inputs(self, action: XWAction, inputs: Dict[str, Any]) -> ValidationResult:
        """Validate input parameters using XWSchema."""
        result = ValidationResult(valid=True)
        
        if not action.in_types:
            return result
        
        # Validate each input parameter using XWSchema
        for param_name, param_value in inputs.items():
            if param_name in action.in_types:
                schema = action.in_types[param_name]
                if isinstance(schema, XWSchema):
                    # Use XWSchema validation
                    is_valid, errors = await schema.validate_sync(param_value)
                    if not is_valid:
                        result.valid = False
                        result.errors.extend([
                            {
                                "param": param_name,
                                "issue_type": err.get("issue_type"),
                                "message": err.get("message"),
                                "node_path": err.get("node_path")
                            }
                            for err in errors
                        ])
        
        return result
    
    def validate_outputs(self, action: XWAction, output: Any) -> ValidationResult:
        """Validate output result using XWSchema."""
        result = ValidationResult(valid=True)
        
        if not action.out_types:
            return result
        
        # Validate output using XWSchema
        for schema_name, schema in action.out_types.items():
            if isinstance(schema, XWSchema):
                # Use XWSchema validation
                is_valid, errors = await schema.validate_sync(output)
                if not is_valid:
                    result.valid = False
                    result.errors.extend([
                        {
                            "schema": schema_name,
                            "issue_type": err.get("issue_type"),
                            "message": err.get("message"),
                            "node_path": err.get("node_path")
                        }
                        for err in errors
                    ])
        
        return result
```

#### 2.3 OpenAPI Generator (`core/openapi.py`)

**Modernization (Minimal Changes):**
- **Preserve MIGRAT OpenAPI generation logic exactly**
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Use `XWSchema.to_native()` for schema extraction (same as MIGRAT's `xSchema.to_native()`)
- **Maintain full OpenAPI 3.1 compliance exactly as in MIGRAT**
- **Maintain all OpenAPI generation features**
- **No logic changes - only import replacements**

**Key Changes:**
```python
class OpenAPIGenerator:
    def generate_spec(self, action: XWAction) -> Dict[str, Any]:
        """Generate OpenAPI specification using XWSchema."""
        spec = {
            "operationId": action.operationId or action.api_name,
            "summary": action.summary,
            "description": action.description,
            "tags": action.tags,
            "parameters": self._extract_parameters(action),
            "requestBody": self._extract_request_body(action),
            "responses": self._extract_responses(action),
            "security": self._extract_security_schemes(action),
            "deprecated": action.deprecated
        }
        return spec
    
    def _extract_parameters(self, action: XWAction) -> List[Dict[str, Any]]:
        """Extract parameters from XWSchema instances."""
        parameters = []
        
        if action.in_types:
            for param_name, schema in action.in_types.items():
                if isinstance(schema, XWSchema):
                    # Convert XWSchema to OpenAPI parameter
                    param_spec = {
                        "name": param_name,
                        "in": "query",  # or "path", "header", "cookie"
                        "required": True,  # Check schema for required fields
                        "schema": self._xwschema_to_openapi_schema(schema)
                    }
                    parameters.append(param_spec)
        
        return parameters
    
    def _xwschema_to_openapi_schema(self, schema: XWSchema) -> Dict[str, Any]:
        """Convert XWSchema to OpenAPI schema."""
        schema_dict = schema.to_native()
        
        # Map JSON Schema to OpenAPI schema
        # OpenAPI 3.1 uses JSON Schema, so this is mostly direct mapping
        openapi_schema = {
            "type": schema_dict.get("type"),
            "properties": schema_dict.get("properties", {}),
            "required": schema_dict.get("required", []),
            # ... map other fields ...
        }
        
        return openapi_schema
```

#### 2.4 Execution Engine (`engine.py`)

**Modernization (Minimal Changes):**
- **Preserve MIGRAT execution logic exactly**
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Replace `xData` imports with `XWData` (drop-in replacement)
- **Maintain all execution phases exactly as in MIGRAT**
- **Maintain all error handling and rollback logic**
- **No logic changes - only import replacements**

**Key Changes:**
```python
class ActionExecutor:
    def execute(self, action: XWAction, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """Execute action with XWSchema validation."""
        start_time = time.time()
        
        try:
            # Input validation using XWSchema
            validation_result = action_validator.validate_inputs(action, kwargs)
            if not validation_result.valid:
                raise XWActionValidationError(
                    "Input validation failed",
                    issues=validation_result.errors
                )
            
            # Execute BEFORE handlers
            if not self._execute_handlers(ActionHandlerPhase.BEFORE, action, context, **kwargs):
                raise XWActionError("Handler validation failed")
            
            # Permission check
            if not action.check_permissions(context):
                raise XWActionPermissionError(
                    action.api_name,
                    action.roles,
                    context.metadata.get("roles", [])
                )
            
            # Select and execute engine
            engine = self._select_engine(action)
            result = engine.execute(action, context, instance, **kwargs)
            
            # Output validation using XWSchema
            if result.success and result.data:
                output_validation = action_validator.validate_outputs(action, result.data)
                if not output_validation.valid:
                    raise XWActionValidationError(
                        "Output validation failed",
                        issues=output_validation.errors
                    )
            
            # Execute AFTER handlers
            self._execute_handlers(ActionHandlerPhase.AFTER, action, context, result=result.data, **kwargs)
            
            # Execute FINALLY handlers
            self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
            
            duration = time.time() - start_time
            result.duration = duration
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Execute ERROR handlers
            self._execute_handlers(ActionHandlerPhase.ERROR, action, context, error=e, **kwargs)
            self._execute_handlers(ActionHandlerPhase.FINALLY, action, context, **kwargs)
            
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={"error_type": type(e).__name__}
            )
```

#### 2.5 Validation Handler (`handlers/validation.py`)

**Modernization (Minimal Changes):**
- **Preserve MIGRAT validation handler logic exactly**
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Use `XWSchema.validate_issues_sync()` for structured errors (maintain sync API)
- **Maintain all caching logic exactly as in MIGRAT**
- **Maintain all validation phases and behavior**
- **No logic changes - only import replacements and API method name updates**

**Key Changes:**
```python
class ValidationActionHandler(aActionHandlerBase):
    def _perform_input_validation(self, action: XWAction, inputs: Dict[str, Any]) -> bool:
        """Perform input validation using XWSchema."""
        if not action.in_types:
            return True
        
        for param_name, param_value in inputs.items():
            if param_name in action.in_types:
                schema = action.in_types[param_name]
                if isinstance(schema, XWSchema):
                    # Use XWSchema validation
                    is_valid, issues = await schema.validate_issues_sync(param_value)
                    if not is_valid:
                        logger.warning(
                            f"Input validation failed for {param_name}: "
                            f"{[issue['message'] for issue in issues]}"
                        )
                        return False
        
        return True
    
    def _perform_output_validation(self, action: XWAction, output: Any) -> bool:
        """Perform output validation using XWSchema."""
        if not action.out_types:
            return True
        
        for schema_name, schema in action.out_types.items():
            if isinstance(schema, XWSchema):
                # Use XWSchema validation
                is_valid, issues = await schema.validate_issues_sync(output)
                if not is_valid:
                    logger.warning(
                        f"Output validation failed for {schema_name}: "
                        f"{[issue['message'] for issue in issues]}"
                    )
                    return False
        
        return True
```

#### 2.6 Workflow Handler (`handlers/workflow.py`)

**Modernization (Minimal Changes):**
- **Preserve MIGRAT workflow handler logic exactly**
- Replace `xData` imports with `XWData` (drop-in replacement)
- Use `XWData.from_native()` and `XWData.to_native()` (same API as MIGRAT's `xData`)
- **Maintain all rollback capabilities exactly as in MIGRAT**
- **Maintain all checkpoint management logic**
- **No logic changes - only import replacements**

**Key Changes:**
```python
class WorkflowActionHandler(aActionHandlerBase):
    def __init__(self):
        super().__init__(name="workflow", priority=30, async_enabled=True)
        # Use XWData for workflow state
        self._workflow_state = XWData.from_native({})
        self._rollback_stack = []
    
    def before_execution(self, action: XWAction, context: ActionContext, **kwargs) -> bool:
        """Initialize workflow state using XWData."""
        workflow_id = context.trace_id
        
        # Store workflow state in XWData
        workflow_state = {
            "action_name": action.api_name,
            "start_time": time.time(),
            "status": "running",
            "steps": [],
            "checkpoints": [],
            "rollback_points": []
        }
        
        self._workflow_state[workflow_id] = workflow_state
        
        # Add initial checkpoint
        self._add_checkpoint(workflow_id, "start", kwargs)
        
        return True
    
    def _add_checkpoint(self, workflow_id: str, checkpoint_type: str, data: Dict[str, Any]):
        """Add checkpoint using XWData."""
        checkpoint = {
            "timestamp": time.time(),
            "type": checkpoint_type,
            "data": data
        }
        
        # Use XWData for checkpoint storage
        checkpoints_path = f"{workflow_id}/checkpoints"
        if checkpoints_path in self._workflow_state:
            checkpoints = self._workflow_state[checkpoints_path]
            if isinstance(checkpoints, list):
                checkpoints.append(checkpoint)
            else:
                self._workflow_state[checkpoints_path] = [checkpoint]
        else:
            self._workflow_state[checkpoints_path] = [checkpoint]
```

---

### Phase 3: Engine Implementations

**Goal:** Modernize all engine implementations with minimal changes

#### 3.1 Native Engine (`engines/native.py`)

**Changes (Minimal):**
- **Preserve MIGRAT native engine logic exactly**
- Replace `xwsystem` imports with `exonware.xwsystem`
- **Maintain all execution behavior**
- **No logic changes - only import replacements**

#### 3.2 FastAPI Engine (`engines/fastapi.py`)

**Changes (Minimal):**
- **Preserve MIGRAT FastAPI engine logic exactly**
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Replace `xwsystem` imports with `exonware.xwsystem`
- **Maintain all FastAPI integration features**
- **No logic changes - only import replacements**

#### 3.3 Celery Engine (`engines/celery.py`)

**Changes (Minimal):**
- **Preserve MIGRAT Celery engine logic exactly**
- Replace `xData` imports with `XWData` (drop-in replacement)
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Replace `xwsystem` imports with `exonware.xwsystem`
- **Maintain all Celery integration features**
- **No logic changes - only import replacements**

#### 3.4 Prefect Engine (`engines/prefect.py`)

**Changes (Minimal):**
- **Preserve MIGRAT Prefect engine logic exactly**
- Replace `xData` imports with `XWData` (drop-in replacement)
- Replace `xSchema` imports with `XWSchema` (drop-in replacement)
- Replace `xwsystem` imports with `exonware.xwsystem`
- **Maintain all Prefect integration features**
- **No logic changes - only import replacements**

---

### Phase 4: Testing

**Goal:** Comprehensive test coverage following `GUIDE_TEST.md` strictly

**Testing Strategy:**
- Follow GUIDE_TEST.md structure exactly: `0.core/`, `1.unit/`, `2.integration/`
- Preserve all MIGRAT tests (update imports only)
- Add new tests for XWSchema/XWData integration
- Ensure 100% test pass rate
- Use hierarchical test runners as per GUIDE_TEST.md

#### 4.1 Test Structure
```
tests/
├── 0.core/
│   ├── test_facade.py          # XWAction decorator tests
│   ├── test_engine.py          # Execution engine tests
│   ├── test_registry.py        # Action registry tests
│   ├── test_validation.py     # Validation engine tests (XWSchema integration)
│   ├── test_openapi.py         # OpenAPI generation tests
│   └── test_context.py        # Context and result tests
├── 1.unit/
│   ├── test_profiles.py        # Profile tests
│   ├── test_engines.py         # Engine tests
│   ├── test_handlers.py        # Handler tests
│   ├── test_config.py          # Configuration tests
│   └── test_errors.py          # Error class tests
└── 2.integration/
    ├── test_xwschema_integration.py  # XWSchema integration tests
    ├── test_xwdata_integration.py    # XWData integration tests
    ├── test_end_to_end.py            # End-to-end workflow tests
    └── test_engines_integration.py   # Engine integration tests
```

#### 4.2 Key Test Scenarios

**XWSchema Integration:**
- Input validation with XWSchema
- Output validation with XWSchema
- Schema generation from XWSchema
- OpenAPI schema generation from XWSchema
- Validation error reporting with structured issues

**XWData Integration:**
- Action metadata storage
- Workflow state management
- Checkpoint storage
- Serialization/deserialization

**End-to-End:**
- Full action execution flow
- Validation → Execution → Result
- Error handling and rollback
- Multi-engine execution

---

### Phase 5: Documentation

**Goal:** Comprehensive documentation

#### 5.1 Documentation Structure
```
docs/
├── README.md                    # Main documentation
├── QUICK_START.md              # Quick start guide
├── XWSCHEMA_INTEGRATION.md    # XWSchema integration guide
├── XWDATA_INTEGRATION.md      # XWData integration guide
├── API_REFERENCE.md           # API reference
├── EXAMPLES.md                 # Usage examples
└── MIGRATION_GUIDE.md         # Migration from MIGRAT
```

#### 5.2 Key Documentation Topics

- XWSchema integration examples
- XWData integration examples
- Action profile usage
- Engine configuration
- Handler customization
- OpenAPI generation
- Workflow orchestration
- Error handling

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create project structure
- [ ] Implement `contracts.py` (interfaces)
- [ ] Implement `base.py` (abstract classes)
- [ ] Implement `errors.py` (error classes)
- [ ] Implement `defs.py` (enums and constants)
- [ ] Implement `config.py` (configuration)
- [ ] Implement `context.py` (ActionContext, ActionResult)

### Phase 2: Core
- [ ] Implement `facade.py` (XWAction decorator)
  - [ ] Replace `xSchema` with `XWSchema`
  - [ ] Use `XWData` for metadata
  - [ ] Maintain all MIGRAT features
- [ ] Implement `core/validation.py`
  - [ ] Use `XWSchema` for validation
  - [ ] Use `XWSchema.validate_issues()`
- [ ] Implement `core/openapi.py`
  - [ ] Use `XWSchema` for schema generation
  - [ ] Generate OpenAPI from XWSchema
- [ ] Implement `engine.py`
  - [ ] Integrate XWSchema validation
  - [ ] Use XWData for context storage
- [ ] Implement `registry.py`
  - [ ] Use XWData for action storage
  - [ ] Maintain all registry features

### Phase 3: Handlers
- [ ] Implement `handlers/validation.py`
  - [ ] Use `XWSchema` instead of `xSchema`
  - [ ] Use `XWSchema.validate_issues()`
- [ ] Implement `handlers/security.py`
  - [ ] Maintain security features
- [ ] Implement `handlers/monitoring.py`
  - [ ] Maintain monitoring features
- [ ] Implement `handlers/workflow.py`
  - [ ] Use `XWData` for state management
  - [ ] Maintain rollback capabilities

### Phase 4: Engines
- [ ] Implement `engines/native.py`
- [ ] Implement `engines/fastapi.py`
  - [ ] Use XWSchema for validation
- [ ] Implement `engines/celery.py`
  - [ ] Use XWData for serialization
- [ ] Implement `engines/prefect.py`
  - [ ] Use XWData for state

### Phase 5: Testing
- [ ] Create test structure
- [ ] Write core tests
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test XWSchema integration
- [ ] Test XWData integration
- [ ] Test end-to-end workflows

### Phase 6: Documentation
- [ ] Write README
- [ ] Write quick start guide
- [ ] Write integration guides
- [ ] Write API reference
- [ ] Write examples
- [ ] Write migration guide

---

## Library Integration Details

### XWSystem Integration

**Core Utilities:**
- **Logging**: `exonware.xwsystem.logging.get_logger()` - Replace `src.xlib.xwsystem.get_logger()`
- **Async Operations**: `exonware.xwsystem.async_utils` - For async-safe operations
- **Serialization**: `exonware.xwsystem.io.serialization.AutoSerializer` - Format-agnostic I/O
- **Validation Interfaces**: `exonware.xwsystem.validation.contracts.ISchemaValidator` - If needed for custom validators
- **Caching**: `exonware.xwsystem.caching` - If needed for action result caching
- **Security**: `exonware.xwsystem.security` - If needed for security utilities

**Usage Pattern:**
```python
# Old (MIGRAT)
from src.xlib.xwsystem import get_logger
logger = get_logger(__name__)

# New (Modern)
from exonware.xwsystem.logging import get_logger
logger = get_logger(__name__)
```

### XWNode Integration (If Needed)

**Use Cases:**
- Complex action metadata navigation
- Action registry querying with complex paths
- Nested action configuration access

**Usage Pattern:**
```python
# If needed for complex metadata navigation
from exonware.xwnode import XWNode
action_metadata = XWNode.from_native(action_dict)
nested_value = action_metadata["config.security.oauth2.scopes"]
```

### XWFormats Integration (If Needed)

**Use Cases:**
- Format-specific serialization beyond AutoSerializer
- Custom format handling for action definitions
- Format conversion for action schemas

**Usage Pattern:**
```python
# If needed for format-specific operations
from exonware.xwformats import FormatRegistry
# Use only if AutoSerializer doesn't cover the use case
```

### XWSyntax Integration (If Needed)

**Use Cases:**
- Parsing action definitions from OpenAPI/GraphQL files
- Generating action code from schema definitions
- Format conversion for action schemas

**Usage Pattern:**
```python
# If needed for parsing action definitions
from exonware.xwsyntax import XWSyntax
# Use only if manual parsing is needed
```

### XWQuery Integration (If Needed)

**Use Cases:**
- Advanced action registry querying
- Filtering actions by complex criteria
- Action discovery with complex filters

**Usage Pattern:**
```python
# If needed for advanced querying
from exonware.xwquery import XWQuery
# Use only if simple filtering is insufficient
```

## Migration Strategy

### From MIGRAT to Modern

**⚠️ CRITICAL: Minimal Changes Only**

The migration should be **drop-in replacements** with **zero logic changes**. Only update imports and API method names where necessary.

1. **Schema Migration (Drop-in Replacement):**
   ```python
   # Old (MIGRAT)
   from src.xlib.xdata import xSchema
   in_types = {"email": xSchema({"type": "string", "format": "email"})}
   is_valid = schema.validate(value)  # Returns bool
   
   # New (Modern) - Drop-in replacement
   from exonware.xwschema import XWSchema
   in_types = {"email": XWSchema({"type": "string", "format": "email"})}
   is_valid, _ = schema.validate_sync(value)  # Returns (bool, issues)
   # Note: Use validate_sync() to maintain sync API compatibility
   ```

2. **Data Migration (Drop-in Replacement):**
   ```python
   # Old (MIGRAT)
   from src.xlib.xdata import xData
   metadata = xData(action_dict)
   value = metadata["key"]
   native = metadata.to_native()
   
   # New (Modern) - Drop-in replacement
   from exonware.xwdata import XWData
   metadata = XWData.from_native(action_dict)
   value = metadata["key"]  # Same API
   native = metadata.to_native()  # Same API
   ```

3. **System Utilities Migration (Drop-in Replacement):**
   ```python
   # Old (MIGRAT)
   from src.xlib.xwsystem import get_logger
   logger = get_logger(__name__)
   
   # New (Modern) - Drop-in replacement
   from exonware.xwsystem.logging import get_logger
   logger = get_logger(__name__)  # Same API
   ```

4. **Error Migration (Drop-in Replacement):**
   ```python
   # Old (MIGRAT)
   from src.xlib.xdata.core.exceptions import SchemaValidationError
   raise SchemaValidationError("Validation failed")
   
   # New (Modern) - Drop-in replacement
   from exonware.xwschema import XWSchemaValidationError
   raise XWSchemaValidationError("Validation failed")
   ```

5. **Validation Issues Migration (Enhanced API):**
   ```python
   # Old (MIGRAT)
   schema.validate(value)  # Returns bool only
   
   # New (Modern) - Enhanced API (maintain backward compatibility)
   is_valid, issues = schema.validate_sync(value)  # Returns (bool, issues)
   # Or use validate_issues_sync() for structured errors
   issues = schema.validate_issues_sync(value)  # Returns list of issues
   ```

**Migration Checklist:**
- [ ] Replace all `src.xlib.xdata.xSchema` → `exonware.xwschema.XWSchema`
- [ ] Replace all `src.xlib.xdata.xData` → `exonware.xwdata.XWData`
- [ ] Replace all `src.xlib.xwsystem` → `exonware.xwsystem`
- [ ] Replace all `SchemaValidationError` → `XWSchemaValidationError`
- [ ] Update `schema.validate()` → `schema.validate_sync()` (maintain sync API)
- [ ] Update `schema.validate()` calls to handle `(bool, issues)` return
- [ ] Test all functionality to ensure 100% feature parity
- [ ] Verify no logic changes were made
- [ ] Verify all tests pass

---

## Dependencies

### Required (Core)
- `exonware.xwschema` - Schema validation (replaces `src.xlib.xdata.xSchema`)
- `exonware.xwdata` - Data manipulation (replaces `src.xlib.xdata.xData`)
- `exonware.xwsystem` - Core utilities (replaces `src.xlib.xwsystem`)
  - `exonware.xwsystem.io.serialization.AutoSerializer` - Format-agnostic serialization
  - `exonware.xwsystem.validation.contracts.ISchemaValidator` - Validation interfaces
  - `exonware.xwsystem.logging` - Logging utilities
  - `exonware.xwsystem.async_utils` - Async operations

### Optional (Supporting - Use as Needed)
- `exonware.xwnode` - Complex metadata navigation (if needed for action registry queries)
- `exonware.xwformats` - Format-specific handling (if needed beyond AutoSerializer)
- `exonware.xwsyntax` - Action definition parsing (if needed for OpenAPI/GraphQL parsing)
- `exonware.xwquery` - Action registry querying (if needed for advanced filtering)

### External (Engine-Specific)
- `fastapi` - FastAPI engine (optional)
- `celery` - Celery engine (optional)
- `prefect` - Prefect engine (optional)

---

## Success Criteria

1. ✅ **100% MIGRAT feature parity** - All features preserved exactly
2. ✅ **Full XWSchema integration** - Drop-in replacement for `xSchema`
3. ✅ **Full XWData integration** - Drop-in replacement for `xData`
4. ✅ **Full XWSystem integration** - Drop-in replacement for `src.xlib.xwsystem`
5. ✅ **Minimal changes** - Only import replacements, no logic changes
6. ✅ **100% test coverage** - All MIGRAT tests preserved and passing
7. ✅ **All tests passing** - Zero test failures
8. ✅ **Documentation complete** - Following GUIDE_DOCS.md
9. ✅ **Migration guide available** - Clear upgrade path
10. ✅ **Examples working** - All examples functional
11. ✅ **Performance maintained** - No performance regressions
12. ✅ **Strict adherence to GUIDE_DEV.md** - All guidelines followed
13. ✅ **Strict adherence to GUIDE_TEST.md** - Test structure and runners correct
14. ✅ **Root cause analysis** - All issues fixed at root, no workarounds

---

## Timeline Estimate

- **Phase 1:** 2-3 days
- **Phase 2:** 5-7 days
- **Phase 3:** 3-4 days
- **Phase 4:** 4-5 days
- **Phase 5:** 3-4 days
- **Phase 6:** 2-3 days

**Total:** 19-26 days

---

## Notes

### Critical Preservation Requirements
- **All features from MIGRAT must be preserved exactly** - The old version was working perfectly
- **Minimal changes only** - Only replace imports, keep all logic identical
- **No logic modifications** - Preserve all behavior, structure, and implementation details
- **Drop-in replacements** - XWSchema, XWData, XWSystem should be drop-in replacements

### Integration Requirements
- **XWSchema integration is mandatory** - Replace `xSchema` with `XWSchema`
- **XWData integration is mandatory** - Replace `xData` with `XWData`
- **XWSystem integration is mandatory** - Replace `src.xlib.xwsystem` with `exonware.xwsystem`
- **Supporting libraries as needed** - Use xwnode, xwformats, xwsyntax, xwquery only if they add value

### Quality Requirements
- **Follow GUIDE_DEV.md strictly** - All development guidelines must be followed
- **Follow GUIDE_TEST.md strictly** - Test structure, runners, and organization must be correct
- **Root cause analysis** - Never use workarounds, always fix root causes
- **Performance maintained** - No performance regressions
- **Documentation comprehensive** - Following GUIDE_DOCS.md

### Testing Requirements
- **Preserve all MIGRAT tests** - Update imports only, keep test logic
- **Add integration tests** - Test XWSchema/XWData integration
- **100% pass rate** - All tests must pass
- **Follow test structure** - Use `0.core/`, `1.unit/`, `2.integration/` as per GUIDE_TEST.md

---

**Last Updated:** December 2025  
**Status:** Planning Phase - Ready for Implementation

