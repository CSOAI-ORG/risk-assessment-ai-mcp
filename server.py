#!/usr/bin/env python3
"""MEOK AI Labs — risk-assessment-ai-mcp MCP Server. Enterprise risk assessment and management."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.fastmcp import FastMCP
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

_store = {"assessments": [], "risks": [], "mitigation_plans": [], "risk_registers": {}}
mcp = FastMCP("risk-assessment-ai", instructions="Enterprise risk assessment and management.")


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


@mcp.tool()
def assess_risk(risk_name: str = "Unnamed", likelihood: int = 3, impact: int = 3, category: str = "General", api_key: str = "") -> str:
    """Assess risk"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    result = calculate_risk_score(likelihood, impact)
    assessment = {
        "id": create_id(),
        "name": risk_name,
        "category": category,
        "score": result,
        "assessed_at": datetime.now().isoformat(),
    }
    _store["assessments"].append(assessment)
    return json.dumps({"risk": risk_name, **result}, indent=2)


@mcp.tool()
def create_risk_register(project_name: str, owner: str = "Unassigned", api_key: str = "") -> str:
    """Create risk register"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    register = {
        "id": create_id(),
        "project_name": project_name,
        "owner": owner,
        "risks": [],
        "created_at": datetime.now().isoformat(),
    }
    _store["risk_registers"][register["id"]] = register
    return json.dumps(
        {"register_id": register["id"], "project": project_name}, indent=2
    )


@mcp.tool()
def add_risk(register_id: str, risk_name: str, likelihood: int, impact: int, category: str = "General", mitigation: str = "", api_key: str = "") -> str:
    """Add risk to register"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if register_id not in _store["risk_registers"]:
        return json.dumps({"error": "Register not found"})
    result = calculate_risk_score(likelihood, impact)
    risk = {
        "id": create_id(),
        "name": risk_name,
        "category": category,
        "mitigation": mitigation,
        "score": result,
        "status": "identified",
        "added_at": datetime.now().isoformat(),
    }
    _store["risk_registers"][register_id]["risks"].append(risk)
    _store["risks"].append(risk)
    return json.dumps(
        {"risk_id": risk["id"], "level": result["level"], "priority": result["priority"]},
        indent=2,
    )


@mcp.tool()
def get_risk_register(register_id: str, api_key: str = "") -> str:
    """Get risks in register"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if register_id not in _store["risk_registers"]:
        return json.dumps({"error": "Register not found"})
    register = _store["risk_registers"][register_id]
    return json.dumps(
        {
            "project": register["project_name"],
            "total_risks": len(register["risks"]),
            "risks": register["risks"],
        },
        indent=2,
    )


@mcp.tool()
def update_risk_status(risk_id: str, new_likelihood: int = 0, new_impact: int = 0, status: str = "", api_key: str = "") -> str:
    """Update risk status"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    for risk in _store["risks"]:
        if risk["id"] == risk_id:
            if new_likelihood and new_impact:
                risk["score"] = calculate_risk_score(new_likelihood, new_impact)
            if status:
                risk["status"] = status
            return json.dumps({"updated": True, "risk": risk}, indent=2)
    return json.dumps({"error": "Risk not found"})


@mcp.tool()
def create_mitigation_plan(risk_id: str, actions: list = None, owner: str = "Unassigned", due_date: str = "", api_key: str = "") -> str:
    """Create mitigation plan"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    plan = {
        "id": create_id(),
        "risk_id": risk_id,
        "actions": actions or [],
        "owner": owner,
        "due_date": due_date or None,
        "status": "in_progress",
        "completed": 0,
        "created_at": datetime.now().isoformat(),
    }
    _store["mitigation_plans"].append(plan)
    return json.dumps({"plan_id": plan["id"], "actions": len(plan["actions"])}, indent=2)


@mcp.tool()
def get_mitigation_progress(risk_id: str, api_key: str = "") -> str:
    """Get mitigation progress"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    plans = [p for p in _store["mitigation_plans"] if p.get("risk_id") == risk_id]
    if not plans:
        return json.dumps({"error": "No plan found"})
    plan = plans[0]
    progress = (
        (plan["completed"] / len(plan["actions"]) * 100) if plan["actions"] else 0
    )
    return json.dumps(
        {"progress_percent": round(progress, 1), "status": plan["status"]}, indent=2
    )


@mcp.tool()
def calculate_reserve(risks: list = None, api_key: str = "") -> str:
    """Calculate contingency reserve"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    risks_list = risks or []
    total = sum(
        (
            calculate_risk_score(r.get("likelihood", 3), r.get("impact", 3))["score"]
            / 25
        )
        * r.get("impact", 3)
        * 10000
        for r in risks_list
    )
    return json.dumps({"contingency_reserve": round(total, 2)}, indent=2)


@mcp.tool()
def risk_heatmap_data(register_id: str, api_key: str = "") -> str:
    """Get heatmap data"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if register_id not in _store["risk_registers"]:
        return json.dumps({"error": "Not found"})
    matrix = {}
    for r in _store["risk_registers"][register_id]["risks"]:
        key = f"{r['score']['score']}-{r['score']['score']}"
        matrix[key] = matrix.get(key, 0) + 1
    return json.dumps({"heatmap": matrix}, indent=2)


@mcp.tool()
def get_top_risks(limit: int = 10, api_key: str = "") -> str:
    """Get highest priority risks"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    sorted_risks = sorted(
        _store["risks"], key=lambda x: x["score"]["score"], reverse=True
    )
    return json.dumps({"top_risks": sorted_risks[:limit]}, indent=2)


@mcp.tool()
def risk_trend_analysis(register_id: str, days: int = 30, api_key: str = "") -> str:
    """Analyze risk trends"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if register_id not in _store["risk_registers"]:
        return json.dumps({"error": "Not found"})
    risks = _store["risk_registers"][register_id]["risks"]
    return json.dumps(
        {
            "total": len(risks),
            "critical": sum(1 for r in risks if r["score"]["level"] == "critical"),
        },
        indent=2,
    )


@mcp.tool()
def export_risk_report(register_id: str, format: str = "summary", api_key: str = "") -> str:
    """Export risk report"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if register_id not in _store["risk_registers"]:
        return json.dumps({"error": "Not found"})
    register = _store["risk_registers"][register_id]
    if format == "json":
        return json.dumps(register, indent=2)
    return json.dumps(
        {"project": register["project_name"], "total_risks": len(register["risks"])},
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
