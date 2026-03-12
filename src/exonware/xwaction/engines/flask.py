#exonware/xwaction/engines/flask.py
"""
Flask Action Engine Implementation
Web API execution engine for XWAction using Flask.
"""

import time
import inspect
import re
from typing import Any, Optional, Callable
from .base import AActionEngineBase
from .defs import ActionEngineType
from ..context import ActionContext, ActionResult
from ..defs import ActionProfile
from exonware.xwsystem import get_logger
from flask import Flask, request, jsonify, make_response
from flask.views import View
from pydantic import ValidationError, Field
logger = get_logger(__name__)


class FlaskActionEngine(AActionEngineBase):
    """
    Flask Action Engine
    Executes actions as Flask endpoints.
    """

    def __init__(self):
        super().__init__(
            name="flask",
            engine_type=ActionEngineType.EXECUTION,
            priority=70  # Slightly lower priority than FastAPI
        )
        self._app: Optional[Flask] = None
        self._registered_routes: dict[str, dict[str, str]] = {}

    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """Flask engine can execute endpoint and query profiles."""
        return action_profile in [
            ActionProfile.ENDPOINT, 
            ActionProfile.QUERY, 
            ActionProfile.COMMAND
        ]

    def execute(self, action: Any, context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action as Flask endpoint (fallback/internal use).
        """
        start_time = time.time()
        try:
            if not self._app:
                logger.warning("Flask app not initialized, falling back to native execution")
                return self._fallback_execution(action, context, instance, **kwargs)
            # Execute the function directly
            result = self._execute_function(action, instance, **kwargs)
            # Handle coroutines if any (Flask 2.0+ supports async, but direct execute is sync)
            if inspect.iscoroutine(result):
                # We can't await it here in sync execute
                logger.warning("Executing async action in sync Flask execute wrapper. Result may be a coroutine.")
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            return ActionResult(
                success=True,
                data=result,
                duration=duration,
                metadata={
                    "engine": "flask",
                    "http_method": getattr(action, 'http_method', 'POST'),
                    "endpoint_path": getattr(action, 'endpoint_path', f"/{action.api_name}")
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self._update_metrics(duration, False)
            logger.error(f"Flask engine execution failed: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={
                    "engine": "flask",
                    "error_type": type(e).__name__
                }
            )

    def _create_route_handler(self, 
                              action: Any, 
                              func: Callable, 
                              sig: inspect.Signature,
                              path_param_names: set[str],
                              method: str,
                              path: str,
                              RequestModel: Optional[Any] = None) -> Callable:
        """
        Factory to create the actual route handler function.
        Uses a unified async handler to support Flask 2.0+ and ensure non-blocking execution.
        """
        is_bound_method = hasattr(action, '__self__') and hasattr(action, '__func__')
        bound_instance = action.__self__ if is_bound_method else None
        def extract_arguments(**view_args):
            """Helper to extract and validate arguments from request."""
            # 1. Start with path params passed by Flask
            execution_kwargs = view_args.copy()
            # 2. Body Params
            body_data = {}
            if method.upper() in ("POST", "PUT", "PATCH"):
                if request.is_json:
                    body_data = request.get_json(silent=True) or {}
                else:
                    body_data = request.form.to_dict()
            # 3. Query Params
            query_data = request.args.to_dict()
            # 4. Bind arguments based on signature
            # We iterate over signature parameters to find where to get values
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                # If it's a path param, it's already in execution_kwargs from view_args
                if param_name in path_param_names:
                    continue
                # Check for Pydantic Body Model 'request_body'
                if param_name == 'request_body' and RequestModel:
                    try:
                        # Validate body data against model
                        model_instance = RequestModel(**body_data)
                        execution_kwargs['request_body'] = model_instance
                    except Exception as e:
                        # If validation fails, we might want to fail early
                        # Or pass raw data if model is optional? 
                        # For now, let's treat it as a hard failure if Pydantic is used
                        if isinstance(e, ValidationError):
                            raise ValueError(f"Invalid request body: {e}")
                        raise
                    continue
                # Try to find parameter in Body (if field-based), then Query
                value = None
                found = False
                # If we are using individual fields instead of request_body model
                if not RequestModel and method.upper() in ("POST", "PUT", "PATCH"):
                    if param_name in body_data:
                        value = body_data[param_name]
                        found = True
                # Fallback to Query params
                if not found and param_name in query_data:
                    value = query_data[param_name]
                    found = True
                if found:
                    # Simple type casting if annotation is basic type
                    # This is very basic; robust casting would need more logic
                    ann = param.annotation
                    if ann in (int, float, bool, str) and isinstance(value, str):
                        try:
                            if ann is bool:
                                value = value.lower() in ('true', '1', 'yes')
                            else:
                                value = ann(value)
                        except (ValueError, TypeError):
                            pass  # Keep original value if cast fails
                    execution_kwargs[param_name] = value
            return execution_kwargs
        async def unified_handler(**kwargs):
            start_time = time.time()
            try:
                execution_kwargs = extract_arguments(**kwargs)
                # Execute using base class async helper
                # Handles async actions -> awaited
                # Handles sync actions -> run in threadpool (non-blocking!)
                result = await self._execute_function_async(
                    action, 
                    bound_instance, 
                    **execution_kwargs
                )
                self._update_metrics(time.time() - start_time, True)
                # Convert result to response if it's not already
                # If result is Pydantic model, dump it
                if hasattr(result, 'model_dump'):
                    return jsonify(result.model_dump())
                elif isinstance(result, (dict, list)):
                    return jsonify(result)
                else:
                    return make_response(str(result))
            except Exception as e:
                self._update_metrics(time.time() - start_time, False)
                logger.error(f"Flask execution failed: {e}")
                status_code = 400 if isinstance(e, (ValueError, TypeError)) else 500
                return make_response(jsonify({"error": str(e)}), status_code)
        return unified_handler

    def register_action(self, action: Any, app: Any, path: str = None, method: str = "POST") -> bool:
        """
        Register an action as a Flask endpoint.
        """
        try:
            self._app = app
            endpoint_path = path or f"/{action.api_name}"
            # Identify function
            if hasattr(action, '__self__') and hasattr(action, '__func__'):
                func = action.__func__
            else:
                func = getattr(action, 'func', None)
            if not func:
                logger.error(f"Action {action.api_name} has no function to register")
                return False
            # --- 1. Analyze Signature ---
            sig = inspect.signature(func)
            type_hints = self._resolve_type_hints(func)
            # Path params in Flask are like <name> or <int:name>
            # We assume user provides path in Flask format
            # Regex to find <name> or <type:name>
            path_param_names = set(re.findall(r'<(?:\w+:)?(\w+)>', endpoint_path))
            # Parameter categorization for Pydantic model
            body_params_fields = {}
            is_body_method = method.upper() in ("POST", "PUT", "PATCH")
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls') or param_name in path_param_names:
                    continue
                annotation = type_hints.get(param_name, param.annotation)
                if annotation == inspect.Parameter.empty:
                    annotation = Any
                # Check for Pydantic compatibility
                if not self._is_pydantic_compatible(annotation):
                    continue
                # If method allows body, we try to put it in a Pydantic model
                if is_body_method:
                    # Check if it has default
                    if param.default != inspect.Parameter.empty:
                        # For Pydantic Field
                        default_val = param.default
                        if isinstance(default_val, Field):
                            field_def = (annotation, default_val)
                        else:
                            field_def = (annotation, Field(default=default_val))
                    else:
                        field_def = (annotation, ...)
                    body_params_fields[param_name] = field_def
            # --- 2. Create Input Model ---
            RequestModel = None
            if is_body_method and body_params_fields:
                func_module = getattr(func, '__module__', None)
                RequestModel = self._create_input_model(action.api_name, body_params_fields, func_module)
            # --- 3. Create Handler ---
            handler = self._create_route_handler(
                action, func, sig, path_param_names, method, endpoint_path, RequestModel
            )
            # Set name for Flask (must be unique)
            handler.__name__ = f"handler_{action.api_name}"
            # --- 4. Register with Flask ---
            app.add_url_rule(
                endpoint_path,
                endpoint=action.api_name,
                view_func=handler,
                methods=[method.upper()]
            )
            self._registered_routes[action.api_name] = {
                "path": endpoint_path,
                "method": method
            }
            logger.info(f"Registered action {action.api_name} as Flask endpoint: {method} {endpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to register action {getattr(action, 'api_name', 'unknown')} as Flask endpoint: {e}", exc_info=True)
            return False

    def setup(self, config: dict[str, Any]) -> bool:
        """Setup Flask engine."""
        try:
            if "app" in config:
                self._app = config["app"]
            elif "create_app" in config:
                self._app = config["create_app"]()
            logger.debug("Flask action engine setup completed")
            return True
        except Exception as e:
            logger.error(f"Failed to setup Flask engine: {e}")
            return False
