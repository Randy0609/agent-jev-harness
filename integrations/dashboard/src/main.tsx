import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ReceiptView, receiptSchema} from './view';
import sample from './sample.json';
import './style.css';

function App() {
  const [receipt,setReceipt]=useState(receiptSchema.parse(sample));
  const [error,setError]=useState('');
  return <main><header><strong>Agent + JEV Harness</strong><span>任务有边界 · 判断有依据 · 结果可验收</span></header>
    <div className="toolbar"><label>打开本地 receipt.json <input type="file" accept=".json,application/json" onChange={async e=>{
      const file=e.target.files?.[0]; if(!file)return;
      try {if(file.size>1_000_000)throw new Error('oversize');setReceipt(receiptSchema.parse(JSON.parse(await file.text())));setError('');}
      catch{setError('回执格式不符或超过 1 MB；仍显示上一次有效回执。');}
    }}/></label><small>文件在当前浏览器内读取，不上传到模型服务。</small></div>
    {error&&<p role="alert">{error}</p>}<ReceiptView receipt={receipt}/>
    <footer>界面由 json-render 渲染 · 执行台账接入 Canny · 批处理接入 SemDecide</footer></main>;
}
createRoot(document.getElementById('root')!).render(<App/>);
