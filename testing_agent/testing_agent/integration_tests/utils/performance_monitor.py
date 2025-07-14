"""
Performance Monitoring for Integration Tests

This module provides utilities for monitoring and measuring performance
during integration tests, including response times, throughput, and resource usage.
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    test_name: str
    start_time: float
    end_time: float
    duration_ms: float
    response_times: List[float]
    throughput_rps: float
    cpu_usage_percent: float
    memory_usage_mb: float
    error_count: int
    success_count: int

@dataclass
class ResourceUsage:
    """Container for system resource usage."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    network_bytes_sent: int
    network_bytes_recv: int

class PerformanceMonitor:
    """Monitor performance metrics during integration tests."""
    
    def __init__(self):
        self.metrics = []
        self.resource_usage = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system resources."""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_resources, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring system resources."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_resources(self, interval: float):
        """Monitor system resources in background thread."""
        while self.monitoring:
            try:
                net_io = psutil.net_io_counters()
                usage = ResourceUsage(
                    timestamp=time.time(),
                    cpu_percent=psutil.cpu_percent(),
                    memory_mb=psutil.virtual_memory().used / (1024 * 1024),
                    network_bytes_sent=net_io.bytes_sent,
                    network_bytes_recv=net_io.bytes_recv
                )
                self.resource_usage.append(usage)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                
    @contextmanager
    def measure_performance(self, test_name: str):
        """Context manager to measure performance of a test."""
        start_time = time.time()
        response_times = []
        error_count = 0
        success_count = 0
        
        # Start resource monitoring if not already started
        if not self.monitoring:
            self.start_monitoring()
        
        initial_resources = self._get_current_resources()
        
        class MetricsCollector:
            def add_response_time(self, duration_ms: float):
                response_times.append(duration_ms)
            
            def increment_success(self):
                nonlocal success_count
                success_count += 1
            
            def increment_error(self):
                nonlocal error_count
                error_count += 1
        
        collector = MetricsCollector()
        
        try:
            yield collector
        finally:
            end_time = time.time()
            final_resources = self._get_current_resources()
            
            # Calculate metrics
            duration_ms = (end_time - start_time) * 1000
            total_requests = success_count + error_count
            throughput_rps = total_requests / (duration_ms / 1000) if duration_ms > 0 else 0
            
            avg_cpu = (initial_resources.cpu_percent + final_resources.cpu_percent) / 2
            avg_memory = (initial_resources.memory_mb + final_resources.memory_mb) / 2
            
            metrics = PerformanceMetrics(
                test_name=test_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                response_times=response_times.copy(),
                throughput_rps=throughput_rps,
                cpu_usage_percent=avg_cpu,
                memory_usage_mb=avg_memory,
                error_count=error_count,
                success_count=success_count
            )
            
            self.metrics.append(metrics)
            logger.info(f"Performance metrics collected for {test_name}: "
                       f"{duration_ms:.2f}ms, {throughput_rps:.2f} RPS")
    
    def _get_current_resources(self) -> ResourceUsage:
        """Get current system resource usage."""
        net_io = psutil.net_io_counters()
        return ResourceUsage(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(),
            memory_mb=psutil.virtual_memory().used / (1024 * 1024),
            network_bytes_sent=net_io.bytes_sent,
            network_bytes_recv=net_io.bytes_recv
        )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        if not self.metrics:
            return {"message": "No metrics collected"}
        
        total_duration = sum(m.duration_ms for m in self.metrics)
        avg_response_time = sum(
            sum(m.response_times) / len(m.response_times) if m.response_times else 0 
            for m in self.metrics
        ) / len(self.metrics) if self.metrics else 0
        
        total_requests = sum(m.success_count + m.error_count for m in self.metrics)
        total_errors = sum(m.error_count for m in self.metrics)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        avg_throughput = sum(m.throughput_rps for m in self.metrics) / len(self.metrics)
        avg_cpu = sum(m.cpu_usage_percent for m in self.metrics) / len(self.metrics)
        avg_memory = sum(m.memory_usage_mb for m in self.metrics) / len(self.metrics)
        
        return {
            "total_tests": len(self.metrics),
            "total_duration_ms": total_duration,
            "average_response_time_ms": avg_response_time,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_percent": error_rate,
            "average_throughput_rps": avg_throughput,
            "average_cpu_percent": avg_cpu,
            "average_memory_mb": avg_memory,
            "test_details": [asdict(m) for m in self.metrics]
        }
    
    def get_performance_report(self) -> str:
        """Generate a formatted performance report."""
        summary = self.get_metrics_summary()
        
        if "message" in summary:
            return summary["message"]
        
        report_lines = [
            "=== INTEGRATION TEST PERFORMANCE REPORT ===",
            "",
            f"Total Tests: {summary['total_tests']}",
            f"Total Duration: {summary['total_duration_ms']:.2f} ms",
            f"Average Response Time: {summary['average_response_time_ms']:.2f} ms",
            f"Total Requests: {summary['total_requests']}",
            f"Error Rate: {summary['error_rate_percent']:.2f}%",
            f"Average Throughput: {summary['average_throughput_rps']:.2f} RPS",
            f"Average CPU Usage: {summary['average_cpu_percent']:.2f}%",
            f"Average Memory Usage: {summary['average_memory_mb']:.2f} MB",
            "",
            "=== TEST DETAILS ===",
            ""
        ]
        
        for test in summary['test_details']:
            report_lines.extend([
                f"Test: {test['test_name']}",
                f"  Duration: {test['duration_ms']:.2f} ms",
                f"  Throughput: {test['throughput_rps']:.2f} RPS",
                f"  Requests: {test['success_count']} success, {test['error_count']} errors",
                f"  CPU: {test['cpu_usage_percent']:.2f}%, Memory: {test['memory_usage_mb']:.2f} MB",
                ""
            ])
        
        return "\n".join(report_lines)
    
    def export_metrics(self, output_file: str):
        """Export metrics to a JSON file."""
        import json
        from pathlib import Path
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.get_metrics_summary(), f, indent=2)
        
        logger.info(f"Performance metrics exported to {output_path}")
    
    def clear_metrics(self):
        """Clear all collected metrics."""
        self.metrics.clear()
        self.resource_usage.clear()
        logger.info("Performance metrics cleared")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()