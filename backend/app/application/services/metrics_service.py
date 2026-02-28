"""
System Metrics Collection Service - Phase 5
Collects and reports system performance and health metrics
"""
import logging
import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

from app.application.services.event_service import EventService
from app.domain.entities.event import EventType, EventSeverity

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    load_average: List[float] = field(default_factory=list)
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    python_memory_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_percent": self.memory_usage_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_total_mb": self.memory_total_mb,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_used_gb": self.disk_used_gb,
            "disk_total_gb": self.disk_total_gb,
            "load_average": self.load_average,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv,
            "process_count": self.process_count,
            "python_memory_mb": self.python_memory_mb
        }


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    active_downloads: int = 0
    pending_episodes: int = 0
    failed_episodes: int = 0
    total_channels: int = 0
    total_episodes: int = 0
    storage_used_gb: float = 0.0
    recent_errors_count: int = 0
    avg_response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "active_downloads": self.active_downloads,
            "pending_episodes": self.pending_episodes,
            "failed_episodes": self.failed_episodes,
            "total_channels": self.total_channels,
            "total_episodes": self.total_episodes,
            "storage_used_gb": self.storage_used_gb,
            "recent_errors_count": self.recent_errors_count,
            "avg_response_time_ms": self.avg_response_time_ms
        }


