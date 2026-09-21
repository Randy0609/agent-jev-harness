"""Offline fixture replay. No model inference, credentials or network calls."""
import json
from functools import partial
from pathlib import Path
import tempfile
from unittest.mock import patch

import core


def fixture_transport(payload, _key):
    answers = {}
    for name, question in payload['questions'].items():
        if question['type'] == 'noul':
            answers[name] = {'type': 'noul', 'noul': .1}
            continue
        chosen = {'route': 'implementation', 'goal_coverage': 'partial',
                  'claim_0': 'supported', 'claim_1': 'unsupported'}[name]
        answers[name] = {'type': 'choice', 'choice': chosen, 'confidence': .9,
                         'probabilities': {k: float(k == chosen) for k in question['criteria']}}
    return {'model': 'jev-fixture', 'answers': answers, 'usage': {}}


def main():
    directory = Path(__file__).parent / 'examples'
    triage = json.loads((directory / 'triage.json').read_text())
    review = json.loads((directory / 'review.json').read_text())
    evaluate = core.evaluate
    with tempfile.TemporaryDirectory() as tmp, patch.object(core, 'load_key', return_value='fixture'), \
         patch.object(core, 'evaluate', partial(evaluate, transport=fixture_transport, root=Path(tmp))):
        start = core.triage(triage['goal'], triage['context'])
        finish = core.review(review['goal'], review['claims'])
    assert start['answers']['route']['choice'] == 'implementation'
    assert finish['verdict'] == 'needs_work' and finish['gap_claims'] == [1]
    print('离线演示：预设模型响应，非 JEV 实测；未读取密钥，未发出网络请求。')
    print('任务：生成一份虚构经营日报，并发送给测试收件人。')
    print('开工建议：implementation → 制作并检查产物。')
    print('声明 1：日报已生成。证据：本例假设已读取到文件。')
    print('声明 2：日报已发送。证据：只有发送计划，没有发送回执。')
    print('复核结果：' + finish['verdict'] + ' → 声明 2 缺证据，需要继续核实。')
    print('这里实际验证的是程序分支；本例没有生成日报，也没有发送消息。')


if __name__ == '__main__':
    main()
