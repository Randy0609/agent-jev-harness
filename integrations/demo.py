"""Offline synthetic receipt: real subprocess checks + Canny + SemDecide (mock provider)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from integrations.kit import BASE, ROOT, source
from integrations.batch import screen


class DemoProvider:
    """Explicit synthetic fixture, never represented as a live model response."""
    def evaluate(self, state, questions):
        values = [0.97, 0.12, 0.8]
        return {'answers': {key: {'noul': values[i]} for i, key in enumerate(questions)}, 'model': 'MOCK-no-network'}, 0


def run(output):
    source('canny')
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / 'daily-report.json'
    # Both subprocesses operate on synthetic data, not company systems.
    produce = subprocess.run([sys.executable, '-c',
        'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"data_class":"synthetic","amounts":[100,200],"total":300}))', str(artifact)], capture_output=True)
    check = subprocess.run([sys.executable, '-c',
        'import json,sys; x=json.load(open(sys.argv[1])); assert sum(x["amounts"])==x["total"]; print("sum verified")', str(artifact)], capture_output=True)
    now = int(time.time() * 1000)
    events = [
        {'ts': now, 'type': 'event', 'phase': 'after', 'hookEvent': 'demo', 'tool': 'report', 'fact':
         {'kind': 'edit', 'files': ['daily-report.json'], 'deleted': [], 'code': ['daily-report.json']}},
        {'ts': now + 1, 'type': 'event', 'phase': 'after', 'hookEvent': 'demo', 'tool': 'check', 'fact':
         {'kind': 'command', 'command': 'synthetic report sum check', 'exitCode': check.returncode,
          'verify': True, 'fingerprint': hashlib.sha256(check.stdout + check.stderr).hexdigest(),
          'summary': 'sum verified' if check.returncode == 0 else 'check failed', 'code': []}}]
    event_path = output / 'events.json'
    event_path.write_text(json.dumps(events))
    ledger = output / f'canny-{time.time_ns()}.jsonl'
    result = subprocess.run(['node', str(BASE / 'canny_evidence.mjs'), str(event_path), str(ledger)], check=True, capture_output=True, text=True)
    canny = json.loads(result.stdout)
    batch = screen([{'id': 'S1', 'text': '物流三天没有更新'}, {'id': 'S2', 'text': '想了解尺码'}, {'id': 'S3', 'text': '订单有点问题'}], DemoProvider(), 'Does this synthetic message report a logistics issue?')
    receipt = {'schema_version': 1, 'data_class': 'synthetic', 'title': '经营日报 · 合成数据演示',
               'generated': produce.returncode == 0 and artifact.exists(),
               'checked': check.returncode == 0 and canny['verification_after_last_edit'],
               'sent': False, 'target_visible': False,
               'evidence': [{'label': '模拟金额核对', 'status': 'passed' if check.returncode == 0 else 'failed', 'detail': '100 + 200 = 300；独立 Python 进程退出码 ' + str(check.returncode)},
                            {'label': 'Canny 执行台账', 'status': 'passed' if canny['verification_after_last_edit'] else 'missing', 'detail': '调用上游 ledger.summarize，检查发生在产物记录之后'},
                            {'label': '真实业务数据覆盖', 'status': 'missing', 'detail': '本例只使用合成数据，没有接入业务系统'},
                            {'label': '发送与目标回读', 'status': 'missing', 'detail': '未执行发送，也没有目标端回执'}],
               'batch': batch['records'], 'batch_model': batch.get('model', 'unavailable')}
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'receipt': str(output / 'receipt.json'), 'canny': canny, 'batch_model': receipt['batch_model'], 'network_calls': 0}, ensure_ascii=False, indent=2))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts' / 'integrations-demo')
    run(parser.parse_args().output.resolve())
