#!/usr/bin/env python3
"""
🎯 Validation Action Handler Implementation
Input/output validation handler for xAction.
"""

import time
import hashlib
from typing import Any, Dict, Optional, Set
from functools import lru_cache

from .abc import aActionHandlerBase, ActionHandlerPhase
from ..abc import ActionContext
from src.xlib.xwsystem import get_logger

logger = get_logger(__name__)


class ValidationActionHandler(aActionHandlerBase):
    """
    🌟 Validation Action Handler
    
    Handles input/output validation for actions using xSchema.
    Provides caching and async support for performance.
    """
    
    def __init__(self):
        super().__init__(
            name="validation",
            priority=100,  # High priority - validation should run first
            async_enabled=True
        )
        self._validation_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps = {}
    
    @property
    def supported_phases(self) -> Set[ActionHandlerPhase]:
        """Validation handler supports before and after phases."""
        return {ActionHandlerPhase.BEFORE, ActionHandlerPhase.AFTER}
    
    def before_execution(self, action: 'xAction', context: ActionContext, **kwargs) -> bool:
        """
        Validate input parameters before execution.
        
        Args:
            action: The action being executed
            context: Execution context
            **kwargs: Action parameters
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            start_time = time.time()
            
            # Check if we have input validation schemas
            if not hasattr(action, 'in_types') or not action.in_types:
                logger.debug(f"No input validation schemas for action {action.api_name}")
                return True
            
            # Validate input parameters
            validation_result = self._validate_inputs(action, kwargs)
            
            duration = time.time() - start_time
            self._update_metrics(duration, validation_result)
            
            if not validation_result:
                logger.warning(f"Input validation failed for action {action.api_name}")
                return False
            
            logger.debug(f"Input validation passed for action {action.api_name}")
            return True
            
        except Exception as e:
            logger.error(f"Validation handler error in before_execution: {e}")
            return False
    
    def after_execution(self, action: 'xAction', context: ActionContext, result: Any, **kwargs) -> bool:
        """
        Validate output result after execution.
        
        Args:
            action: The action that was executed
            context: Execution context
            result: The execution result
            **kwargs: Additional parameters
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            start_time = time.time()
            
            # Check if we have output validation schemas
            if not hasattr(action, 'out_types') or not action.out_types:
                logger.debug(f"No output validation schemas for action {action.api_name}")
                return True
            
            # Validate output result
            validation_result = self._validate_outputs(action, result)
            
            duration = time.time() - start_time
            self._update_metrics(duration, validation_result)
            
            if not validation_result:
                logger.warning(f"Output validation failed for action {action.api_name}")
                return False
            
            logger.debug(f"Output validation passed for action {action.api_name}")
            return True
            
        except Exception as e:
            logger.error(f"Validation handler error in after_execution: {e}")
            return False
    
    def on_error(self, action: 'xAction', context: ActionContext, error: Exception, **kwargs) -> bool:
        """
        Handle validation errors.
        
        Args:
            action: The action that failed
            context: Execution context
            error: The exception that occurred
            **kwargs: Additional parameters
            
        Returns:
            True if error was handled, False otherwise
        """
        logger.error(f"Validation error for action {action.api_name}: {error}")
        return True  # Always handle validation errors gracefully
    
    def _validate_inputs(self, action: 'xAction', inputs: Dict[str, Any]) -> bool:
        """
        Validate input parameters using xSchema.
        
        Args:
            action: The action to validate
            inputs: Input parameters
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Generate cache key
            cache_key = self._get_validation_cache_key(action, "input", inputs)
            
            # Check cache
            if cache_key in self._validation_cache:
                cached_result = self._validation_cache[cache_key]
                if self._is_cache_valid(cache_key):
                    self._metrics["cache_hits"] += 1
                    return cached_result
            
            # Perform validation
            validation_result = self._perform_input_validation(action, inputs)
            
            # Cache result
            self._validation_cache[cache_key] = validation_result
            self._cache_timestamps[cache_key] = time.time()
            self._metrics["cache_misses"] += 1
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False
    
    def _validate_outputs(self, action: 'xAction', output: Any) -> bool:
        """
        Validate output result using xSchema.
        
        Args:
            action: The action to validate
            output: Output result
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Generate cache key
            cache_key = self._get_validation_cache_key(action, "output", output)
            
            # Check cache
            if cache_key in self._validation_cache:
                cached_result = self._validation_cache[cache_key]
                if self._is_cache_valid(cache_key):
                    self._metrics["cache_hits"] += 1
                    return cached_result
            
            # Perform validation
            validation_result = self._perform_output_validation(action, output)
            
            # Cache result
            self._validation_cache[cache_key] = validation_result
            self._cache_timestamps[cache_key] = time.time()
            self._metrics["cache_misses"] += 1
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Output validation error: {e}")
            return False
    
    def _perform_input_validation(self, action: 'xAction', inputs: Dict[str, Any]) -> bool:
        """Perform actual input validation using xSchema."""
        try:
            # Import xSchema here to avoid circular imports
            from src.xlib.xdata import xSchema
            
            # Get input schemas
            in_types = action.in_types
            
            # Validate each input parameter
            for param_name, param_value in inputs.items():
                if param_name in in_types:
                    schema = in_types[param_name]
                    if isinstance(schema, xSchema):
                        # Use xSchema validation
                        if not schema.validate(param_value):
                            logger.warning(f"Input validation failed for parameter {param_name}")
                            return False
                    else:
                        # Basic type validation
                        if not isinstance(param_value, schema):
                            logger.warning(f"Type validation failed for parameter {param_name}")
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False
    
    def _perform_output_validation(self, action: 'xAction', output: Any) -> bool:
        """Perform actual output validation using xSchema."""
        try:
            # Import xSchema here to avoid circular imports
            from src.xlib.xdata import xSchema
            
            # Get output schemas
            out_types = action.out_types
            
            # Validate output
            for schema_name, schema in out_types.items():
                if isinstance(schema, xSchema):
                    # Use xSchema validation
                    if not schema.validate(output):
                        logger.warning(f"Output validation failed for schema {schema_name}")
                        return False
                else:
                    # Basic type validation
                    if not isinstance(output, schema):
                        logger.warning(f"Output type validation failed for schema {schema_name}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Output validation error: {e}")
            return False
    
    def _get_validation_cache_key(self, action: 'xAction', validation_type: str, data: Any) -> str:
        """Generate cache key for validation results."""
        # Create a hash of the action and data
        key_data = {
            "action_name": action.api_name,
            "validation_type": validation_type,
            "data_hash": hashlib.md5(str(data).encode()).hexdigest()
        }
        
        return hashlib.md5(str(key_data).encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached validation result is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        
        timestamp = self._cache_timestamps[cache_key]
        return (time.time() - timestamp) < self._cache_ttl
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup validation handler."""
        try:
            # Configure cache TTL
            self._cache_ttl = config.get("cache_ttl", 300)
            
            # Clear existing cache
            self._validation_cache.clear()
            self._cache_timestamps.clear()
            
            logger.debug("Validation action handler setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup validation handler: {e}")
            return False
    
    def teardown(self) -> bool:
        """Teardown validation handler."""
        self._validation_cache.clear()
        self._cache_timestamps.clear()
        logger.debug("Validation action handler teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation handler metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "handler_type": "validation",
            "cache_size": len(self._validation_cache),
            "cache_ttl": self._cache_ttl,
            "cache_hit_rate": (
                metrics["cache_hits"] / (metrics["cache_hits"] + metrics["cache_misses"])
                if (metrics["cache_hits"] + metrics["cache_misses"]) > 0 else 0.0
            )
        })
        return metrics
