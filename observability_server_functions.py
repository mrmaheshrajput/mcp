"""
MCP Observability Server
A Model Context Protocol server for observability and monitoring systems.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
import sys
from typing import Any, Dict, List, Optional
import httpx

from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
import mcp.server.stdio
import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions, Server


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observability-server")


server = Server("observability-mcp-server")
metrics_data = {}
alerts = []
logs = []
services = [
    {"name": "web-api", "status": "healthy", "response_time": 120},
    {"name": "database", "status": "healthy", "response_time": 45},
    {"name": "cache", "status": "degraded", "response_time": 200},
    {"name": "queue", "status": "healthy", "response_time": 80},
]


def _generate_sample_data():
    """Generate sample observability data"""
    global alerts
    current_time = datetime.now()

    for i in range(24):  # Last 24 hours
        timestamp = current_time - timedelta(hours=i)
        metrics_data[timestamp.isoformat()] = {
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 90),
            "disk_usage": random.uniform(40, 85),
            "request_count": random.randint(100, 1000),
            "error_rate": random.uniform(0.1, 5.0),
            "response_time": random.uniform(50, 300),
        }

    alerts = [
        {
            "id": "alert-001",
            "severity": "warning",
            "service": "web-api",
            "message": "High response time detected",
            "timestamp": (current_time - timedelta(minutes=30)).isoformat(),
            "status": "active",
        },
        {
            "id": "alert-002",
            "severity": "critical",
            "service": "database",
            "message": "Connection pool exhaustion",
            "timestamp": (current_time - timedelta(hours=2)).isoformat(),
            "status": "resolved",
        },
    ]

    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    services = ["web-api", "database", "cache", "queue"]

    for i in range(50):
        timestamp = current_time - timedelta(minutes=i)
        logs.append(
            {
                "timestamp": timestamp.isoformat(),
                "level": random.choice(log_levels),
                "service": random.choice(services),
                "message": f"Sample log message {i}",
                "trace_id": f"trace-{random.randint(1000, 9999)}",
            }
        )


_generate_sample_data()


def _generate_dashboard_html() -> str:
    """Generate HTML dashboard"""
    active_alerts = [a for a in alerts if a["status"] == "active"]
    healthy_services = [s for s in services if s["status"] == "healthy"]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Observability Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .metric-card {{ 
                background: #f5f5f5; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }}
            .status-healthy {{ color: green; }}
            .status-degraded {{ color: orange; }}
            .status-critical {{ color: red; }}
            .alert {{ 
                background: #fff3cd; 
                border: 1px solid #ffeaa7; 
                padding: 10px; 
                margin: 5px 0; 
                border-radius: 3px; 
            }}
        </style>
    </head>
    <body>
        <h1>System Observability Dashboard</h1>
        
        <div class="metric-card">
            <h2>System Overview</h2>
            <p>Services Monitored: {len(services)}</p>
            <p>Healthy Services: {len(healthy_services)}</p>
            <p>Active Alerts: {len(active_alerts)}</p>
            <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metric-card">
            <h2>Service Status</h2>
            {''.join([f'<p><span class="status-{s["status"]}">{s["name"]}: {s["status"].upper()}</span> (Response: {s["response_time"]}ms)</p>' for s in services])}
        </div>
        
        <div class="metric-card">
            <h2>Active Alerts</h2>
            {(''.join([f'<div class="alert"><strong>{a["severity"].upper()}</strong>: {a["message"]} ({a["service"]})</div>' for a in active_alerts]) if active_alerts else '<p>No active alerts</p>')}
        </div>
    </body>
    </html>
    """
    return html


