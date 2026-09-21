# v0.1.0 验证记录

日期：2026-09-21。环境：macOS，Python 3.14；在本目录新建虚拟环境安装依赖。原有本机部署没有用于替代本目录代码的验证。

| 检查 | 本次观察 |
|---|---|
| 核心单元测试 | 17 项通过，含异常响应、凭据模式、输入上限、停用、调用额度与缺证据覆盖规则 |
| 离线演示 | 运行通过，返回 needs_work，标记第二条声明缺证据；使用预设响应 |
| 独立依赖安装 | requirements.txt 安装成功；requirements.lock 记录当次完整依赖版本 |
| MCP 本地检查 | 完成 stdio 握手，发现 3 个工具，读到本版本 0.1.0 |
| CLI | 状态读取成功；3 个无效输入以 invalid_input 和退出码 2 拒绝 |
| 真实合成 triage | status=ok，实际模型 jev-1.13.0，建议 implementation |
| 真实合成 review | status=ok，verdict=needs_work，缺证据项为第 2 项；没有误称全部交付 |

两个 API 调用使用仓库的虚构日报案例，不包含真实经营数据。测得 Harness 单次调用耗时为 959ms 和 926ms，包含本地处理和网络等待；仅两个样例，不代表供应商纯推理延迟、稳定性能或相对其他模型的优势。

当次供应商返回：triage 输入 599 / 输出 94 tokens，review 输入 853 / 输出 122 tokens。未核对实际账单，不将这些计数换算成已节省金额。

原始本地调用记录在被忽略的 `artifacts/mcp-live.json`；不随源码压缩包发布。可以运行 `python verify_mcp.py --live --output artifacts/mcp-live.json` 自行复现；之后返回值可能变化。

尚未验证：真实企业任务收益、长期概率校准、其他品牌宿主自动加载、Windows，以及 Linux 上的真实 API / MCP 接入。Linux 上的核心离线测试和演示已通过，见下方公开发布核验。

本节记录本地初版的验证结果。公开仓库为 [Randy0609/agent-jev-harness](https://github.com/Randy0609/agent-jev-harness)；远端 CI 结果请查阅仓库 Actions，不以本地测试代替。

## 公开发布核验

2026-09-21，首个公开提交 `cbf07ef3276f75d87962dbca15327c32659fe603` 已完成以下检查：

- GitHub API 返回仓库可见性为 PUBLIC。
- 从 GitHub 无需登录下载该提交的源码，24 个文件逐一与本地提交内容一致。
- 解压到临时目录后，17 项核心测试和离线演示均通过。
- GitHub Actions 的 Ubuntu 环境中，Python 3.11、3.12、3.13 三组核心测试与离线演示全部成功。[查看该次 CI](https://github.com/Randy0609/agent-jev-harness/actions/runs/35566750815)。

本记录只证明发布文件与所列检查结果，不代表企业业务效果已验证。后续版本的 CI 状态以各自提交关联的运行记录为准。
