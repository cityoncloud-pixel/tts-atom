# Goal (GGS Draft — tts-atom MVP)

> 来源：`project_control/.ggs/idea.md`（GGS 编译，iteration 1）  
> 假设：见 `project_control/.ggs/assumptions.md`

## 1) Intent / 原始意图

为儿童陪伴系统补齐「文字 → 语音」原子能力，构建本地可复用的 `tts-atom` 服务：低延迟、可缓存、Provider 可插拔、支持分句与角色音色配置，供 Companion BFF 调用，并作为云端 TTS 的本地兜底。

## 2) Target Outcome / 目标交付物

交付一个可安装、可本地运行的 Python 包 **`tts-atom`**，具备：

| 类别 | 交付物 |
|------|--------|
| 包结构 | `pyproject.toml`、`tts_atom/`（core、providers、roles、schemas、server、CLI） |
| 运行形态 | CLI（`synth` / `serve` / `voices` / `doctor`）+ FastAPI HTTP 服务（默认 `127.0.0.1:9020`） |
| Provider | `TTSProvider` 抽象 + **MeloTTSProvider**（接入路径/占位）+ **MockProvider**（无模型可测）+ **WindowsSapiProvider** 或等价兜底 |
| HTTP API | `GET /healthz`；`GET /api/tts/providers`；`GET /api/tts/voices`；`POST /api/tts/synthesize`；`POST /api/tts/split-synthesize`；`POST /api/tts/prewarm`；静态 `GET /audio/...` |
| 能力 | 分句、SHA256 缓存、`runs/` 音频输出、统一错误结构、每次合成返回 `timing`、角色配置（`role_id` → 音色/Provider） |
| 文档与配置 | `README.md`、`.env.example`、`tts_atom/assets/prewarm_phrases.zh.json`、`tts_atom/roles/default_roles.json` |
| 测试 | `tests/` 覆盖 healthz、splitter、cache、schemas、mock 合成 |

**不在此阶段交付**：WebSocket 流式、Kokoro/豆包真实接入、Launcher 托管实现、语音克隆、嘴型同步。

## 3) Success Criteria / 成功标准（可验证）

1. **CLI 合成**：`tts-atom synth --text "你好，小警员，我们开始吧。" --json` 返回 `ok=true`，含 `audio_path`、`provider`、`timing`；同参数第二次请求 `cached=true`。
2. **HTTP 健康与合成**：`tts-atom serve --port 9020` 后，`GET http://127.0.0.1:9020/healthz` 返回 `ok=true`；`POST /api/tts/synthesize` 返回可访问的 `audio_url`（可通过浏览器或 `curl` 下载播放）。
3. **分句合成**：对文本「好的，我们先看第一题。5加3等于几呢？你可以先数5个，再数3个。」调用 `POST /api/tts/split-synthesize` 返回 ≥2 个 `segments`，每段含 `text`、`audio_url`、`duration_ms`、`cached`。
4. **自动化测试**：在项目根目录执行 `pytest`（或 `python -m pytest`）全部通过，且包含无真实 MeloTTS 模型时的 mock 合成测试。
5. **架构约束**：CLI 与 HTTP 共用同一套 `core/engine` 逻辑；任意合成失败返回统一 `error` 结构（含 `code`、`source`、`recoverable`）及 `timing`。

## 4) Scope / 范围

### In Scope

- Python 项目骨架与可安装 CLI 入口 `tts-atom`
- Pydantic 请求/响应/错误模型
- Provider 抽象与 `auto` 路由（role → primary → default melotts → fallback → windows_sapi）
- MeloTTS 默认 Provider（含真实接入路径；无模型时 Mock 兜底）
- 缓存（hash key 含 text/provider/voice/语气参数等）、`runs/` 与 `cache/` 目录
- 中文分句（。！？；及 `.!?;`、换行；短句合并、长句二次切分）
- 角色音色配置（`default_roles.json`，至少 `rabbit_officer` 示例）
- 预热 API `/api/tts/prewarm` 与资产话术文件
- `doctor` 诊断命令（Provider 可用性、目录、端口等）
- README：安装、开发启动、API 示例、Companion BFF 接入说明

### Out of Scope

- 儿童陪伴业务逻辑（作业流程、情绪策略、LLM 编排）— 归属 Companion Orchestrator / BFF
- 前端直连 MeloTTS 或 `tts-atom`
- WebSocket 流式音频（MVP）
- Kokoro、Edge、豆包 Provider 的**真实**生产接入（仅预留接口/占位）
- 语音克隆、嘴型同步、多租户账号、云端计费
- Companion Launcher 自动启停（仅文档规划，不实现）
- 商业级儿童动画配音音质保证

## 5) Constraints / 约束

