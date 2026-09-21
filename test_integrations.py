"""Offline tests for integration boundaries, not model quality tests."""
import asyncio
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations.kit import BASE, source

AVAILABLE = (BASE / 'upstream' / 'semdecide' / 'src').exists()

@unittest.skipUnless(AVAILABLE, 'Initialize optional submodules for integration tests')
class BatchTests(unittest.TestCase):
    def test_preserves_all_rows_and_uncertainty(self):
        from integrations.batch import screen
        from integrations.demo import DemoProvider
        rows = [{'id': str(i), 'text': 'synthetic'} for i in range(3)]
        result = screen(rows, DemoProvider(), 'Synthetic question')
        self.assertEqual([r['id'] for r in result['records']], ['0','1','2'])
        self.assertEqual([r['route'] for r in result['records']], ['match','no_match','review'])

    def test_provider_failure_and_invalid_probability_preserve_rows(self):
        from integrations.batch import screen
        class Broken:
            def evaluate(self, *args): raise RuntimeError('private error must not escape')
        class Invalid:
            def evaluate(self, *args): return {'answers': {'record_0': {'noul': float('nan')}}}, 0
        rows = [{'id':'a','text':'synthetic'}]
        for provider in (Broken(), Invalid()):
            result = screen(rows, provider, 'question')
            self.assertEqual(result['records'][0]['route'], 'provider_error')
            self.assertNotIn('private', json.dumps(result))

    def test_duplicate_ids_rejected_before_network(self):
        from integrations.batch import screen
        with self.assertRaises(ValueError):
            screen([{'id':'a','text':'x'},{'id':'a','text':'y'}], None, 'question')

    def test_canny_invalidates_old_checks_after_edit(self):
        source('canny')
        script = '''import {summarize} from './integrations/upstream/canny/dist/ledger.js';
        const checked={type:'event',fact:{kind:'command',code:[],exitCode:0,verify:true,fingerprint:'x'}};
        const edit={type:'event',fact:{kind:'edit',code:['report.json']}};
        if(summarize([edit,checked]).verified===null) process.exit(1);
        if(summarize([checked,edit]).verified!==null) process.exit(2);'''
        subprocess.run(['node','--input-type=module','-e',script],cwd=BASE.parent,check=True)

    def test_real_demo_does_not_claim_delivery(self):
        from integrations.demo import run
        with tempfile.TemporaryDirectory() as tmp:
            receipt = run(Path(tmp))
            self.assertTrue(receipt['generated'])
            self.assertTrue(receipt['checked'])
            self.assertFalse(receipt['sent'])
            self.assertFalse(receipt['target_visible'])
            self.assertEqual(receipt['batch_model'], 'MOCK-no-network')


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install optional MCP dependencies for bridge tests')
class BridgeTests(unittest.TestCase):
    def test_only_selected_provider_key_is_inherited(self):
        from integrations.bridge import environment
        with patch.dict(os.environ, {'HARNESS_JEV_PROVIDER':'openrouter','OPENROUTER_API_KEY':'synthetic-or', 'TYPESAFE_API_KEY':'synthetic-ts','UNRELATED_SECRET':'do-not-copy'}):
            env=environment()
        self.assertIn('OPENROUTER_API_KEY',env)
        self.assertNotIn('TYPESAFE_API_KEY',env)
        self.assertNotIn('UNRELATED_SECRET',env)

    def test_oversized_payload_rejected_before_call(self):
        from integrations.bridge import invoke
        with self.assertRaises(ValueError):
            asyncio.run(invoke('business_verify',{'evidence':'a'*21000},'synthetic'))

    def test_error_details_not_exposed(self):
        from integrations.bridge import safe_invoke
        with patch('integrations.bridge.invoke',side_effect=RuntimeError('sensitive-provider-body')):
            result=asyncio.run(safe_invoke('business_verify',{},'synthetic'))
        self.assertEqual(result['status'],'unavailable')
        self.assertNotIn('sensitive',json.dumps(result))


if __name__ == '__main__': unittest.main()
