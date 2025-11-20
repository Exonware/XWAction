#!/usr/bin/env python3
"""
🎯 FastAPI Action Engine Implementation
Web API execution engine for xAction.
"""

import time
import inspect
from typing import Any, Dict, Optional, List
from functools import wraps

from .abc import aActionEngineBase, ActionEngineType
from ..abc import ActionContext, ActionResult
from ..core.profiles import ActionProfile
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class FastAPIActionEngine(aActionEngineBase):
    """
    🌟 FastAPI Action Engine
    
    Executes actions as FastAPI endpoints with automatic OpenAPI generation.
    This engine is ideal for web API endpoints.
    """
    
    def __init__(self):
        super().__init__(
            name="fastapi",
            engine_type=ActionEngineType.EXECUTION,
            priority=80  # High priority for API endpoints
        )
        self._app = None
        self._registered_routes = {}
    
    def can_execute(self, action_profile: ActionProfile, **kwargs) -> bool:
        """FastAPI engine can execute endpoint and query profiles."""
        return action_profile in [ActionProfile.ENDPOINT, ActionProfile.QUERY, ActionProfile.COMMAND]
    
    def execute(self, action: 'xAction', context: ActionContext, 
                instance: Any, **kwargs) -> ActionResult:
        """
        Execute action as FastAPI endpoint.
        
        Args:
            action: The action to execute
            context: Execution context
            instance: The entity instance (self in decorated method)
            **kwargs: Action parameters
            
        Returns:
            ActionResult with execution results
        """
        start_time = time.time()
        
        try:
            # For FastAPI, we typically don't execute directly
            # Instead, we register the action as an endpoint
            if not self._app:
                logger.warning("FastAPI app not initialized, falling back to native execution")
                return self._fallback_execution(action, context, instance, **kwargs)
            
            # Execute the function (simulating HTTP request)
            result = self._execute_function(action, instance, **kwargs)
            
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            
            return ActionResult(
                success=True,
                data=result,
                duration=duration,
                metadata={
                    "engine": "fastapi",
                    "http_method": getattr(action, 'http_method', 'GET'),
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
    
    def _fallback_execution(self, action: 'xAction', context: ActionContext, 
                           instance: Any, **kwargs) -> ActionResult:
        """Fallback to native execution when FastAPI is not available."""
        from .native import NativeActionEngine
        native_engine = NativeActionEngine()
        return native_engine.execute(action, context, instance, **kwargs)
    
    def _execute_function(self, action: 'xAction', instance: Any, **kwargs) -> Any:
        """Execute the action function."""
        func = action.func
        
        # Prepare arguments
        args = []
        if instance is not None:
            args.append(instance)
        
        # Add action parameters
        args.extend(kwargs.values())
        
        # Execute the function
        return func(*args)
    
    def register_endpoint(self, action: 'xAction', app=None):
        """
        Register an action as a FastAPI endpoint.
        
        Args:
            action: The action to register
            app: FastAPI app instance (optional)
        """
        if app:
            self._app = app
        
        if not self._app:
            logger.warning("No FastAPI app provided, cannot register endpoint")
            return
        
        # Generate endpoint configuration
        endpoint_config = self._generate_endpoint_config(action)
        
        # Register the route
        self._register_route(action, endpoint_config)
        
        self._metrics["openapi_generated"] = self._metrics.get("openapi_generated", 0) + 1
        logger.info(f"Registered FastAPI endpoint: {endpoint_config['path']}")
    
    def _generate_endpoint_config(self, action: 'xAction') -> Dict[str, Any]:
        """Generate FastAPI endpoint configuration."""
        # Extract HTTP method from action profile or default to GET
        http_method = "GET"
        if action.profile == ActionProfile.COMMAND:
            http_method = "POST"
        elif action.profile == ActionProfile.ENDPOINT:
            http_method = "POST"  # Default for endpoints
        
        # Generate path
        path = f"/{action.api_name}"
        if hasattr(action, 'endpoint_path'):
            path = action.endpoint_path
        
        # Generate OpenAPI operation
        operation = action.to_openapi()
        
        return {
            "path": path,
            "method": http_method.lower(),
            "operation": operation,
            "tags": action.tags,
            "summary": action.summary,
            "description": action.description,
            "security": action.security_config
        }
    
    def _register_route(self, action: 'xAction', config: Dict[str, Any]):
        """Register the route with FastAPI."""
        if not self._app:
            return
        
        # Create the endpoint function
        def endpoint_function(**kwargs):
            # Execute the action
            context = ActionContext(
                actor="http_request",
                source="api",
                metadata={"http_method": config["method"], "path": config["path"]}
            )
            
            result = self._execute_function(action, None, **kwargs)
            return result
        
        # Add metadata to the function
        endpoint_function.__name__ = action.api_name
        endpoint_function.__doc__ = action.description
        
        # Register with FastAPI
        method = config["method"]
        path = config["path"]
        
        if method == "get":
            self._app.get(path, **self._get_fastapi_kwargs(config))(endpoint_function)
        elif method == "post":
            self._app.post(path, **self._get_fastapi_kwargs(config))(endpoint_function)
        elif method == "put":
            self._app.put(path, **self._get_fastapi_kwargs(config))(endpoint_function)
        elif method == "delete":
            self._app.delete(path, **self._get_fastapi_kwargs(config))(endpoint_function)
        
        # Store registration info
        self._registered_routes[action.api_name] = config
    
    def _get_fastapi_kwargs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get FastAPI decorator kwargs."""
        kwargs = {}
        
        if config.get("tags"):
            kwargs["tags"] = config["tags"]
        
        if config.get("summary"):
            kwargs["summary"] = config["summary"]
        
        if config.get("description"):
            kwargs["description"] = config["description"]
        
        if config.get("operation"):
            kwargs["operation_id"] = config["operation"].get("operationId")
        
        return kwargs
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup FastAPI engine."""
        try:
            # Try to import FastAPI
            import fastapi
            logger.debug("FastAPI action engine setup completed")
            return True
        except ImportError:
            logger.warning("FastAPI not available, engine will use fallback execution")
            return False
    
    def teardown(self) -> bool:
        """Teardown FastAPI engine."""
        self._app = None
        self._registered_routes.clear()
        logger.debug("FastAPI action engine teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get FastAPI engine metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "engine_type": "fastapi",
            "registered_routes": len(self._registered_routes),
            "openapi_generated": metrics.get("openapi_generated", 0)
        })
        return metrics