def _generate_observability_report(report_type: str, time_range: str) -> str:
    """Generate observability report"""
    current_time = datetime.now()

    if report_type == "summary":
        active_alerts = [a for a in alerts if a["status"] == "active"]
        healthy_services = [s for s in services if s["status"] == "healthy"]

        report = f"""
OBSERVABILITY SUMMARY REPORT
Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Time Range: {time_range}
SYSTEM HEALTH:
- Total Services: {len(services)}
- Healthy Services: {len(healthy_services)}
- Services with Issues: {len(services) - len(healthy_services)}
- Active Alerts: {len(active_alerts)}
SERVICE STATUS:
{chr(10).join([f"- {s['name']}: {s['status'].upper()} ({s['response_time']}ms)" for s in services])}
CRITICAL ALERTS:
{chr(10).join([f"- {a['severity'].upper()}: {a['message']} ({a['service']})" for a in active_alerts]) if active_alerts else "No active alerts"}
RECOMMENDATIONS:
- Monitor services with degraded status
- Review error logs for patterns
- Consider scaling if response times are high
        """

    elif report_type == "detailed":
        # Get latest metrics
        latest_metrics = list(metrics_data.values())[-1] if metrics_data else {}
        recent_errors = [log for log in logs if log["level"] == "ERROR"][-5:]

        report = f"""
DETAILED OBSERVABILITY REPORT  
Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Time Range: {time_range}
CURRENT SYSTEM METRICS:
- CPU Usage: {latest_metrics.get('cpu_usage', 0):.1f}%
- Memory Usage: {latest_metrics.get('memory_usage', 0):.1f}%
- Disk Usage: {latest_metrics.get('disk_usage', 0):.1f}%
- Request Count: {latest_metrics.get('request_count', 0)}
- Error Rate: {latest_metrics.get('error_rate', 0):.2f}%
- Average Response Time: {latest_metrics.get('response_time', 0):.1f}ms
RECENT ERROR LOGS:
{chr(10).join([f"- [{log['timestamp']}] {log['service']}: {log['message']}" for log in recent_errors]) if recent_errors else "No recent errors"}
ALERT HISTORY:
{chr(10).join([f"- {a['timestamp']}: {a['severity']} - {a['message']} ({a['status']})" for a in alerts[-5:]])}
        """

    else:  # incident report
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        error_logs = [log for log in logs if log["level"] == "ERROR"]

        report = f"""
INCIDENT REPORT
Generated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Time Range: {time_range}
CRITICAL INCIDENTS:
{chr(10).join([f"- {a['timestamp']}: {a['message']} ({a['service']}) - {a['status']}" for a in critical_alerts]) if critical_alerts else "No critical incidents"}
ERROR ANALYSIS:
- Total Errors: {len(error_logs)}
- Services Affected: {len(set(log['service'] for log in error_logs))}
TOP ERROR SOURCES:
{chr(10).join([f"- {service}: {len([log for log in error_logs if log['service'] == service])} errors" for service in set(log['service'] for log in error_logs)])}
IMPACT ASSESSMENT:
- Service Availability: {(len([s for s in services if s['status'] == 'healthy']) / len(services) * 100):.1f}%
- Performance Impact: Based on response times and error rates
        """

    return report


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available observability resources"""
    return [
        Resource(
            uri="observability://metrics",
            name="System Metrics",
            description="Real-time system performance metrics",
            mimeType="application/json",
        ),
        Resource(
            uri="observability://alerts",
            name="Active Alerts",
            description="Current system alerts and incidents",
            mimeType="application/json",
        ),
        Resource(
            uri="observability://services",
            name="Service Status",
            description="Status of all monitored services",
            mimeType="application/json",
        ),
        Resource(
            uri="observability://logs",
            name="System Logs",
            description="Recent system logs and events",
            mimeType="application/json",
        ),
        Resource(
            uri="observability://dashboard",
            name="Observability Dashboard",
            description="HTML dashboard showing system overview",
            mimeType="text/html",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read observability resource content"""

    if uri == "observability://metrics":
        return json.dumps(metrics_data, indent=2)

    elif uri == "observability://alerts":
        return json.dumps(alerts, indent=2)

    elif uri == "observability://services":
        return json.dumps(services, indent=2)

    elif uri == "observability://logs":
        # Return last 20 logs
        recent_logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:20]
        return json.dumps(recent_logs, indent=2)

    elif uri == "observability://dashboard":
        return _generate_dashboard_html()

    else:
        raise ValueError(f"Unknown resource URI: {uri}")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available observability tools"""
    return [
        Tool(
            name="query_metrics",
            description="Query system metrics for a specific time range and service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name to query metrics for",
                    },
                    "metric": {
                        "type": "string",
                        "enum": [
                            "cpu_usage",
                            "memory_usage",
                            "disk_usage",
                            "request_count",
                            "error_rate",
                            "response_time",
                        ],
                        "description": "Metric type to query",
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to look back",
                        "default": 1,
                    },
                },
                "required": ["metric"],
            },
        ),
        Tool(
            name="create_alert",
            description="Create a new alert for monitoring",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service to monitor"},
                    "severity": {
                        "type": "string",
                        "enum": ["info", "warning", "critical"],
                        "description": "Alert severity level",
                    },
                    "message": {"type": "string", "description": "Alert message"},
                },
                "required": ["service", "severity", "message"],
            },
        ),
        Tool(
            name="get_service_health",
            description="Get detailed health information for a specific service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to check",
                    }
                },
                "required": ["service_name"],
            },
        ),
        Tool(
            name="search_logs",
            description="Search system logs with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "enum": ["INFO", "WARN", "ERROR", "DEBUG"],
                        "description": "Log level to filter by",
                    },
                    "service": {
                        "type": "string",
                        "description": "Service name to filter by",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of logs to return",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="generate_report",
            description="Generate a comprehensive observability report",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["summary", "detailed", "incident"],
                        "description": "Type of report to generate",
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["1h", "6h", "24h", "7d"],
                        "description": "Time range for the report",
                        "default": "24h",
                    },
                },
                "required": ["report_type"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool execution"""

    if name == "query_metrics":
        metric = arguments.get("metric")
        hours = arguments.get("hours", 1)
        service = arguments.get("service")

        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=hours)

        filtered_metrics = {}
        for timestamp_str, metrics in metrics_data.items():
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp >= cutoff_time:
                filtered_metrics[timestamp_str] = {metric: metrics[metric]}

        result = {
            "metric": metric,
            "service": service,
            "time_range_hours": hours,
            "data": filtered_metrics,
        }

        return [
            types.TextContent(
                type="text",
                text=f"Metrics Query Result:\n{json.dumps(result, indent=2)}",
            )
        ]

    elif name == "create_alert":
        alert_id = f"alert-{random.randint(1000, 9999)}"
        new_alert = {
            "id": alert_id,
            "service": arguments["service"],
            "severity": arguments["severity"],
            "message": arguments["message"],
            "timestamp": datetime.now().isoformat(),
            "status": "active",
        }

        alerts.append(new_alert)

        return [
            types.TextContent(
                type="text",
                text=f"Alert created successfully:\n{json.dumps(new_alert, indent=2)}",
            )
        ]

    elif name == "get_service_health":
        service_name = arguments["service_name"]

        service = next((s for s in services if s["name"] == service_name), None)
        if not service:
            return [
                types.TextContent(
                    type="text", text=f"Service '{service_name}' not found"
                )
            ]

        recent_metrics = list(metrics_data.values())[-1] if metrics_data else {}

        health_info = {
            "service": service,
            "recent_metrics": recent_metrics,
            "active_alerts": [
                a
                for a in alerts
                if a["service"] == service_name and a["status"] == "active"
            ],
            "timestamp": datetime.now().isoformat(),
        }

        return [
            types.TextContent(
                type="text",
                text=f"Service Health Report:\n{json.dumps(health_info, indent=2)}",
            )
        ]

    elif name == "search_logs":
        level_filter = arguments.get("level")
        service_filter = arguments.get("service")
        limit = arguments.get("limit", 20)

        filtered_logs = logs

        if level_filter:
            filtered_logs = [
                log for log in filtered_logs if log["level"] == level_filter
            ]

        if service_filter:
            filtered_logs = [
                log for log in filtered_logs if log["service"] == service_filter
            ]

        filtered_logs = sorted(
            filtered_logs, key=lambda x: x["timestamp"], reverse=True
        )[:limit]

        return [
            types.TextContent(
                type="text",
                text=f"Log Search Results ({len(filtered_logs)} entries):\n{json.dumps(filtered_logs, indent=2)}",
            )
        ]

    elif name == "generate_report":
        report_type = arguments["report_type"]
        time_range = arguments.get("time_range", "24h")

        report = _generate_observability_report(report_type, time_range)

        return [types.TextContent(type="text", text=report)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def run():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="observability-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


# External API simulation classes
class MetricsAPI:
    """Simulated external metrics API (e.g., Prometheus, DataDog)"""

    @staticmethod
    async def get_metrics(service: str, timerange: str = "1h"):
        """Simulate fetching metrics from external API"""
        await asyncio.sleep(0.1)  # Simulate API delay

        return {
            "service": service,
            "timerange": timerange,
            "metrics": {
                "cpu_usage": random.uniform(20, 80),
                "memory_usage": random.uniform(30, 90),
                "request_rate": random.randint(100, 1000),
                "error_rate": random.uniform(0.1, 5.0),
            },
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def create_dashboard(services: List[str]):
        """Simulate creating a dashboard via API"""
        await asyncio.sleep(0.2)

        return {
            "dashboard_id": f"dash-{random.randint(1000, 9999)}",
            "services": services,
            "url": f"https://metrics.example.com/dashboard/{random.randint(1000, 9999)}",
            "created_at": datetime.now().isoformat(),
        }


class AlertingAPI:
    """Simulated external alerting API (e.g., PagerDuty, Slack)"""

    @staticmethod
    async def send_alert(alert_data: Dict[str, Any]):
        """Simulate sending alert to external system"""
        await asyncio.sleep(0.1)

        return {
            "alert_id": f"ext-alert-{random.randint(1000, 9999)}",
            "status": "sent",
            "external_id": f"pd-{random.randint(10000, 99999)}",
            "sent_at": datetime.now().isoformat(),
        }

    @staticmethod
    async def get_incidents():
        """Simulate fetching incidents from external API"""
        await asyncio.sleep(0.1)

        return [
            {
                "id": f"incident-{i}",
                "title": f"Sample Incident {i}",
                "status": random.choice(["open", "acknowledged", "resolved"]),
                "severity": random.choice(["info", "warning", "critical"]),
                "created_at": (
                    datetime.now() - timedelta(hours=random.randint(1, 48))
                ).isoformat(),
            }
            for i in range(5)
        ]


class LoggingAPI:
    """Simulated external logging API (e.g., ELK Stack, Splunk)"""

    @staticmethod
    async def search_logs(query: str, limit: int = 100):
        """Simulate log search via external API"""
        await asyncio.sleep(0.2)

        services = ["web-api", "database", "cache", "queue"]
        levels = ["INFO", "WARN", "ERROR", "DEBUG"]

        return {
            "query": query,
            "total_hits": random.randint(50, 500),
            "logs": [
                {
                    "timestamp": (
                        datetime.now() - timedelta(minutes=random.randint(1, 60))
                    ).isoformat(),
                    "level": random.choice(levels),
                    "service": random.choice(services),
                    "message": f"Log entry matching '{query}' - {random.randint(1, 1000)}",
                    "trace_id": f"trace-{random.randint(1000, 9999)}",
                }
                for _ in range(min(limit, 10))
            ],
        }

    @staticmethod
    async def get_log_analytics(timerange: str = "24h"):
        """Simulate log analytics from external API"""
        await asyncio.sleep(0.3)

        return {
            "timerange": timerange,
            "total_logs": random.randint(10000, 100000),
            "error_count": random.randint(100, 1000),
            "warn_count": random.randint(500, 2000),
            "top_errors": [
                f"Database connection timeout: {random.randint(10, 100)} occurrences",
                f"API rate limit exceeded: {random.randint(5, 50)} occurrences",
                f"Cache miss ratio high: {random.randint(20, 80)} occurrences",
            ],
        }


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        logger.exception(f"Failed to start observability server: {e}")
        print(e, file=sys.stderr)
        exit(1)