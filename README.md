# Risk Assessment Ai

> By [MEOK AI Labs](https://meok.ai) — Enterprise risk assessment and management.

MEOK AI Labs — risk-assessment-ai-mcp MCP Server. Enterprise risk assessment and management.

## Installation

```bash
pip install risk-assessment-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install risk-assessment-ai-mcp
```

## Tools

### `assess_risk`
Assess risk

**Parameters:**
- `risk_name` (str)
- `likelihood` (int)
- `impact` (int)
- `category` (str)

### `create_risk_register`
Create risk register

**Parameters:**
- `project_name` (str)
- `owner` (str)

### `add_risk`
Add risk to register

**Parameters:**
- `register_id` (str)
- `risk_name` (str)
- `likelihood` (int)
- `impact` (int)
- `category` (str)
- `mitigation` (str)

### `get_risk_register`
Get risks in register

**Parameters:**
- `register_id` (str)

### `update_risk_status`
Update risk status

**Parameters:**
- `risk_id` (str)
- `new_likelihood` (int)
- `new_impact` (int)
- `status` (str)

### `create_mitigation_plan`
Create mitigation plan

**Parameters:**
- `risk_id` (str)
- `actions` (str)
- `owner` (str)
- `due_date` (str)

### `get_mitigation_progress`
Get mitigation progress

**Parameters:**
- `risk_id` (str)

### `calculate_reserve`
Calculate contingency reserve

**Parameters:**
- `risks` (str)

### `risk_heatmap_data`
Get heatmap data

**Parameters:**
- `register_id` (str)

### `get_top_risks`
Get highest priority risks

**Parameters:**
- `limit` (int)

### `risk_trend_analysis`
Analyze risk trends

**Parameters:**
- `register_id` (str)
- `days` (int)

### `export_risk_report`
Export risk report

**Parameters:**
- `register_id` (str)
- `format` (str)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/risk-assessment-ai-mcp](https://github.com/CSOAI-ORG/risk-assessment-ai-mcp)
- **PyPI**: [pypi.org/project/risk-assessment-ai-mcp](https://pypi.org/project/risk-assessment-ai-mcp/)

## License

MIT — MEOK AI Labs
