"""STDIO MCP entry point; also accepts bounded JSON via --call on stdin."""
import argparse
import json
import sys
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, ValidationError

import core

Text = Annotated[str, Field(min_length=1, max_length=3000)]
SmallText = Annotated[str, Field(max_length=2000)]
DataClass = Literal['synthetic', 'public', 'sanitized']

class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    claim: Text
    evidence: SmallText
    evidence_status: Literal['observed', 'unverified', 'missing']

class TriageInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    goal: Text
    data_class: DataClass
    context: SmallText = ''

class ReviewInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    goal: Text
    claims: Annotated[list[Claim], Field(min_length=1, max_length=8)]
    data_class: DataClass

mcp = FastMCP('Agent + JEV Harness', instructions=(
    'Default: use jev_triage before executing an actionable task, including small tasks, and jev_review '
    'before delivery. Reuse triage for same-goal follow-ups. Skip pure conversation or explicit bypasses. Send only '
    'public/synthetic or deliberately sanitized summaries, no secrets, raw transcripts or private records. '
    'JEV is advisory, cannot grant authorization or switch models. On unavailable, continue with normal Agent '
    'checks. Read the agent-jev-harness skill for workflow details.'), log_level='ERROR')

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True)

@mcp.tool(annotations=READ)
def jev_triage(goal: Text, data_class: DataClass, context: SmallText = '') -> dict:
    """Suggest work mode and evidence needs for a sanitized task summary. Sends summary to TypeSafe. No actions executed."""
    data = TriageInput(goal=goal, context=context, data_class=data_class)
    return core.triage(data.goal, data.context)

@mcp.tool(annotations=READ)
def jev_review(goal: Text, claims: Annotated[list[Claim], Field(min_length=1, max_length=8)], data_class: DataClass) -> dict:
    """Check 1-8 completion claims against supplied sanitized evidence summaries. No independent file access. Sends summaries to TypeSafe."""
    data = ReviewInput(goal=goal, claims=claims, data_class=data_class)
    return core.review(data.goal, [c.model_dump() for c in data.claims])

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def jev_status() -> dict:
    """Local status only. Does not call TypeSafe, read transcripts or return credential values."""
    return core.status()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--call', choices=['triage', 'review', 'status'])
    args = parser.parse_args()
    if not args.call:
        mcp.run(transport='stdio')
    else:
        try:
            if args.call == 'status':
                result = core.status()
            else:
                raw = sys.stdin.buffer.read(20001)
                if len(raw) > 20000:
                    raise ValueError('oversized')
                schema = TriageInput if args.call == 'triage' else ReviewInput
                data = schema.model_validate_json(raw)
                result = (core.triage(data.goal, data.context) if args.call == 'triage'
                          else core.review(data.goal, [c.model_dump() for c in data.claims]))
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except (ValueError, ValidationError):
            print(json.dumps({'status': 'invalid_input', 'reason': 'Check required fields and size limits; no content logged.'}))
            sys.exit(2)
