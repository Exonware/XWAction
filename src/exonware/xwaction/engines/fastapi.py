#exonware/xwaction/engines/fastapi.py
"""
FastAPI Action Engine Implementation
Web API execution engine for XWAction.
"""

import time
import inspect
import functools
import sys
import re
from typing import Any
from .base import AActionEngineBase
from .defs import ActionEngineType
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
from exonware.xwsystem import get_logger
# Optional dependencies imported directly (using xwsystem lazy import support)
from fastapi import FastAPI, HTTPException, Body, Depends, Request, Response, BackgroundTasks, Form, Query
from fastapi.params import Param, Depends as DependsType, Body as BodyParam
from pydantic import Field
from collections.abc import Callable, Coroutine
logger = get_logger(__name__)


class FastAPIActionEngine(AActionEngineBase):
    """
    FastAPI Action Engine
    Executes actions as FastAPI endpoints with automatic OpenAPI generation.
    This engine is ideal for web API endpoints.
    """

    def __init__(self):
        super().__init__(
            name="fastapi",
            engine_type=ActionEngineType.EXECUTION,
            priority=80  # High priority for API endpoints
        )
        self._app: FastAPI | None = None
        self._registered_routes: dict[str, dict[str, str]] = {}

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """FastAPI engine can execute endpoint and query profiles."""
        return action_profile in [
            ActionProfile.ENDPOINT, 
            ActionProfile.QUERY, 
            ActionProfile.COMMAND
        ]

    def execute(self, action: Any, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action as FastAPI endpoint.
        NOTE: This method is primarily for internal consistency.
        The actual execution for web requests happens via the route handler
        created in _create_route_handler, which handles async properly.
        """
        start_time = time.time()
        try:
            if not self._app:
                logger.warning("FastAPI app not initialized, falling back to native execution")
                return self._fallback_execution(action, context, instance, **kwargs)
            # Execute the function
            result = self._execute_function(action, instance, **kwargs)
            # Note: If result is a coroutine, we can't await it here as execute is sync.
            # This is a limitation of the synchronous execute protocol.
            # The route handler handles this correctly.
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            return ActionResult(
                success=True,
                data=result,
                duration=duration,
                metadata={
                    "engine": "fastapi",
                    "http_method": getattr(action, 'http_method', 'POST'),
                    "endpoint_path": getattr(action, 'endpoint_path', f"/{action.api_name}")
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            logger.error(f"FastAPI engine execution failed: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "engine": "fastapi",
                    "error_type": type(e).__name__
                }
            )

    def _create_route_handler(self, 
                              action: Any, 
                              func: Callable, 
                              combined_sig: inspect.Signature,
                              path_param_names: set[str],
                              method: str,
                              path: str,
                              original_sig: inspect.Signature | None = None) -> Callable:
        """
        Factory to create the actual route handler function.
        Handles both sync and async actions, metrics, and error handling.
        """
        is_coroutine = inspect.iscoroutinefunction(func)
        # Check if action is a bound method
        # If action itself is a bound method, we need to handle it carefully
        is_bound_method = hasattr(action, '__self__') and hasattr(action, '__func__')
        # Bound instance for context if available
        bound_instance = action.__self__ if is_bound_method else None
        # Use a unified execution helper to handle metrics and errors
        async def execute_unified(args: tuple, kwargs: dict):
            start_time = time.time()
            # Create ActionContext
            context = ActionContext(
                actor="api", 
                source="fastapi",
                metadata={
                    "http_method": method, 
                    "endpoint_path": path,
                    "engine": "fastapi"
                }
            )
            # Bind arguments to the combined signature (Path params + Body + Dependencies)
            try:
                bound = combined_sig.bind(*args, **kwargs)
                bound.apply_defaults()
                bound_args = bound.arguments
            except TypeError as e:
                logger.error(f"Signature binding failed for {action.api_name}: {e}")
                self._update_metrics(time.time() - start_time, False)
                raise HTTPException(status_code=400, detail="Invalid request parameters")
            # Extract arguments for the actual function call
            execution_kwargs = {}
            # 1. Path Params
            for name in path_param_names:
                if name in bound_args:
                    execution_kwargs[name] = bound_args[name]
            # 2. Body Params (if a Pydantic model was created and injected as 'request_body')
            request_body = bound_args.get('request_body')
            if request_body:
                if hasattr(request_body, 'model_dump'):
                    # Unwrap Pydantic model fields back to kwargs
                    body_kwargs = request_body.model_dump()
                    execution_kwargs.update(body_kwargs)
                elif isinstance(request_body, dict):
                    execution_kwargs.update(request_body)
            # 3. Dependencies and other params
            # Iterate over all bound args and add them if they aren't path params or the special request_body
            for name, value in bound_args.items():
                if name not in path_param_names and name != 'request_body':
                    # This includes params injected by Depends, Request, Response, etc.
                    # And also Body params if we didn't use a composite Pydantic model
                    # And also auto-extracted Form/Query params from in_types
                    execution_kwargs[name] = value
            # Remove 'self' if it crept in
            execution_kwargs.pop('self', None)
            # When we auto-extracted parameters from in_types, attach them to Request object
            # so functions with only 'request' parameter can access them
            request_obj = execution_kwargs.get('request')
            if request_obj and isinstance(request_obj, Request) and original_sig:
                # Get auto-extracted params (params in execution_kwargs but not in original signature)
                original_param_names = set(original_sig.parameters.keys())
                auto_extracted = {k: v for k, v in execution_kwargs.items() 
                                if k not in original_param_names and k not in path_param_names}
                # Attach extracted params to Request object as attributes
                for param_name, param_value in auto_extracted.items():
                    setattr(request_obj, param_name, param_value)
            # Filter execution_kwargs to only include parameters the original function expects
            # This prevents TypeError when calling function with unexpected kwargs
            if original_sig:
                original_param_names = set(original_sig.parameters.keys())
                filtered_kwargs = {k: v for k, v in execution_kwargs.items() 
                                 if k in original_param_names or k in path_param_names}
                execution_kwargs = filtered_kwargs
            try:
                # Execute the action using the base class async helper
                # This handles sync/async and thread offloading transparently
                result = await self._execute_function_async(
                    action, 
                    bound_instance, 
                    **execution_kwargs
                )
                # Success
                duration = time.time() - start_time
                self._update_metrics(duration, True)
                return result
            except HTTPException:
                # Re-raise HTTPExceptions as-is
                self._update_metrics(time.time() - start_time, False)
                raise
            except Exception as e:
                duration = time.time() - start_time
                self._update_metrics(duration, False)
                logger.error(f"FastAPI execution failed for {action.api_name}: {e}")
                # Determine status code based on error type
                status_code = 400  # Default to Bad Request for logic errors
                if isinstance(e, (TypeError, ValueError)):
                    status_code = 400
                elif "Permission" in type(e).__name__ or "Auth" in type(e).__name__:
                    status_code = 403
                elif "NotFound" in type(e).__name__:
                    status_code = 404
                else:
                    status_code = 500  # Internal Server Error for others
                raise HTTPException(status_code=status_code, detail=str(e))
        # Create the wrapper function that FastAPI will see
        # We always create an async wrapper to handle both sync and async underlying functions efficiently.
        # If the action is configured as streaming, engines that understand streaming can
        # return an async iterator/coroutine which we wrap in StreamingResponse here.
        from fastapi.responses import StreamingResponse

        is_streaming = bool(getattr(action, "stream", False))
        stream_type = getattr(action, "stream_type", None) or "ndjson"

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await execute_unified(args, kwargs)
            if not is_streaming:
                return result
            # If result is already a StreamingResponse, return as-is
            if isinstance(result, StreamingResponse):
                return result
            # If result is an async iterator or async generator, wrap it directly
            if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
                media_type = (
                    "application/x-ndjson"
                    if stream_type == "ndjson"
                    else "text/event-stream" if stream_type == "sse" else "application/octet-stream"
                )
                return StreamingResponse(result, media_type=media_type)
            # If result is a normal value, just return it (engine/user misconfiguration)
            return result

        return wrapper

    def register_action(self, action: Any, app: Any, path: str = None, method: str = "POST") -> bool:
        """
        Register an action as a FastAPI endpoint.
        """
        try:
            self._app = app
            # Resolve XWAction wrapper: @XWAction decorator returns a wrapper with .xwaction pointing to the real action
            if getattr(action, 'xwaction', None) is not None:
                action = action.xwaction
            # Use provided path, or check for endpoint_path attribute, or fall back to api_name
            # The path parameter from AUTH_SERVICES should take precedence
            if path:
                endpoint_path = path
            elif hasattr(action, 'endpoint_path') and action.endpoint_path:
                endpoint_path = action.endpoint_path
            else:
                endpoint_path = f"/{action.api_name}"
            # Use method from action if available, otherwise use provided method
            if hasattr(action, 'method') and action.method:
                method = action.method.upper()
            else:
                method = method.upper()
            # Handle bound methods vs functions
            if hasattr(action, '__self__') and hasattr(action, '__func__'):
                func = action.__func__
                bound_method = action
            else:
                func = getattr(action, 'func', None)
                bound_method = None
            if not func:
                logger.error(f"Action {action.api_name} has no function to register")
                return False
            # --- 1. Analyze Function Signature ---
            sig = inspect.signature(func)
            type_hints = self._resolve_type_hints(func)
            # Identify Path Parameters (from URL regex)
            path_param_names = set(re.findall(r'\{(\w+)\}', endpoint_path))
            # Check if we need to auto-extract from Request based on in_types
            # This happens when:
            # 1. Function only has Request parameter (or Request + special types)
            # 2. in_types is defined with schemas
            # 3. HTTP method is known
            has_only_request = False
            request_param = None
            in_types = getattr(action, 'in_types', None) or {}
            # Check if function signature only has Request (and maybe Response/BackgroundTasks)
            regular_params = [p for p in sig.parameters.values() 
                            if p.name not in ('self', 'cls') 
                            and p.annotation not in (Request, Response, BackgroundTasks)
                            and not isinstance(p.default, (DependsType, BodyParam, Param))]
            request_params = [p for p in sig.parameters.values() 
                            if p.annotation == Request]
            if len(regular_params) == 0 and len(request_params) == 1 and in_types:
                has_only_request = True
                request_param = request_params[0]
                logger.debug(f"[{action.api_name}] Auto-extracting parameters from Request based on in_types")
            # Parameter categorization
            body_params_fields = {}
            query_params_fields = {}
            form_params_fields = {}
            new_params = []
            is_body_method = method.upper() in ("POST", "PUT", "PATCH")
            is_get_method = method.upper() == "GET"
            # If we have in_types and only Request parameter, create parameters from in_types
            if has_only_request and in_types:
                for param_name, schema in in_types.items():
                    # Skip path parameters (they're already handled)
                    if param_name in path_param_names:
                        continue
                    # Convert schema to Python type and default
                    param_type = str  # Default to str
                    param_default = inspect.Parameter.empty
                    # Extract type from schema
                    if isinstance(schema, dict):
                        schema_type = schema.get("type", "string")
                        if schema_type == "integer":
                            param_type = int
                        elif schema_type == "number":
                            param_type = float
                        elif schema_type == "boolean":
                            param_type = bool
                        elif schema_type == "array":
                            param_type = list
                        elif schema_type == "object":
                            param_type = dict
                        else:
                            param_type = str
                        # Check if optional (has default or not required)
                        if "default" in schema:
                            param_default = schema["default"]
                    # Create parameter based on HTTP method
                    if is_get_method:
                        # GET: Query parameters
                        query_params_fields[param_name] = (param_type, param_default)
                    elif is_body_method:
                        # POST/PUT/PATCH: Form data (for OAuth 2.0 compatibility)
                        # We use Form() for form-urlencoded data
                        form_params_fields[param_name] = (param_type, param_default)
            for param_name, param in sig.parameters.items():
                # Skip 'self' and 'cls'
                if param_name in ('self', 'cls'):
                    continue
                annotation = type_hints.get(param_name, param.annotation)
                if annotation == inspect.Parameter.empty:
                    annotation = Any
                # Check for Path Parameters
                if param_name in path_param_names:
                    # Keep as is, just ensure annotation is updated
                    new_params.append(param.replace(annotation=annotation))
                    continue
                # Check for Dependencies and Special FastAPI types
                # If param has a default that is an instance of Depends/Security/etc,
                # OR if the type is Request/Response/etc, keep it in signature.
                is_dependency = (
                    isinstance(param.default, (DependsType, BodyParam, Param)) or 
                    (hasattr(param.default, '__class__') and 
                     any(c.__name__ == 'Depends' for c in param.default.__class__.__mro__))
                )
                is_special_type = annotation in (Request, Response, BackgroundTasks)
                if is_dependency or is_special_type:
                    # Keep exactly as is
                    new_params.append(param.replace(annotation=annotation))
                    continue
                # Check compatibility with Pydantic Body (using base class helper)
                if not self._is_pydantic_compatible(annotation):
                    # If not compatible and not a dependency, strict filtering or keep as query?
                    # For now, if it's not compatible, we keep it in signature and hope FastAPI
                    # can handle it (e.g. as Query) or it fails at startup which is better than runtime.
                    new_params.append(param.replace(annotation=annotation))
                    continue
                # Handle Body Parameters
                if is_body_method:
                    # It's a candidate for the Body model
                    if param.default != inspect.Parameter.empty:
                        field_def = (annotation, Field(default=param.default))
                    else:
                        field_def = (annotation, ...)
                    body_params_fields[param_name] = field_def
                else:
                    # GET/DELETE: Everything else is Query
                    new_params.append(param.replace(annotation=annotation))
            # Add auto-generated parameters from in_types
            if has_only_request and in_types:
                # Add Request parameter first (if it exists)
                if request_param:
                    new_params.append(request_param)
                # Add query parameters for GET
                if is_get_method and query_params_fields:
                    for param_name, (param_type, param_default) in query_params_fields.items():
                        if param_default != inspect.Parameter.empty:
                            default = Query(default=param_default)
                        else:
                            default = Query(...)
                        new_params.append(
                            inspect.Parameter(
                                param_name,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                annotation=param_type,
                                default=default
                            )
                        )
                # Add form parameters for POST/PUT/PATCH
                elif is_body_method and form_params_fields:
                    for param_name, (param_type, param_default) in form_params_fields.items():
                        if param_default != inspect.Parameter.empty:
                            default = Form(default=param_default)
                        else:
                            default = Form(...)
                        new_params.append(
                            inspect.Parameter(
                                param_name,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                annotation=param_type,
                                default=default
                            )
                        )
            else:
                # Normal flow: add Request if it exists
                for param_name, param in sig.parameters.items():
                    if param.annotation == Request and param_name not in [p.name for p in new_params]:
                        new_params.append(param)
            # --- 2. Create Pydantic Model for Body (if needed) ---
            RequestModel = None
            if is_body_method and body_params_fields:
                func_module = getattr(func, '__module__', None)
                # Use base class helper to create input model
                RequestModel = self._create_input_model(action.api_name, body_params_fields, func_module)
            # --- 3. Add Body Parameter to Signature ---
            if RequestModel:
                new_params.append(
                    inspect.Parameter(
                        'request_body',
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=Body(...),
                        annotation=RequestModel
                    )
                )
            elif is_body_method and body_params_fields:
                # Fallback: Model creation failed, add individual Body params
                for name, (ann, val) in body_params_fields.items():
                    default_val = val.default if isinstance(val, Field) else val
                    p_default = inspect.Parameter.empty if default_val is ... else default_val
                    new_params.append(
                        inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=ann, default=p_default)
                    )
            # --- 4. Create Combined Signature ---
            combined_sig = sig.replace(parameters=new_params)
            # --- 5. Create Handler Wrapper ---
            action_for_handler = bound_method if bound_method else action
            route_handler = self._create_route_handler(
                action_for_handler, func, combined_sig, path_param_names, method, endpoint_path, original_sig=sig
            )
            # Update Wrapper Metadata for OpenAPI
            # We explicitly do NOT delete the return annotation here to preserve Response Schema.
            # However, we must ensure the return type is valid for FastAPI.
            route_handler.__signature__ = combined_sig
            # Update annotations for FastAPI to see
            route_handler.__annotations__ = {
                p.name: p.annotation for p in new_params 
                if p.annotation != inspect.Parameter.empty
            }
            # Preserve return annotation if valid
            return_annotation = type_hints.get('return', sig.return_annotation)
            if return_annotation != inspect.Parameter.empty:
                route_handler.__annotations__['return'] = return_annotation
            route_handler.__doc__ = func.__doc__ or getattr(action, 'description', None)
            if hasattr(func, '__module__'):
                route_handler.__module__ = func.__module__
            # --- 6. Register with FastAPI App ---
            # Use add_api_route to explicitly set the path and ensure OpenAPI schema uses it
            operation_id = getattr(action, 'operationId', None) or action.api_name
            summary = getattr(action, 'summary', None)
            description = getattr(action, 'description', None)
            tags = getattr(action, 'tags', None) or []
            try:
                # Use add_api_route to ensure the path is explicitly set
                app.add_api_route(
                    endpoint_path,
                    route_handler,
                    methods=[method.upper()],
                    operation_id=operation_id,
                    summary=summary,
                    description=description,
                    tags=tags if tags else None,
                    name=operation_id,
                )
            except Exception as reg_error:
                logger.error(f"Failed to register action '{action.api_name}' as FastAPI endpoint: {reg_error}")
                raise
            self._registered_routes[action.api_name] = {
                "path": endpoint_path,
                "method": method
            }
            # Generic callback mechanism: if app.state has an on_action_registered callback, call it
            # This allows higher-level frameworks (like xwapi) to hook into action registration
            # without FastAPIActionEngine knowing about them
            if app and hasattr(app, 'state'):
                on_action_registered = getattr(app.state, 'on_action_registered', None)
                if callable(on_action_registered):
                    try:
                        on_action_registered(action)
                    except Exception as e:
                        logger.debug(f"on_action_registered callback failed: {e}")
            logger.info(f"Registered action {action.api_name} as FastAPI endpoint: {method} {endpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to register action {getattr(action, 'api_name', 'unknown')} as FastAPI endpoint: {e}", exc_info=True)
            return False

    def setup(self, config: dict[str, Any]) -> bool:
        """Setup FastAPI engine."""
        try:
            if "app" in config:
                self._app = config["app"]
            elif "create_app" in config:
                self._app = config["create_app"]()
            logger.debug("FastAPI action engine setup completed")
            return True
        except Exception as e:
            logger.error(f"Failed to setup FastAPI engine: {e}")
            return False
