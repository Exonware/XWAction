#!/usr/bin/env python3
"""
🎯 Monitoring Action Handler Implementation
Performance monitoring and metrics handler for xAction.
"""

import time
from typing import Any, Dict, Optional, Set

from .abc import aActionHandlerBase, ActionHandlerPhase
from ..abc import ActionContext
from src.xlib.xsystem import get_logger

logger = get_logger(__name__)


class MonitoringActionHandler(aActionHandlerBase):
    """
    🌟 Monitoring Action Handler
    
    Handles performance monitoring, metrics collection, and observability.
    Provides comprehensive monitoring for action execution.
    """
    
    def __init__(self):
        super().__init__(
            name="monitoring",
            priority=50,  # Medium priority - monitoring should run after core handlers
            async_enabled=True
        )
        self._metrics_collector = None
        self._performance_data = []
        self._alert_thresholds = {}
    
    @property
    def supported_phases(self) -> Set[ActionHandlerPhase]:
        """Monitoring handler supports all phases."""
        return {ActionHandlerPhase.BEFORE, ActionHandlerPhase.AFTER, ActionHandlerPhase.ERROR}
    
    def before_execution(self, action: 'xAction', context: ActionContext, **kwargs) -> bool:
        """
        Start monitoring before execution.
        
        Args:
            action: The action being executed
            context: Execution context
            **kwargs: Action parameters
            
        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            start_time = time.time()
            
            # Record execution start
            execution_record = {
                "action_name": action.api_name,
                "trace_id": context.trace_id,
                "actor": context.actor,
                "source": context.source,
                "start_time": start_time,
                "parameters": kwargs
            }
            
            # Store execution record
            self._performance_data.append(execution_record)
            
            # Send to metrics collector
            if self._metrics_collector:
                self._metrics_collector.record_execution_start(execution_record)
            
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            
            logger.debug(f"Monitoring started for action {action.api_name}")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring handler error in before_execution: {e}")
            return False
    
    def after_execution(self, action: 'xAction', context: ActionContext, result: Any, **kwargs) -> bool:
        """
        Record monitoring data after execution.
        
        Args:
            action: The action that was executed
            context: Execution context
            result: The execution result
            **kwargs: Additional parameters
            
        Returns:
            True if monitoring completed successfully, False otherwise
        """
        try:
            start_time = time.time()
            
            # Find execution record
            execution_record = self._find_execution_record(context.trace_id)
            if not execution_record:
                logger.warning(f"No execution record found for trace_id {context.trace_id}")
                return False
            
            # Update execution record
            end_time = time.time()
            duration = end_time - execution_record["start_time"]
            
            execution_record.update({
                "end_time": end_time,
                "duration": duration,
                "success": True,
                "result_type": type(result).__name__,
                "result_size": len(str(result)) if result else 0
            })
            
            # Check performance thresholds
            self._check_performance_thresholds(action, duration)
            
            # Send to metrics collector
            if self._metrics_collector:
                self._metrics_collector.record_execution_complete(execution_record)
            
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            
            logger.debug(f"Monitoring completed for action {action.api_name} (duration: {duration:.3f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring handler error in after_execution: {e}")
            return False
    
    def on_error(self, action: 'xAction', context: ActionContext, error: Exception, **kwargs) -> bool:
        """
        Record error monitoring data.
        
        Args:
            action: The action that failed
            context: Execution context
            error: The exception that occurred
            **kwargs: Additional parameters
            
        Returns:
            True if error monitoring completed, False otherwise
        """
        try:
            start_time = time.time()
            
            # Find execution record
            execution_record = self._find_execution_record(context.trace_id)
            if not execution_record:
                logger.warning(f"No execution record found for trace_id {context.trace_id}")
                return False
            
            # Update execution record with error
            end_time = time.time()
            duration = end_time - execution_record["start_time"]
            
            execution_record.update({
                "end_time": end_time,
                "duration": duration,
                "success": False,
                "error_type": type(error).__name__,
                "error_message": str(error)
            })
            
            # Send error to metrics collector
            if self._metrics_collector:
                self._metrics_collector.record_execution_error(execution_record)
            
            # Check error thresholds
            self._check_error_thresholds(action, error)
            
            duration = time.time() - start_time
            self._update_metrics(duration, True)
            
            logger.debug(f"Error monitoring completed for action {action.api_name}")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring handler error in on_error: {e}")
            return False
    
    def _find_execution_record(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Find execution record by trace ID."""
        for record in self._performance_data:
            if record.get("trace_id") == trace_id:
                return record
        return None
    
    def _check_performance_thresholds(self, action: 'xAction', duration: float):
        """Check if execution duration exceeds thresholds."""
        try:
            # Get performance thresholds
            thresholds = self._alert_thresholds.get(action.api_name, {})
            warning_threshold = thresholds.get("warning", 5.0)  # 5 seconds
            critical_threshold = thresholds.get("critical", 10.0)  # 10 seconds
            
            if duration > critical_threshold:
                logger.error(f"Critical performance threshold exceeded for {action.api_name}: {duration:.3f}s")
                self._send_alert(action, "critical", duration)
            elif duration > warning_threshold:
                logger.warning(f"Warning performance threshold exceeded for {action.api_name}: {duration:.3f}s")
                self._send_alert(action, "warning", duration)
                
        except Exception as e:
            logger.error(f"Performance threshold check failed: {e}")
    
    def _check_error_thresholds(self, action: 'xAction', error: Exception):
        """Check if error rate exceeds thresholds."""
        try:
            # Get error thresholds
            thresholds = self._alert_thresholds.get(action.api_name, {})
            error_threshold = thresholds.get("error_rate", 0.1)  # 10% error rate
            
            # Calculate error rate for this action
            action_records = [r for r in self._performance_data if r.get("action_name") == action.api_name]
            if len(action_records) > 10:  # Only check if we have enough data
                recent_records = action_records[-10:]  # Last 10 executions
                error_count = sum(1 for r in recent_records if not r.get("success", True))
                error_rate = error_count / len(recent_records)
                
                if error_rate > error_threshold:
                    logger.error(f"Error rate threshold exceeded for {action.api_name}: {error_rate:.2%}")
                    self._send_alert(action, "error_rate", error_rate)
                    
        except Exception as e:
            logger.error(f"Error threshold check failed: {e}")
    
    def _send_alert(self, action: 'xAction', alert_type: str, value: Any):
        """Send alert to monitoring system."""
        try:
            alert = {
                "timestamp": time.time(),
                "action_name": action.api_name,
                "alert_type": alert_type,
                "value": value,
                "severity": "high" if alert_type in ["critical", "error_rate"] else "medium"
            }
            
            # Send to metrics collector
            if self._metrics_collector:
                self._metrics_collector.send_alert(alert)
            
            logger.warning(f"Alert sent: {alert}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def setup(self, config: Dict[str, Any]) -> bool:
        """Setup monitoring handler."""
        try:
            # Initialize metrics collector if available
            try:
                from src.xlib.xsystem.monitoring import MetricsCollector
                self._metrics_collector = MetricsCollector()
                logger.debug("Metrics collector initialized for monitoring handler")
            except ImportError:
                logger.debug("Metrics collector not available, using local monitoring")
            
            # Set alert thresholds
            self._alert_thresholds = config.get("alert_thresholds", {})
            
            # Clear performance data
            self._performance_data.clear()
            
            logger.debug("Monitoring action handler setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring handler: {e}")
            return False
    
    def teardown(self) -> bool:
        """Teardown monitoring handler."""
        self._metrics_collector = None
        self._performance_data.clear()
        self._alert_thresholds.clear()
        logger.debug("Monitoring action handler teardown completed")
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring handler metrics."""
        metrics = super().get_metrics()
        
        # Calculate performance statistics
        if self._performance_data:
            durations = [r.get("duration", 0) for r in self._performance_data if r.get("duration")]
            success_count = sum(1 for r in self._performance_data if r.get("success", True))
            error_count = len(self._performance_data) - success_count
            
            metrics.update({
                "handler_type": "monitoring",
                "total_executions": len(self._performance_data),
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": success_count / len(self._performance_data) if self._performance_data else 0.0,
                "average_duration": sum(durations) / len(durations) if durations else 0.0,
                "max_duration": max(durations) if durations else 0.0,
                "min_duration": min(durations) if durations else 0.0,
                "metrics_collector_available": self._metrics_collector is not None
            })
        else:
            metrics.update({
                "handler_type": "monitoring",
                "total_executions": 0,
                "success_count": 0,
                "error_count": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "max_duration": 0.0,
                "min_duration": 0.0,
                "metrics_collector_available": self._metrics_collector is not None
            })
        
        return metrics
