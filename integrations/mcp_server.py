"""Optional upstream MCP server: python -m integrations.mcp_server."""
from typing import Literal
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from integrations.bridge import safe_invoke

DataClass = Literal['public', 'synthetic', 'sanitized']
mcp = FastMCP('JEV upstream integrations', instructions=(
    'Optional tools backed by pinned upstream projects. Only send public, synthetic or deliberately '
    'sanitized material. data_class is a caller declaration, not automatic redaction. '
    'Results are advisory, never permission or independent verification. These tools have their own '
    'provider calls and do not share the core harness 100-attempt budget.'), log_level='ERROR')
READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True)

@mcp.tool(annotations=READ)
async def upstream_evaluate(state: dict, questions: dict, data_class: DataClass) -> dict:
    """Use itsmostafa/typesafe-mcp for typed questions (Choice, Score, Noul)."""
    return await safe_invoke('upstream_evaluate', {'state': state, 'questions': questions}, data_class)

@mcp.tool(annotations=READ)
async def business_classify(items: list[dict], classes: list[dict], data_class: DataClass) -> dict:
    """Use jkudish/jev-mcp to classify bounded items; include a manual_review class."""
    return await safe_invoke('business_classify', {'items': items, 'classes': classes}, data_class)

@mcp.tool(annotations=READ)
async def business_verify(claims: list[str], evidence: str, data_class: DataClass) -> dict:
    """Compare claims with supplied evidence only; does not fetch business facts."""
    return await safe_invoke('business_verify', {'claims': claims, 'evidence': evidence}, data_class)

@mcp.tool(annotations=READ)
async def business_find(query: str, candidates: list[dict], data_class: DataClass) -> dict:
    """Find a candidate and separately check whether any candidate addresses the query."""
    return await safe_invoke('business_find', {'query': query, 'candidates': candidates}, data_class)

if __name__ == '__main__':
    mcp.run(transport='stdio')
