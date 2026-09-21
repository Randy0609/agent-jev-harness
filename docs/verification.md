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

尚未验证：真实企业任务收益、长期概率校准、其他品牌宿主自动加载、Windows、Linux 或 CI 执行。CI 配置包含 Python 3.11–3.13 的离线检查，但没有在远端运行，不将配置文件视为 CI 已通过。

本节记录本地初版的验证结果。公开仓库为 [Randy0609/agent-jev-harness](https://github.com/Randy0609/agent-jev-harness)；远端 CI 结果请查阅仓库 Actions，不以本地测试代替。
