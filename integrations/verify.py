"""Offline upstream MCP handshakes; --live adds three synthetic provider requests."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from integrations.bridge import environment, invoke, TOOLS
from integrations.kit import ROOT, command


async def check(live):
    report = {'data_class':'synthetic','live':live,'handshakes':{},'live_checks':[]}
    for name in ('typesafe-mcp','jev-mcp','bridge'):
        cmd = ([sys.executable,'-m','integrations.mcp_server'] if name == 'bridge' else command(name))
        if name == 'typesafe-mcp': cmd += ['mcp']
        async with asyncio.timeout(30):
            async with stdio_client(StdioServerParameters(command=cmd[0],args=cmd[1:],cwd=str(ROOT),env=environment(offline=True))) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    names=sorted(t.name for t in (await session.list_tools()).tools)
                    required = {'evaluate'} if name == 'typesafe-mcp' else set(TOOLS) if name == 'bridge' else {'jev_classify','jev_verify','jev_find'}
                    if not required.issubset(names): raise RuntimeError('Missing upstream tools')
                    report['handshakes'][name]=names
    if live:
        # Only synthetic literals below can be sent by this test.
        result=await invoke('upstream_evaluate', {'state':{'text':'The parcel has not arrived.'},'questions':{'delivery':{'type':'noul','instructions':'Does the message concern delivery?'}}}, 'synthetic')
        if result['status'] != 'ok': raise RuntimeError('evaluate call failed')
        p=result['result']['answers']['delivery']['noul']
        if not isinstance(p,(int,float)) or not 0 <= p <= 1: raise RuntimeError('Invalid evaluate probability')
        report['live_checks'].append({'component':'typesafe-mcp','valid_answer':True})
        result=await invoke('business_classify',{'items':[{'id':'S1','text':'My parcel has not arrived.'}], 'classes':[{'id':'shipping','description':'Delivery and parcel tracking'},{'id':'other','description':'Other or unclear'}]},'synthetic')
        if result['status'] != 'ok': raise RuntimeError('classify call failed')
        rows = result['result'].get('results', [])
        if len(rows) != 1 or rows[0].get('id') != 'S1' or rows[0].get('classification') not in ('shipping','other') or rows[0].get('status') == 'invalid_response':
            raise RuntimeError('Invalid classify answer or lost record id')
        report['live_checks'].append({'component':'jev-mcp','valid_tool_response':True})
        from integrations.batch import screen
        from reflex_guard.providers.typesafe import TypeSafeProvider
        if os.environ.get('HARNESS_JEV_PROVIDER','typesafe') != 'typesafe':
            report['live_checks'].append({'component':'semdecide','skipped':'TypeSafe-only upstream'})
        else:
            result=screen([{'id':'S1','text':'My parcel has not arrived.'}],TypeSafeProvider(timeout=12,retries=0),'Does this message concern delivery?')
            if result['records'][0]['route']=='provider_error': raise RuntimeError('SemDecide live call failed')
            report['live_checks'].append({'component':'semdecide','valid_answer':True})
    report['passed']=True
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=asyncio.run(check(args.live))
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    print(text)
