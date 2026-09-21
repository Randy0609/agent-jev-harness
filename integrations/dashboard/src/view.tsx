import React from 'react';
import { z } from 'zod';
import { defineCatalog, type Spec } from '@json-render/core';
import { schema } from '@json-render/react/schema';
import { defineRegistry, Renderer, JSONUIProvider } from '@json-render/react';

export const receiptSchema = z.object({
  schema_version: z.literal(1), data_class: z.enum(['synthetic', 'public', 'sanitized']),
  title: z.string().max(200), generated: z.boolean(), checked: z.boolean(),
  sent: z.boolean(), target_visible: z.boolean(),
  evidence: z.array(z.object({label: z.string().max(200), status: z.enum(['passed', 'failed', 'missing']), detail: z.string().max(2000)})).max(100),
  batch: z.array(z.object({id: z.string().max(100), route: z.enum(['match', 'no_match', 'review', 'provider_error']), probability: z.number().min(0).max(1).nullable()})).max(100),
  batch_model: z.string().max(200)
});
export type Receipt = z.infer<typeof receiptSchema>;
const catalog = defineCatalog(schema, {components: {
  Panel: {props: z.object({title: z.string()}), description: '验收分组'},
  Fact: {props: z.object({label: z.string(), status: z.string(), detail: z.string()}), description: '回执中的一项事实'}
}, actions: {}});
const {registry} = defineRegistry(catalog, {components: {
  Panel: ({props, children}) => <section><h2>{props.title}</h2>{children}</section>,
  Fact: ({props}) => <article className={`fact ${props.status}`}><div><strong>{props.label}</strong><span>{({passed:'已核对',failed:'检查失败',missing:'尚缺证据'} as Record<string,string>)[props.status] ?? props.status}</span></div><p>{props.detail}</p></article>
}});

export function receiptSpec(receipt: Receipt): Spec {
  return {root:'receipt', elements: {
    receipt: {type:'Panel',props:{title:'结果与依据'},children:receipt.evidence.map((_,i)=>`fact${i}`)},
    ...Object.fromEntries(receipt.evidence.map((fact,i)=>[`fact${i}`, {type:'Fact',props:fact}]))
  }};
}

export function ReceiptView({receipt}: {receipt: Receipt}) {
  return <><div className="notice">{receipt.data_class === 'synthetic' ? '合成数据演示 · 不代表真实业务已完成' : '导入回执 · 页面仅展示，未独立核验文件或业务系统'}</div>
    <h1>{receipt.title}</h1><div className="stages">{[
      ['产物生成',receipt.generated],['检查通过',receipt.checked],['发送成功',receipt.sent],['目标可见',receipt.target_visible]
    ].map(([label,done])=><div key={String(label)} className={done?'done':''}><b>{done?'✓':'—'}</b>{label}</div>)}</div>
    <JSONUIProvider registry={registry} initialState={{}} handlers={{}}><Renderer spec={receiptSpec(receipt)} registry={registry}/></JSONUIProvider>
    <section><h2>批量判断 · {receipt.batch_model.startsWith('MOCK')?'模拟结果':'提供方结果'}</h2><p className="muted">不确定与调用失败分别保留。判断结果不会触发发送、退款或其他业务动作。</p>
    <table><thead><tr><th>记录</th><th>处理结果</th><th>概率</th></tr></thead><tbody>{receipt.batch.map(row=><tr key={row.id}><td>{row.id}</td><td>{({match:'匹配',no_match:'不匹配',review:'待复核',provider_error:'调用失败'})[row.route]}</td><td>{row.probability===null?'未知':`${Math.round(row.probability*100)}%`}</td></tr>)}</tbody></table></section>
  </>;
}