class MetricsCollectionService:
    """
    Service for collecting and reporting system metrics
    """
    
    def __init__(self, event_service: EventService):
        self.event_service = event_service
        self._last_network_stats = None
        self._collection_interval = 60  # seconds
        self._is_collecting = False
        self._collection_task = None
    
    # System Metrics Collection
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
            metrics = SystemMetrics()
            
            # CPU metrics
            metrics.cpu_usage_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.memory_usage_percent = memory.percent
            metrics.memory_used_mb = memory.used / (1024 * 1024)
            metrics.memory_total_mb = memory.total / (1024 * 1024)
            
            # Disk metrics (root partition)
            disk = psutil.disk_usage('/')
            metrics.disk_usage_percent = (disk.used / disk.total) * 100
            metrics.disk_used_gb = disk.used / (1024 * 1024 * 1024)
            metrics.disk_total_gb = disk.total / (1024 * 1024 * 1024)
            
            # Load average (Unix-like systems)
            try:
                metrics.load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                metrics.load_average = []
            
            # Network metrics
            network = psutil.net_io_counters()
            metrics.network_bytes_sent = network.bytes_sent
            metrics.network_bytes_recv = network.bytes_recv
            
            # Process metrics
            metrics.process_count = len(psutil.pids())
            
            # Current Python process memory
            process = psutil.Process()
            metrics.python_memory_mb = process.memory_info().rss / (1024 * 1024)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics()  # Return empty metrics on error
    
    async def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        try:
            metrics = ApplicationMetrics()
            
            # Get recent error count
            error_events = await self.event_service.get_error_events(hours=1)
            metrics.recent_errors_count = len(error_events)
            
            # Get event statistics for more insights
            event_stats = await self.event_service.get_event_statistics(hours=24)
            
            # Calculate average response time from performance events
            perf_events = await self.event_service.get_performance_metrics(hours=1)
            if perf_events:
                total_duration = sum(event.duration_ms for event in perf_events if event.duration_ms)
                metrics.avg_response_time_ms = total_duration / len(perf_events) if perf_events else 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return ApplicationMetrics()  # Return empty metrics on error
    
    async def collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """Collect both system and application metrics"""
        system_metrics = self.collect_system_metrics()
        app_metrics = await self.collect_application_metrics()
        
        return {
            "system": system_metrics.to_dict(),
            "application": app_metrics.to_dict(),
            "collection_timestamp": datetime.utcnow().isoformat()
        }
    
    # Health Checks
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        metrics = self.collect_system_metrics()
        health_status = "healthy"
        issues = []
        
        # CPU health check
        if metrics.cpu_usage_percent > 90:
            health_status = "critical"
            issues.append(f"High CPU usage: {metrics.cpu_usage_percent:.1f}%")
        elif metrics.cpu_usage_percent > 70:
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"Elevated CPU usage: {metrics.cpu_usage_percent:.1f}%")
        
        # Memory health check
        if metrics.memory_usage_percent > 95:
            health_status = "critical"
            issues.append(f"Critical memory usage: {metrics.memory_usage_percent:.1f}%")
        elif metrics.memory_usage_percent > 80:
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"High memory usage: {metrics.memory_usage_percent:.1f}%")
        
        # Disk health check
        if metrics.disk_usage_percent > 95:
            health_status = "critical"
            issues.append(f"Critical disk usage: {metrics.disk_usage_percent:.1f}%")
        elif metrics.disk_usage_percent > 85:
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
        
        # Python process memory check
        if metrics.python_memory_mb > 1000:  # 1GB
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"High Python memory usage: {metrics.python_memory_mb:.1f}MB")
        
        return {
            "health_status": health_status,
            "issues": issues,
            "metrics": metrics.to_dict(),
            "check_timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_application_health(self) -> Dict[str, Any]:
        """Check application-specific health metrics"""
        app_metrics = await self.collect_application_metrics()
        system_health = await self.event_service.get_system_health_summary(hours=1)
        
        health_status = "healthy"
        issues = []
        
        # Error rate check
        error_rate = system_health.get("error_rate_percentage", 0)
        if error_rate > 20:
            health_status = "critical"
            issues.append(f"High error rate: {error_rate:.1f}%")
        elif error_rate > 10:
            health_status = "warning"
            issues.append(f"Elevated error rate: {error_rate:.1f}%")
        
        # Response time check
        if app_metrics.avg_response_time_ms > 5000:  # 5 seconds
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"Slow response time: {app_metrics.avg_response_time_ms:.0f}ms")
        
        return {
            "health_status": health_status,
            "issues": issues,
            "metrics": app_metrics.to_dict(),
            "event_summary": system_health,
            "check_timestamp": datetime.utcnow().isoformat()
        }
    
    # Alerting
    
    async def check_and_alert_on_thresholds(self) -> List[Dict[str, Any]]:
        """Check metrics against thresholds and create alert events"""
        alerts_created = []
        
        try:
            # System health check
            system_health = await self.check_system_health()
            if system_health["health_status"] != "healthy":
                alert_event = await self.event_service.log_system_event(
                    channel_id=0,  # System-wide
                    action="system_health_alert",
                    message=f"System health status: {system_health['health_status']}",
                    severity=self._get_severity_for_status(system_health["health_status"]),
                    details=system_health
                )
                alerts_created.append({
                    "type": "system_health",
                    "status": system_health["health_status"],
                    "event_id": alert_event.id
                })
            
            # Application health check
            app_health = await self.check_application_health()
            if app_health["health_status"] != "healthy":
                alert_event = await self.event_service.log_system_event(
                    channel_id=0,  # System-wide
                    action="application_health_alert",
                    message=f"Application health status: {app_health['health_status']}",
                    severity=self._get_severity_for_status(app_health["health_status"]),
                    details=app_health
                )
                alerts_created.append({
                    "type": "application_health",
                    "status": app_health["health_status"],
                    "event_id": alert_event.id
                })
        
        except Exception as e:
            logger.error(f"Failed to check thresholds and create alerts: {e}")
        
        return alerts_created
    
    def _get_severity_for_status(self, status: str) -> EventSeverity:
        """Convert health status to event severity"""
        status_mapping = {
            "healthy": EventSeverity.INFO,
            "warning": EventSeverity.WARNING,
            "critical": EventSeverity.CRITICAL
        }
        return status_mapping.get(status, EventSeverity.INFO)
    
    # Background Collection
    
    async def start_periodic_collection(
        self,
        interval_seconds: int = 60,
        enable_alerting: bool = True
    ):
        """Start periodic metrics collection in the background"""
        if self._is_collecting:
            logger.warning("Metrics collection is already running")
            return
        
        self._collection_interval = interval_seconds
        self._is_collecting = True
        
        # Create background task
        self._collection_task = asyncio.create_task(
            self._periodic_collection_loop(enable_alerting)
        )
        
        logger.info(f"Started periodic metrics collection (interval: {interval_seconds}s)")
        
        # Log the start event
        await self.event_service.log_system_event(
            channel_id=0,
            action="metrics_collection_started",
            message=f"Started periodic metrics collection with {interval_seconds}s interval",
            details={"interval_seconds": interval_seconds, "alerting_enabled": enable_alerting}
        )
    
    async def stop_periodic_collection(self):
        """Stop periodic metrics collection"""
        if not self._is_collecting:
            return
        
        self._is_collecting = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped periodic metrics collection")
        
        # Log the stop event
        await self.event_service.log_system_event(
            channel_id=0,
            action="metrics_collection_stopped",
            message="Stopped periodic metrics collection"
        )
    
    async def _periodic_collection_loop(self, enable_alerting: bool = True):
        """Background task for periodic metrics collection"""
        try:
            while self._is_collecting:
                collection_start = time.time()
                
                try:
                    # Collect comprehensive metrics
                    metrics = await self.collect_comprehensive_metrics()
                    
                    # Log metrics as system event
                    await self.event_service.log_system_event(
                        channel_id=0,
                        action="metrics_collected",
                        message="System and application metrics collected",
                        severity=EventSeverity.DEBUG,  # Use DEBUG to avoid noise
                        details=metrics
                    )
                    
                    # Check for alerts if enabled
                    if enable_alerting:
                        alerts = await self.check_and_alert_on_thresholds()
                        if alerts:
                            logger.info(f"Created {len(alerts)} metric alerts")
                
                except Exception as e:
                    logger.error(f"Error during metrics collection: {e}")
                    # Log the error
                    await self.event_service.log_error_event(
                        channel_id=0,
                        action="metrics_collection_error",
                        error=e
                    )
                
                # Calculate how long to sleep
                collection_duration = time.time() - collection_start
                sleep_duration = max(0, self._collection_interval - collection_duration)
                
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
        
        except asyncio.CancelledError:
            logger.info("Metrics collection loop cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in metrics collection loop: {e}")
    
    # Utility Methods
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current status of metrics collection"""
        return {
            "is_collecting": self._is_collecting,
            "collection_interval": self._collection_interval,
            "has_active_task": self._collection_task is not None and not self._collection_task.done()
        }
    
    async def generate_metrics_report(
        self,
        include_history_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate a comprehensive metrics report"""
        current_metrics = await self.collect_comprehensive_metrics()
        system_health = await self.check_system_health()
        app_health = await self.check_application_health()
        
        # Get historical performance events for trends
        perf_events = await self.event_service.get_performance_metrics(hours=include_history_hours)
        error_events = await self.event_service.get_error_events(hours=include_history_hours)
        
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "current_metrics": current_metrics,
            "system_health": system_health,
            "application_health": app_health,
            "historical_data": {
                "performance_events_count": len(perf_events),
                "error_events_count": len(error_events),
                "avg_performance_duration": (
                    sum(e.duration_ms for e in perf_events if e.duration_ms) / len(perf_events)
                    if perf_events else 0
                )
            },
            "collection_status": self.get_collection_status()
        }