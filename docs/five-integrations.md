# 5 个开源组件：让 AI 接得上、结果有依据、老板看得懂

本次集成直接运行上游代码：4 个固定提交的源码子模块，加上固定版本的 json-render 官方包。原有三项 Harness 工具继续可独立使用。

## 各自负责什么？

| 组件 | 本项目实际使用方式 | 已提供的入口 |
|---|---|---|
| [Canny](https://github.com/qkal/Canny) | 调用其真实 ledger 库，记录并汇总执行事实；保留上游 CLI | `python -m integrations.demo`、`kit run canny` |
| [typesafe-mcp](https://github.com/itsmostafa/typesafe-mcp) | 固定源码及校验过 SHA-256 的 v0.4.2 官方二进制，实际启动 MCP 服务 | `upstream_evaluate` |
| [jev-mcp](https://github.com/jkudish/jev-mcp) | 从固定源码及上游 lockfile 安装构建，转接 3 个业务工具 | `business_classify`、`business_verify`、`business_find` |
| [SemDecide](https://github.com/sharziki/semdecide) | 直接调用其 `filter_records`，加上逐条保留、失败与不确定分流；保留原 CLI | `python -m integrations.batch`、`kit run semdecide` |
| [json-render](https://github.com/vercel-labs/json-render) | 使用 0.21.0 的 core/react 包实际渲染受限验收组件 | 本地验收页面 |

确切版本在 [upstream.lock.json](../integrations/upstream.lock.json)。子模块在 GitHub 中显示为指向上游固定提交的目录；下载 ZIP 不包含子模块内容，请使用 Git 克隆。我们新增的适配代码、页面、测试直接位于本仓库，第三方许可见 [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)。

## 第一步：准备 API Key

真实判断先取得 [TypeSafe 官方 Key](https://console.typesafe.ai/keys)，由宿主安全注入环境变量 `TYPESAFE_API_KEY`。不要粘贴到 GitHub、工单或本项目文件中。离线演示不需要 Key。

新增 MCP 组件默认 `HARNESS_JEV_PROVIDER=typesafe`，只向子进程传入该供应商的 Key。若使用 OpenRouter，需要 `HARNESS_JEV_PROVIDER=openrouter` 和 `OPENROUTER_API_KEY`。本适配显式传入 `typesafe/jev-1.13`，避免依赖上游默认别名。OpenRouter Decisions API 为 alpha，普通 chat/completions 中转接口不适用；此路线尚未真实调用验证。

SemDecide 批处理当前仍只走 TypeSafe。原有 `server.py` 三个核心工具也只走 TypeSafe。新组件不会自动读取原核心的 `TYPESAFE_API_KEY_FILE`；请用宿主的凭据机制注入所选环境变量。

## 第二步：安装组件

支持 macOS / Linux（arm64、amd64）；需要 Python 3.11+、Git、Node.js 24+（含 npm）。其他平台尚未验证。所有命令在仓库根目录运行。

```bash
git clone --recurse-submodules https://github.com/Randy0609/agent-jev-harness.git
cd agent-jev-harness
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m integrations.kit setup all
python -m integrations.kit status
```

已经克隆过的用户先更新仓库，再执行 `git submodule update --init --recursive`。也可以只安装单个组件，例如 `python -m integrations.kit setup jev-mcp`。

安装不会执行上游 `setup mcp` 或 Canny `init`，不会修改全局 Codex / Claude 配置。typesafe-mcp 二进制保存在被 Git 忽略的 `.runtime/integrations/`；其归档校验值固定在仓库中。npm 安装禁用依赖生命周期脚本，再显式运行项目构建。Canny 使用上游已提交的 dist；SemDecide 无运行时第三方依赖。

`status` 只显示本地组件是否具备启动条件，不能证明 Key 有效或 API 连通。

## 第三步：先看一个没有网络调用的示例

```bash
python -m integrations.demo
python -m integrations.kit run json-render
```

打开终端显示的本地地址，点击“打开本地 receipt.json”，选择 `artifacts/integrations-demo/receipt.json`。

演示会真的执行两个本地 Python 进程：生成合成日报并核对合计，再由 Canny 库汇总事件台账。SemDecide 使用明确标为 `MOCK-no-network` 的模拟供应商；这部分只验证集成流程，不证明真实模型准确率。页面内置示例也标注为合成数据。

你会看到：

- 产物已生成，模拟金额已核对；
- 真实业务数据覆盖尚缺证据；
- 没有执行发送，也没有目标端回执；
- 批量记录分为匹配、不匹配、待复核。

当前 Canny 演示由我们适配器把已观察到的进程结果写成事实；不是自动拦截所有 Agent 工具。把 JSON 产物变更映射为需重新核验的事件，是该演示的业务适配规则。台账不是防篡改审计系统。

验收页面只显示传入回执，不独立连接业务系统或验证文件真伪。导入文件只在浏览器中解析，不上传到模型服务。

## 第四步：接入 Agent

新增一个独立 MCP 服务，原有服务保留。下面是通用示例；替换路径，并按宿主格式配置。Key 由宿主安全注入，不写入示例。

```json
{
  "mcpServers": {
    "jev-business": {
      "command": "/absolute/path/agent-jev-harness/.venv/bin/python",
      "args": ["-m", "integrations.mcp_server"],
      "cwd": "/absolute/path/agent-jev-harness"
    }
  }
}
```

应发现四个工具：

| 工具 | 用途 | 输入要点 |
|---|---|---|
| `upstream_evaluate` | 通用有限判断 | `state` 对象、`questions` 类型化问题 |
| `business_classify` | 售后等文本分类 | `items: [{id,text}]`、`classes: [{id,description}]`，建议包含人工复核类 |
| `business_verify` | 对照材料核验声明 | `claims` 字符串列表、`evidence` 字符串；不自动查询事实 |
| `business_find` | 从候选中找合适内容 | `query`、`candidates: [{id,text}]`；单独判断是否有匹配 |

所有工具都要求 `data_class=synthetic/public/sanitized`，只允许主动最小化后的内容。声明 sanitized 不是自动脱敏；新组件不会继承原核心的脱敏器。输入总长限制 20 KB，包装层总超时 45 秒，供应商错误正文不会作为工具结果转发。原核心的每日 100 次上限和 DISABLED 标记不覆盖这些可选组件；调用方需另行管理频次与费用，停用时移除该 MCP 配置。

这些新名称避免与原有 `jev_review` 重名。上游的其他工具仍在原源码中，但没有全部暴露给业务 Agent。

## 第五步：运行检查与真实合成调用

```bash
python -m unittest -v
python -m integrations.verify --output artifacts/integrations-offline.json
npm test --prefix integrations/dashboard
```

上面不会调用模型。配置好凭据后，显式运行：

```bash
python -m integrations.verify --live --output artifacts/integrations-live.json
```

TypeSafe 路线下会对 typesafe-mcp、jev-mcp、SemDecide 各发一个合成请求，可能产生费用。OpenRouter 下只检查前两个组件，SemDecide 明确跳过。若出错，修复配置后再接业务材料。

## 实际批量使用：先筛选哪些售后诉求与物流有关

```bash
python -m integrations.batch --live \
  --input examples/logistics.synthetic.jsonl \
  --output artifacts/logistics-results.json \
  --data-class synthetic \
  --criterion '这条诉求是否涉及物流、配送或包裹未收到？'
```

这是物流相关性筛选；多类别分流使用 `business_classify`。批处理输出保留每个原始 ID，分成 `match/no_match/review/provider_error`。失败返回退出码 4；格式问题直接报错。输出只含 ID 和判断，不复制原始文本。默认阈值仅供演示，正式业务须用人工标注样本校准。

保留的原始 CLI 可通过统一入口使用：

```bash
python -m integrations.kit run semdecide -- --help
python -m integrations.kit run canny -- --help
python -m integrations.kit run typesafe-mcp -- --version
```

Canny 的原始 `init` 会配置 hooks，可能额外采集代码差异、指令或命令信息；需要时请先阅读上游隐私说明和作用范围。本项目默认只用其本地台账库，不会替你启用 hooks。

## 验证范围

2026-09-21 本地验证：

- 25 项 Python 测试通过，其中 17 项核心测试、8 项新增边界与集成测试。
- 2 项使用真实 json-render 渲染器的界面测试通过，生产构建通过。
- typesafe-mcp、jev-mcp、四工具桥接服务均完成真实进程的 MCP 握手和工具发现。
- 通过 TypeSafe 官方路线完成 3 个真实合成请求，分别来自两个上游 MCP 及 SemDecide。
- Canny 真正处理本地事件并验证“后续变更使旧检查失效”；浏览器可见验收页面及未送达状态。

CI 重复离线测试，不使用 API Key。OpenRouter、自动 hooks、第三方客户端中的长期运行、真实业务数据与经营效果不在上述验证范围。

## 升级和移除

升级子模块时必须同时更新 gitlink、`upstream.lock.json`、许可和验证记录；不要执行上游自动更新后仍沿用旧验证结论。json-render 更新时提交新的 npm lockfile。

停用时从 Agent 配置移除新增 MCP 服务、关闭本地页面与服务即可；原有核心入口继续可用。运行文件在 `.runtime/` 和 `artifacts/`，从未自动写入业务系统或创建全局 hooks。
