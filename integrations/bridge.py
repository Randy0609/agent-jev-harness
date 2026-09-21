"""Small explicit MCP adapter; never copies credentials into client configuration."""
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from integrations.kit import command, ROOT

TOOLS = {'upstream_evaluate': ('typesafe-mcp', 'evaluate'),
         'business_classify': ('jev-mcp', 'jev_classify'),
         'business_verify': ('jev-mcp', 'jev_verify'),
         'business_find': ('jev-mcp', 'jev_find')}


def environment(offline=False):
    # Explicit provider prevents a leftover key from choosing a different route.
    provider = os.environ.get('HARNESS_JEV_PROVIDER', 'typesafe')
    if provider not in ('typesafe', 'openrouter'):
        raise ValueError('HARNESS_JEV_PROVIDER must be typesafe or openrouter')
    key_name = 'TYPESAFE_API_KEY' if provider == 'typesafe' else 'OPENROUTER_API_KEY'
    value = 'offline-placeholder-not-a-key' if offline else os.environ.get(key_name)
    if not value:
        raise ValueError(f'Set {key_name} in the launching environment')
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'TMPDIR', 'SYSTEMROOT') if k in os.environ}
    env.update({key_name: value, 'JEV_PROVIDER': provider})
    if provider == 'openrouter':
        env['JEV_MCP_MODEL'] = 'typesafe/jev-1.13'
    return env


async def invoke(name, arguments, data_class):
    if name not in TOOLS or data_class not in ('public', 'synthetic', 'sanitized'):
        raise ValueError('Invalid tool or data_class')
    if len(json.dumps(arguments, ensure_ascii=False).encode()) > 20000:
        raise ValueError('Input exceeds 20 KB; send a minimal summary')
    component, upstream = TOOLS[name]
    env = environment()
    args = dict(arguments)
    if component == 'typesafe-mcp' and env['JEV_PROVIDER'] == 'openrouter':
        # Upstream default alias is not used; official Decisions docs use this slug.
        args.setdefault('model', 'typesafe/jev-1.13')
    cmd = command(component) + (['mcp'] if component == 'typesafe-mcp' else [])
    async with asyncio.timeout(45):
        async with stdio_client(StdioServerParameters(command=cmd[0], args=cmd[1:], cwd=str(ROOT), env=env)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(upstream, args)
                if result.isError:
                    # Upstream error bodies can reflect secrets or input: do not relay them.
                    return {'status': 'upstream_error', 'component': component, 'advisory_only': True}
                payload = result.structuredContent
                if payload is None:
                    payload = json.loads(next(c.text for c in result.content if c.type == 'text'))
                return {'status': 'ok', 'component': component, 'provider': env['JEV_PROVIDER'],
                        'data_class': data_class, 'advisory_only': True, 'result': payload}


async def safe_invoke(name, arguments, data_class):
    try:
        return await invoke(name, arguments, data_class)
    except Exception:
        return {'status': 'unavailable', 'advisory_only': True,
                'next': 'Check component installation, provider and credentials locally. No completion claim was accepted.'}
