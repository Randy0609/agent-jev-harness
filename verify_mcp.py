"""Local MCP smoke check; --live explicitly adds two synthetic provider requests."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def unpack(result):
    if result.isError:
        raise RuntimeError('mcp_tool_error')
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(next(c.text for c in result.content if c.type == 'text'))


async def check(live):
    root = Path(__file__).resolve().parent
    report = {'data_class': 'synthetic', 'live': live, 'checks': []}
    with tempfile.TemporaryDirectory() as tmp:
        env = {k: os.environ[k] for k in ('TYPESAFE_API_KEY', 'TYPESAFE_API_KEY_FILE', 'JEV_MODEL') if k in os.environ}
        env['JEV_DATA_DIR'] = tmp
        params = StdioServerParameters(command=sys.executable, args=[str(root / 'server.py')], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = sorted(t.name for t in (await session.list_tools()).tools)
                if names != ['jev_review', 'jev_status', 'jev_triage']:
                    raise RuntimeError('unexpected_tool_catalog')
                report['tools'] = names
                status = unpack(await session.call_tool('jev_status', {}))
                report['checks'].append({'check': 'status', 'version': status['version'], 'passed': True})
                if live:
                    for name in ('triage', 'review'):
                        arguments = json.loads((root / 'examples' / (name + '.json')).read_text())
                        result = unpack(await session.call_tool('jev_' + name, arguments))
                        if result.get('status') != 'ok':
                            raise RuntimeError('provider_check_unavailable')
                        if name == 'review' and (result.get('verdict') != 'needs_work' or 1 not in result['gap_claims']):
                            raise RuntimeError('missing_evidence_not_flagged')
                        report['checks'].append({'check': name, 'passed': True, 'result': result})
    report['passed'] = True
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Send two synthetic API requests (may incur charges).')
    parser.add_argument('--output', type=Path, help='Optional report path; keep runtime evidence out of source commits.')
    args = parser.parse_args()
    result = asyncio.run(check(args.live))
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    print(output)
