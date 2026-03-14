"""
Action Utilities - Extract and Load XWAction instances.
This module provides utilities for extracting XWAction instances from objects
(class or instance) and loading them onto instances.
Fully reuses ecosystem libraries:
- xwsystem: For logging (get_logger)
"""

from typing import Any, TYPE_CHECKING
import inspect
from functools import wraps
from collections.abc import Callable
if TYPE_CHECKING:
    from .facade import XWAction
from exonware.xwsystem import get_logger
from .context import ActionContext
logger = get_logger(__name__)


def extract_actions(obj: Any) -> list[Any]:  # Returns list[XWAction] but avoids circular import
    """
    Extract all XWAction instances from an object (class or instance).
    Scans for methods/attributes decorated with @XWAction by checking for
    the 'xwaction' attribute that contains an XWAction instance.
    This function handles multiple patterns:
    - Pattern 1: Methods with 'xwaction' attribute (wrapper pattern - current implementation)
    - Pattern 2: Direct XWAction instances
    Args:
        obj: Object (class or instance) to scan for actions
    Returns:
        List of XWAction instances found on the object
    Example:
        >>> class MyClass:
        ...     @XWAction()
        ...     def my_action(self, x: int) -> int:
        ...         return x * 2
        ...
        >>> actions = extract_actions(MyClass)
        >>> len(actions)
        1
        >>> actions[0].api_name
        'my_action'
    """
    # Import here to avoid circular dependency
    from .facade import XWAction
    actions: list[Any] = []
    # Determine what to scan (class dict or instance dict)
    if inspect.isclass(obj):
        namespace = obj.__dict__
    else:
        # For instances, check both instance and class
        namespace = {}
        # Add instance attributes that are callable or have xwaction
        for k, v in vars(obj).items():
            if callable(v) or hasattr(v, 'xwaction'):
                namespace[k] = v
        # Add class attributes
        namespace.update({k: v for k, v in obj.__class__.__dict__.items()})
    for name, attr in namespace.items():
        # Skip private attributes (unless they have xwaction)
        if name.startswith('_') and not hasattr(attr, 'xwaction'):
            continue
        # Pattern 1: Check for xwaction attribute (wrapper pattern - current implementation)
        if hasattr(attr, 'xwaction'):
            action_obj = getattr(attr, 'xwaction')
            if isinstance(action_obj, XWAction):
                actions.append(action_obj)
                logger.debug(f"Extracted action '{name}' from {obj.__name__ if inspect.isclass(obj) else obj.__class__.__name__}")
        # Pattern 2: Check if the attribute itself is an XWAction (direct pattern)
        elif isinstance(attr, XWAction):
            actions.append(attr)
            logger.debug(f"Extracted direct action '{name}' from {obj.__name__ if inspect.isclass(obj) else obj.__class__.__name__}")
    return actions


def load_actions(obj: Any, actions: list[Any]) -> bool:  # Accepts list[XWAction] but avoids circular import
    """
    Load/attach XWAction instances to an object instance as callable methods.
    Creates wrapper methods for each action that can be called directly.
    The wrappers will have the 'xwaction' attribute set so extract_actions()
    can find them again.
    Args:
        obj: Object instance to attach actions to (must be an instance, not a class)
        actions: List of XWAction instances to attach
    Returns:
        True if all actions were successfully attached, False otherwise
    Raises:
        ValueError: If obj is a class instead of an instance
    Example:
        >>> class MyClass:
        ...     pass
        ...
        >>> instance = MyClass()
        >>> action = XWAction(api_name="test_action", func=lambda self, x: x * 2)
        >>> load_actions(instance, [action])
        True
        >>> hasattr(instance, 'test_action')
        True
        >>> instance.test_action(x=4)
        8
    """
    # Import here to avoid circular dependency
    from .facade import XWAction
    if inspect.isclass(obj):
        raise ValueError("Cannot load actions onto a class. Use an instance instead.")
    if not actions:
        logger.warning(f"No actions provided to load onto {obj}")
        return True  # Empty list is considered success
    success_count = 0
    for action in actions:
        if not isinstance(action, XWAction):
            logger.warning(f"Skipping non-XWAction object: {type(action)}")
            continue
        try:
            # Get the function name from the action
            func_name = action.api_name or (action.func.__name__ if hasattr(action, 'func') and action.func else None)
            if not func_name:
                logger.warning(f"Skipping action with no name: {action}")
                continue
            # Check if action has a function (required for creating wrapper)
            if not hasattr(action, 'func') or not action.func:
                logger.warning(f"Skipping action '{func_name}' with no function")
                continue
            # Check if it's a method (has 'self' parameter)
            sig = inspect.signature(action.func)
            is_method = 'self' in sig.parameters
            param_names = list(sig.parameters.keys())  # Capture for closure
            param_names_no_self = param_names[1:] if is_method else param_names  # Capture for closure
            # Create a wrapper function that can be called on the instance
            # We need to capture the action in a closure
            action_instance = action  # Capture for closure
            @wraps(action.func)
            def wrapper(*args, **kwargs):
                # Create context for direct call
                context = ActionContext(actor="direct_call", source="loaded_action")
                # For methods, the instance will be in args[0] (self)
                # For functions, use the object instance
                if is_method and args:
                    instance = args[0]
                    # Remove 'self' from args for execution
                    exec_args = args[1:] if len(args) > 1 else ()
                else:
                    instance = obj
                    exec_args = args
                # Execute the action - convert positional args to kwargs if needed
                # The action executor expects kwargs
                if exec_args:
                    # Match args to parameter names
                    kwargs_from_args = {param_names_no_self[i]: arg for i, arg in enumerate(exec_args) if i < len(param_names_no_self)}
                    kwargs.update(kwargs_from_args)
                return action_instance.execute(context, instance, **kwargs)
            # Attach action metadata to wrapper (same pattern as _decorate in facade.py)
            wrapper.xwaction = action_instance
            wrapper._is_action = True
            wrapper.api_name = action_instance.api_name
            if hasattr(action_instance, 'roles'):
                wrapper.roles = action_instance.roles
            if hasattr(action_instance, 'engines'):
                wrapper.engines = action_instance.engines
            if hasattr(action_instance, 'to_native'):
                wrapper.to_native = action_instance.to_native
            if hasattr(action_instance, '_in_types'):
                wrapper.in_types = action_instance._in_types
            # Bind method to instance if it's a method
            if is_method:
                # It's a method, bind it to the instance
                bound_method = wrapper.__get__(obj, obj.__class__)
                setattr(obj, func_name, bound_method)
            else:
                # It's a function, attach it directly
                setattr(obj, func_name, wrapper)
            logger.debug(f"Loaded action '{func_name}' onto {obj.__class__.__name__} instance")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to load action '{action.api_name if hasattr(action, 'api_name') and action.api_name else 'unknown'}': {e}", exc_info=True)
            continue
    all_success = success_count == len(actions)
    if not all_success:
        logger.warning(f"Only loaded {success_count}/{len(actions)} actions onto {obj.__class__.__name__}")
    return all_success
