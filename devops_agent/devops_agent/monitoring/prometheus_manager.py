"""
Prometheus monitoring manager for the Agentic AI Development Platform.

This module handles the configuration and deployment of Prometheus and Grafana
for monitoring the platform's performance and health.
"""

import logging
import os
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class PrometheusManager:
    """Manages Prometheus and Grafana monitoring setup."""

    def __init__(self):
        """Initialize the Prometheus manager."""
        self.config = None
        self.monitoring_dir = "devops_agent/devops_agent/monitoring/config"

    def init_config(self, config_path):
        """Initialize configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f).get("monitoring", {})
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            self.config = {}

        # Create monitoring config directory if it doesn't exist
        os.makedirs(self.monitoring_dir, exist_ok=True)
        
        # Generate monitoring configuration files
        self._generate_prometheus_config()
        self._generate_alertmanager_config()
        self._generate_grafana_dashboards()

    def _generate_prometheus_config(self):
        """Generate Prometheus configuration."""
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s",
                "scrape_timeout": "10s",
            },
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["alertmanager:9093"],
                            }
                        ]
                    }
                ]
            },
            "rule_files": [
                "/etc/prometheus/rules/*.yml"
            ],
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [
                        {
                            "targets": ["localhost:9090"]
                        }
                    ]
                },
                {
                    "job_name": "node_exporter",
                    "static_configs": [
                        {
                            "targets": ["node-exporter:9100"]
                        }
                    ]
                },
                {
                    "job_name": "cadvisor",
                    "static_configs": [
                        {
                            "targets": ["cadvisor:8080"]
                        }
                    ]
                },
                {
                    "job_name": "master_orchestrator",
                    "static_configs": [
                        {
                            "targets": ["master-orchestrator:8000"]
                        }
                    ],
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "backend_agent",
                    "static_configs": [
                        {
                            "targets": ["backend-agent:8000"]
                        }
                    ],
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "api_gateway",
                    "static_configs": [
                        {
                            "targets": ["api-gateway:3000"]
                        }
                    ],
                    "metrics_path": "/metrics"
                }
            ]
        }
        
        # Write Prometheus configuration
        output_path = f"{self.monitoring_dir}/prometheus.yml"
        with open(output_path, "w") as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        logger.info(f"Generated Prometheus configuration at {output_path}")
        
        # Generate alert rules
        self._generate_alert_rules()

    def _generate_alert_rules(self):
        """Generate Prometheus alert rules."""
        alert_rules = {
            "groups": [
                {
                    "name": "node_alerts",
                    "rules": [
                        {
                            "alert": "HighCPULoad",
                            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High CPU load (instance {{ $labels.instance }})",
                                "description": "CPU load is above 80% for 5 minutes\n  VALUE = {{ $value }}\n  LABELS: {{ $labels }}"
                            }
                        },
                        {
                            "alert": "HighMemoryUsage",
                            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High memory usage (instance {{ $labels.instance }})",
                                "description": "Memory usage is above 85% for 5 minutes\n  VALUE = {{ $value }}\n  LABELS: {{ $labels }}"
                            }
                        },
                        {
                            "alert": "HighDiskUsage",
                            "expr": "100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes) > 85",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High disk usage (instance {{ $labels.instance }})",
                                "description": "Disk usage is above 85% for 5 minutes\n  VALUE = {{ $value }}\n  LABELS: {{ $labels }}"
                            }
                        }
                    ]
                },
                {
                    "name": "service_alerts",
                    "rules": [
                        {
                            "alert": "ServiceDown",
                            "expr": "up == 0",
                            "for": "1m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Service {{ $labels.job }} is down",
                                "description": "Service {{ $labels.job }} on instance {{ $labels.instance }} has been down for more than 1 minute."
                            }
                        },
                        {
                            "alert": "HighResponseTime",
                            "expr": "http_request_duration_seconds{quantile=\"0.9\"} > 1",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High response time (instance {{ $labels.instance }})",
                                "description": "90th percentile of response time is above 1 second for 5 minutes\n  VALUE = {{ $value }}\n  LABELS: {{ $labels }}"
                            }
                        }
                    ]
                }
            ]
        }
        
        # Create rules directory if it doesn't exist
        os.makedirs(f"{self.monitoring_dir}/rules", exist_ok=True)
        
        # Write alert rules
        output_path = f"{self.monitoring_dir}/rules/alerts.yml"
        with open(output_path, "w") as f:
            yaml.dump(alert_rules, f, default_flow_style=False)
        
        logger.info(f"Generated Prometheus alert rules at {output_path}")

    def _generate_alertmanager_config(self):
        """Generate Alertmanager configuration."""
        alertmanager_config = {
            "global": {
                "resolve_timeout": "5m",
                "smtp_smarthost": "smtp.example.org:587",
                "smtp_from": "alerts@example.org",
                "smtp_auth_username": "alerts@example.org",
                "smtp_auth_password": "password",
                "smtp_require_tls": True
            },
            "route": {
                "group_by": ["alertname", "job"],
                "group_wait": "30s",
                "group_interval": "5m",
                "repeat_interval": "12h",
                "receiver": "email-notifications",
                "routes": [
                    {
                        "match": {
                            "severity": "critical"
                        },
                        "receiver": "pager-notifications",
                        "repeat_interval": "1h"
                    }
                ]
            },
            "receivers": [
                {
                    "name": "email-notifications",
                    "email_configs": [
                        {
                            "to": "team@example.org",
                            "send_resolved": True
                        }
                    ]
                },
                {
                    "name": "pager-notifications",
                    "email_configs": [
                        {
                            "to": "oncall@example.org",
                            "send_resolved": True
                        }
                    ]
                }
            ]
        }
        
        # Write Alertmanager configuration
        output_path = f"{self.monitoring_dir}/alertmanager.yml"
        with open(output_path, "w") as f:
            yaml.dump(alertmanager_config, f, default_flow_style=False)
        
        logger.info(f"Generated Alertmanager configuration at {output_path}")

    def _generate_grafana_dashboards(self):
        """Generate Grafana dashboards."""
        # Create dashboards directory if it doesn't exist
        os.makedirs(f"{self.monitoring_dir}/grafana/dashboards", exist_ok=True)
        
        # Generate system overview dashboard (simplified for readability)
        system_dashboard = {
            "title": "System Overview",
            "uid": "system-overview",
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 1,
            "refresh": "10s",
            "panels": [
                {
                    "title": "CPU Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                            "legendFormat": "{{ instance }}",
                            "refId": "A"
                        }
                    ]
                },
                {
                    "title": "Memory Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
                            "legendFormat": "{{ instance }}",
                            "refId": "A"
                        }
                    ]
                },
                {
                    "title": "Disk Usage",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)",
                            "legendFormat": "{{ instance }} {{ mountpoint }}",
                            "refId": "A"
                        }
                    ]
                }
            ]
        }
        
        # Generate services dashboard
        services_dashboard = {
            "title": "Services Overview",
            "uid": "services-overview",
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 1,
            "refresh": "10s",
            "panels": [
                {
                    "title": "Service Up/Down Status",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 24, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": "up",
                            "legendFormat": "{{ job }}",
                            "refId": "A"
                        }
                    ]
                },
                {
                    "title": "HTTP Request Rate",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
                    "targets": [
                        {
                            "expr": "rate(http_requests_total[5m])",
                            "legendFormat": "{{ job }} {{ handler }}",
                            "refId": "A"
                        }
                    ]
                },
                {
                    "title": "HTTP Response Time",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
                    "targets": [
                        {
                            "expr": "http_request_duration_seconds{quantile=\"0.5\"}",
                            "legendFormat": "{{ job }} {{ handler }} (p50)",
                            "refId": "A"
                        },
                        {
                            "expr": "http_request_duration_seconds{quantile=\"0.9\"}",
                            "legendFormat": "{{ job }} {{ handler }} (p90)",
                            "refId": "B"
                        }
                    ]
                }
            ]
        }
        
        # Write dashboard files
        with open(f"{self.monitoring_dir}/grafana/dashboards/system.json", "w") as f:
            f.write(str(system_dashboard).replace("'", "\""))
        
        with open(f"{self.monitoring_dir}/grafana/dashboards/services.json", "w") as f:
            f.write(str(services_dashboard).replace("'", "\""))
        
        logger.info(f"Generated Grafana dashboards in {self.monitoring_dir}/grafana/dashboards")

    def generate_docker_compose(self):
        """Generate Docker Compose file for monitoring stack."""
        compose_file = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "volumes": [
                        "./config/prometheus.yml:/etc/prometheus/prometheus.yml",
                        "./config/rules:/etc/prometheus/rules"
                    ],
                    "ports": ["9090:9090"],
                    "networks": ["monitoring"]
                },
                "alertmanager": {
                    "image": "prom/alertmanager:latest",
                    "volumes": [
                        "./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml"
                    ],
                    "ports": ["9093:9093"],
                    "networks": ["monitoring"]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "volumes": [
                        "./config/grafana/dashboards:/var/lib/grafana/dashboards",
                        "./config/grafana/provisioning:/etc/grafana/provisioning"
                    ],
                    "ports": ["3000:3000"],
                    "networks": ["monitoring"],
                    "environment": [
                        "GF_SECURITY_ADMIN_USER=admin",
                        "GF_SECURITY_ADMIN_PASSWORD=admin",
                        "GF_USERS_ALLOW_SIGN_UP=false"
                    ]
                },
                "node-exporter": {
                    "image": "prom/node-exporter:latest",
                    "volumes": [
                        "/proc:/host/proc:ro",
                        "/sys:/host/sys:ro",
                        "/:/rootfs:ro"
                    ],
                    "command": [
                        "--path.procfs=/host/proc",
                        "--path.sysfs=/host/sys",
                        "--path.rootfs=/rootfs",
                        "--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)"
                    ],
                    "ports": ["9100:9100"],
                    "networks": ["monitoring"]
                },
                "cadvisor": {
                    "image": "gcr.io/cadvisor/cadvisor:latest",
                    "volumes": [
                        "/:/rootfs:ro",
                        "/var/run:/var/run:ro",
                        "/sys:/sys:ro",
                        "/var/lib/docker/:/var/lib/docker:ro",
                        "/dev/disk/:/dev/disk:ro"
                    ],
                    "ports": ["8080:8080"],
                    "networks": ["monitoring"]
                }
            },
            "networks": {
                "monitoring": {
                    "driver": "bridge"
                }
            }
        }
        
        # Write docker-compose.yml
        output_path = f"{self.monitoring_dir}/../docker-compose.monitoring.yml"
        with open(output_path, "w") as f:
            yaml.dump(compose_file, f, default_flow_style=False)
        
        logger.info(f"Generated Docker Compose file for monitoring at {output_path}")
        return output_path

    def setup(self, environment="dev"):
        """Set up monitoring for the specified environment."""
        logger.info(f"Setting up monitoring for {environment} environment...")
        
        # Ensure all configuration files are generated
        if not os.path.exists(f"{self.monitoring_dir}/prometheus.yml"):
            logger.warning("Prometheus configuration not found, generating...")
            self._generate_prometheus_config()
        
        if not os.path.exists(f"{self.monitoring_dir}/alertmanager.yml"):
            logger.warning("Alertmanager configuration not found, generating...")
            self._generate_alertmanager_config()
        
        if not os.path.exists(f"{self.monitoring_dir}/grafana/dashboards"):
            logger.warning("Grafana dashboards not found, generating...")
            self._generate_grafana_dashboards()
        
        # Generate Docker Compose file
        compose_file = self.generate_docker_compose()
        
        logger.info(f"Monitoring setup complete for {environment}. Use Docker Compose file at {compose_file} to start the monitoring stack.")
        return True