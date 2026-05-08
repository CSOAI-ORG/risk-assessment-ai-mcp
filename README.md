<div align="center">

# Risk Assessment Ai MCP

**MCP server for risk assessment ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-risk-assessment-ai-mcp)](https://pypi.org/project/meok-risk-assessment-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Risk Assessment Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `assess_risk` | Assess risk |
| `create_risk_register` | Create risk register |
| `add_risk` | Add risk to register |
| `get_risk_register` | Get risks in register |
| `update_risk_status` | Update risk status |
| `create_mitigation_plan` | Create mitigation plan |
| `get_mitigation_progress` | Get mitigation progress |
| `calculate_reserve` | Calculate contingency reserve |
| `risk_heatmap_data` | Get heatmap data |
| `get_top_risks` | Get highest priority risks |
| `risk_trend_analysis` | Analyze risk trends |
| `export_risk_report` | Export risk report |

## Installation

```bash
pip install meok-risk-assessment-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "risk-assessment-ai": {
      "command": "python",
      "args": ["-m", "meok_risk_assessment_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 12 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
