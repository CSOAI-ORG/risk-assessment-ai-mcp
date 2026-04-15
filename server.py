#!/usr/bin/env python3
"""MEOK AI Labs — risk-assessment-ai-mcp MCP Server. Enterprise risk assessment and management."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

from datetime import datetime, timezone
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types

_store = {"assessments": [], "risks": [], "mitigation_plans": [], "risk_registers": {}}
server = Server("risk-assessment-ai")


def create_id():
    return str(uuid.uuid4())[:8]


def calculate_risk_score(likelihood: int, impact: int) -> dict:
    matrix = {
        1: {1: 1, 2: 2, 3: 3, 4: 4, 5: 5},
        2: {1: 2, 2: 4, 3: 6, 4: 8, 5: 10},
        3: {1: 3, 2: 6, 3: 9, 4: 12, 5: 15},
        4: {1: 4, 2: 8, 3: 12, 4: 16, 5: 20},
        5: {1: 5, 2: 10, 3: 15, 4: 20, 5: 25},
    }
    score = matrix[likelihood][impact]
    if score <= 5:
        return {"score": score, "level": "low", "priority": "monitor"}
    elif score <= 10:
        return {"score": score, "level": "medium", "priority": "watch"}
    elif score <= 15:
        return {"score": score, "level": "high", "priority": "action"}
    else:
        return {"score": score, "level": "critical", "priority": "immediate"}


@server.list_resources()
def handle_list_resources():
    return [
        Resource(
            uri="risk://register", name="Risk Register", mimeType="application/json"
        )
    ]


@server.list_tools()
def handle_list_tools():
    return [
        Tool(
            name="assess_risk",
            description="Assess risk",
            inputSchema={
                "type": "object",
                "properties": {
                    "risk_name": {"type": "string"},
                    "likelihood": {"type": "number", "minimum": 1, "maximum": 5},
                    "impact": {"type": "number", "minimum": 1, "maximum": 5},
                    "category": {"type": "string"},
                    "api_key": {"type": "string"},
                },
            },
        ),
        Tool(
            name="create_risk_register",
            description="Create risk register",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "owner": {"type": "string"},
                    "api_key": {"type": "string"},
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="add_risk",
            description="Add risk to register",
            inputSchema={
                "type": "object",
                "properties": {
                    "register_id": {"type": "string"},
                    "risk_name": {"type": "string"},
                    "likelihood": {"type": "number"},
                    "impact": {"type": "number"},
                    "category": {"type": "string"},
                    "mitigation": {"type": "string"},
                    "api_key": {"type": "string"},
                },
                "required": ["register_id", "risk_name", "likelihood", "impact"],
            },
        ),
        Tool(
            name="get_risk_register",
            description="Get risks in register",
            inputSchema={
                "type": "object",
                "properties": {"register_id": {"type": "string"}},
                "required": ["register_id"],
            },
        ),
        Tool(
            name="update_risk_status",
            description="Update risk status",
            inputSchema={
                "type": "object",
                "properties": {
                    "risk_id": {"type": "string"},
                    "new_likelihood": {"type": "number"},
                    "new_impact": {"type": "number"},
                    "status": {"type": "string"},
                },
                "required": ["risk_id"],
            },
        ),
        Tool(
            name="create_mitigation_plan",
            description="Create mitigation plan",
            inputSchema={
                "type": "object",
                "properties": {
                    "risk_id": {"type": "string"},
                    "actions": {"type": "array"},
                    "owner": {"type": "string"},
                    "due_date": {"type": "string"},
                    "api_key": {"type": "string"},
                },
                "required": ["risk_id", "actions"],
            },
        ),
        Tool(
            name="get_mitigation_progress",
            description="Get mitigation progress",
            inputSchema={
                "type": "object",
                "properties": {"risk_id": {"type": "string"}},
            },
        ),
        Tool(
            name="calculate_reserve",
            description="Calculate contingency reserve",
            inputSchema={"type": "object", "properties": {"risks": {"type": "array"}}},
        ),
        Tool(
            name="risk_heatmap_data",
            description="Get heatmap data",
            inputSchema={
                "type": "object",
                "properties": {"register_id": {"type": "string"}},
            },
        ),
        Tool(
            name="get_top_risks",
            description="Get highest priority risks",
            inputSchema={"type": "object", "properties": {"limit": {"type": "number"}}},
        ),
        Tool(
            name="risk_trend_analysis",
            description="Analyze risk trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "register_id": {"type": "string"},
                    "days": {"type": "number"},
                },
            },
        ),
        Tool(
            name="export_risk_report",
            description="Export risk report",
            inputSchema={
                "type": "object",
                "properties": {
                    "register_id": {"type": "string"},
                    "format": {"type": "string", "enum": ["json", "summary"]},
                },
            },
        ),
    ]


@server.call_tool()
def handle_call_tool(name: str, arguments: Any = None) -> list[types.TextContent]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
                ),
            )
        ]
    if err := _rl():
        return [TextContent(type="text", text=err)]

    if name == "assess_risk":
        result = calculate_risk_score(args.get("likelihood", 3), args.get("impact", 3))
        assessment = {
            "id": create_id(),
            "name": args.get("risk_name", "Unnamed"),
            "category": args.get("category", "General"),
            "score": result,
            "assessed_at": datetime.now().isoformat(),
        }
        _store["assessments"].append(assessment)
        return [
            TextContent(
                type="text",
                text=json.dumps({"risk": args.get("risk_name"), **result}, indent=2),
            )
        ]

    elif name == "create_risk_register":
        register = {
            "id": create_id(),
            "project_name": args["project_name"],
            "owner": args.get("owner", "Unassigned"),
            "risks": [],
            "created_at": datetime.now().isoformat(),
        }
        _store["risk_registers"][register["id"]] = register
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"register_id": register["id"], "project": args["project_name"]},
                    indent=2,
                ),
            )
        ]

    elif name == "add_risk":
        register_id = args.get("register_id")
        if register_id not in _store["risk_registers"]:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Register not found"})
                )
            ]
        result = calculate_risk_score(args.get("likelihood", 3), args.get("impact", 3))
        risk = {
            "id": create_id(),
            "name": args["risk_name"],
            "category": args.get("category", "General"),
            "mitigation": args.get("mitigation", ""),
            "score": result,
            "status": "identified",
            "added_at": datetime.now().isoformat(),
        }
        _store["risk_registers"][register_id]["risks"].append(risk)
        _store["risks"].append(risk)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "risk_id": risk["id"],
                        "level": result["level"],
                        "priority": result["priority"],
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "get_risk_register":
        register_id = args.get("register_id")
        if register_id not in _store["risk_registers"]:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Register not found"})
                )
            ]
        register = _store["risk_registers"][register_id]
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "project": register["project_name"],
                        "total_risks": len(register["risks"]),
                        "risks": register["risks"],
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "update_risk_status":
        risk_id = args.get("risk_id")
        for risk in _store["risks"]:
            if risk["id"] == risk_id:
                if args.get("new_likelihood") and args.get("new_impact"):
                    risk["score"] = calculate_risk_score(
                        args["new_likelihood"], args["new_impact"]
                    )
                risk["status"] = args.get("status", risk["status"])
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"updated": True, "risk": risk}, indent=2),
                    )
                ]
        return [TextContent(type="text", text=json.dumps({"error": "Risk not found"}))]

    elif name == "create_mitigation_plan":
        plan = {
            "id": create_id(),
            "risk_id": args["risk_id"],
            "actions": args.get("actions", []),
            "owner": args.get("owner", "Unassigned"),
            "due_date": args.get("due_date"),
            "status": "in_progress",
            "completed": 0,
            "created_at": datetime.now().isoformat(),
        }
        _store["mitigation_plans"].append(plan)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"plan_id": plan["id"], "actions": len(plan["actions"])}, indent=2
                ),
            )
        ]

    elif name == "get_mitigation_progress":
        risk_id = args.get("risk_id")
        plans = [p for p in _store["mitigation_plans"] if p.get("risk_id") == risk_id]
        if not plans:
            return [
                TextContent(type="text", text=json.dumps({"error": "No plan found"}))
            ]
        plan = plans[0]
        progress = (
            (plan["completed"] / len(plan["actions"]) * 100) if plan["actions"] else 0
        )
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"progress_percent": round(progress, 1), "status": plan["status"]},
                    indent=2,
                ),
            )
        ]

    elif name == "calculate_reserve":
        risks = args.get("risks", [])
        total = sum(
            (
                calculate_risk_score(r.get("likelihood", 3), r.get("impact", 3))[
                    "score"
                ]
                / 25
            )
            * r.get("impact", 3)
            * 10000
            for r in risks
        )
        return [
            TextContent(
                type="text",
                text=json.dumps({"contingency_reserve": round(total, 2)}, indent=2),
            )
        ]

    elif name == "risk_heatmap_data":
        register_id = args.get("register_id")
        if register_id not in _store["risk_registers"]:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]
        matrix = {}
        for r in _store["risk_registers"][register_id]["risks"]:
            key = f"{r['score']['score']}-{r['score']['score']}"
            matrix[key] = matrix.get(key, 0) + 1
        return [
            TextContent(type="text", text=json.dumps({"heatmap": matrix}, indent=2))
        ]

    elif name == "get_top_risks":
        limit = args.get("limit", 10)
        sorted_risks = sorted(
            _store["risks"], key=lambda x: x["score"]["score"], reverse=True
        )
        return [
            TextContent(
                type="text",
                text=json.dumps({"top_risks": sorted_risks[:limit]}, indent=2),
            )
        ]

    elif name == "risk_trend_analysis":
        register_id = args.get("register_id")
        if register_id not in _store["risk_registers"]:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]
        risks = _store["risk_registers"][register_id]["risks"]
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "total": len(risks),
                        "critical": sum(
                            1 for r in risks if r["score"]["level"] == "critical"
                        ),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "export_risk_report":
        register_id = args.get("register_id")
        if register_id not in _store["risk_registers"]:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]
        register = _store["risk_registers"][register_id]
        fmt = args.get("format", "summary")
        if fmt == "json":
            return [TextContent(type="text", text=json.dumps(register, indent=2))]
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "project": register["project_name"],
                        "total_risks": len(register["risks"]),
                    },
                    indent=2,
                ),
            )
        ]

    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]


async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (
        read_stream,
        write_stream,
    ):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="risk-assessment-ai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
