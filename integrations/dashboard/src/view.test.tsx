import React from 'react';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {renderToStaticMarkup} from 'react-dom/server';
import {ReceiptView, receiptSchema} from './view';
import sample from './sample.json';

test('actual json-render renders facts and keeps unobserved delivery separate',()=>{
 const receipt=receiptSchema.parse(sample);const html=renderToStaticMarkup(<ReceiptView receipt={receipt}/>);
 assert.match(html,/Canny 执行台账/);assert.match(html,/尚缺证据/);assert.match(html,/未执行发送/);
 assert.match(html,/模拟结果/);assert.equal(receipt.sent,false);assert.equal(receipt.target_visible,false);
});
test('untrusted evidence is rendered as text, and invalid states are rejected',()=>{
 const receipt=receiptSchema.parse(sample);receipt.evidence[0].detail='<script>alert(1)</script>';
 const html=renderToStaticMarkup(<ReceiptView receipt={receipt}/>);assert.ok(!html.includes('<script>'));assert.match(html,/&lt;script&gt;/);
 assert.equal(receiptSchema.safeParse({...sample,checked:'yes'}).success,false);
});