- **语言/框架**：Python 3.10+；FastAPI + Uvicorn；CLI 推荐 Typer（或 argparse，二选一并统一）
- **默认 Provider**：`melotts`；默认语言 `zh`；默认格式 `wav`；采样率 `24000`
- **网络**：HTTP 仅监听 `127.0.0.1`（可配置）；面向本地原子服务，非公网暴露
- **平台**：优先 Windows 10+ 开发与验收；路径与日志需兼容 Windows
- **文本长度**：默认 `TTS_ATOM_MAX_TEXT_LENGTH=1000`（可配置）
- **架构**：`tts-atom` 只做 TTS；禁止写入陪伴场景业务规则
- **可测试性**：无 MeloTTS 权重时，MockProvider 必须使 CI/本地 `pytest` 绿
- **风格**：与 `voice-atom` 类似的本地原子服务模式（CLI + HTTP + healthz）

## 6) Inputs / 输入材料与上下文

- **主输入**：`project_control/.ggs/idea.md`（完整产品/技术规格种子）
- **仓库状态**：绿场；GAEH 脚手架已 `gaeh init`
- **参考关系**：对称于 `voice-atom`（语音→文字）；上游为 Companion BFF，下游为 MeloTTS 等 Provider
- **配置模板**：`idea.md` §17 `.env.example` 字段集

## 7) UI / Interaction Requirements（如涉及 UI）

**不适用（N/A）**。本服务无终端 UI。  
**调用方交互**：Companion BFF 通过 HTTP JSON 调用；开发者通过 CLI。  
**关键 HTTP 行为**：合成返回 `audio_url` 供前端播放队列顺序消费；分句接口支持流式 LLM 场景下的逐句合成。

## 8) Boundary & Edge Cases / 边界与模糊点

| 边界 | 处理 |
|------|------|
| 空文本 | 返回 `TTS_EMPTY_TEXT`，`ok=false` |
| 超长文本 | 返回 `TTS_TEXT_TOO_LONG` 或截断策略（需在实现 spec 中二选一，默认拒绝） |
| Provider 不可用 | `auto` 链式 fallback；最终失败返回 `TTS_PROVIDER_FAILED` 及已尝试 source |
| 无 MeloTTS 模型 | MockProvider 用于测试；生产由 Owner 配置模型路径 |
| `emotion` 不支持 | 映射为 speed/pitch/volume（见 idea §9.2） |
| 数学表达式分句 | 避免在数字与运算符中间切断；MVP 以标点为主，复杂规则可迭代 |
| 缓存一致性 | key 必须包含语气与 format 参数，避免错误命中 |
| BFF 超时 | `tts-atom` 返回明确错误与 `timing`；BFF 侧超时策略不在本仓库实现 |
| 权限 | 本地服务，无认证；不面向公网 |

## 9) Output Format / 输出格式

```
tts-atom/
  pyproject.toml
  README.md
  .env.example
  tts_atom/          # 包源码（见 idea §6 目录树）
  tests/
  runs/              # 运行时音频（gitkeep）
  cache/             # 缓存（gitkeep）
  models/            # 模型目录占位（gitkeep）
```

**可运行命令（验收用）**：

```bash
pip install -e ".[dev]"
pytest
tts-atom doctor --json
tts-atom synth --text "你好，小警员" --json
tts-atom serve --host 127.0.0.1 --port 9020
```

## 10) Risks / 风险与未知

1. **MeloTTS 中文童声音色**需实机试听，可能需 Phase 2 调参或引入云端豆包作表演音。
2. **Windows 与 MeloTTS 依赖**安装复杂度未知，可能影响首次 `doctor` 通过率。
3. **本地 TTS 音质 vs 云端**：策略为本地快+兜底、云端高质量，MVP 不解决音质争议。
4. **Launcher 托管**未在本阶段实现，正式交付仍依赖手动 `serve` 或后续迭代。
5. **假设依赖**：见 `assumptions.md` A-0001～A-0007；若 Companion BFF 接口字段与 idea 不一致，需 CR 更新 goal。

## 11) Approval Policy / 同意门禁（Owner 决策）

目标清晰后，AI **必须先征得 Owner 同意**再开始连续实现：

- 对话回复：`APPROVE`（或 `APPROVE <task_id>`）
- 或更新：`project_control/approval.json` 中 `start_execution` → `APPROVED`

未同意前：仅允许 Spec / Plan / 风险澄清，不进行大规模实现（除非 Owner 授权 Tiny Fix）。

## 12) Execution Handoff / 给 GAEH 的执行指令

请基于本 `goal.md` 进入 GAEH 流程：**Spec → Plan → Review → 等待 APPROVE → Execute → Verify → Report**。

推荐种子任务（与 `idea.md` §22 一致）：

1. 项目骨架 + pyproject + CLI 入口  
2. Schemas + 统一错误 + timing  
3. MockProvider + 全链路测试  
4. 缓存 + audio_store + `/audio` 静态路由  
5. FastAPI 端点（healthz → synthesize → split → prewarm）  
6. 分句 splitter + 角色配置  
7. MeloTTSProvider 真实接入路径  
8. README + `.env.example` + BFF 接入说明  

推荐路由：**spec_first**（Normal）；预估多阶段，先 Mock 绿再换真实 Provider。
