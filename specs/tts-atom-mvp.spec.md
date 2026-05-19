# Spec: tts-atom MVP (v0.1.0)

| 字段 | 值 |
|------|-----|
| Task ID | `tts-atom-mvp-0001` |
| Route | B — Normal (`spec_first`) |
| Goal | `project_control/goal.md` |
| Status | DRAFT — 待 Owner `APPROVE` 后执行 |
| 详细种子 | `project_control/.ggs/idea.md` |

---

## 1. 系统上下文

```text
Companion BFF  ──HTTP──►  tts-atom (127.0.0.1:9020)
                              │
                    TTSProvider Router
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   MeloTTSProvider    MockProvider (dev/test)   WindowsSapiProvider
```

- **对称能力**：`voice-atom`（ASR）↔ `tts-atom`（TTS）。
- **职责边界**：仅文本→音频；不含陪伴业务、LLM、前端播放逻辑。
- **调用约束**：前端不直连；BFF 调用 HTTP JSON API。

---

## 2. 包与目录结构

```
tts-atom/                          # 仓库根（当前 workspace）
  pyproject.toml                   # 包名 tts-atom, console_scripts: tts-atom
  README.md
  .env.example
  .gitignore
  tts_atom/
    __init__.py                    # __version__
    main.py                        # Typer CLI
    server.py                      # FastAPI app factory + uvicorn entry
    config.py                      # pydantic-settings / env
    schemas.py                     # 请求/响应/错误 Pydantic 模型
    errors.py                      # 错误码常量 + 工厂函数
    logging_config.py
    core/
      engine.py                    # 合成编排（唯一业务入口）
      router.py                    # provider 选择与 fallback
      splitter.py                  # 分句
      cache.py                     # SHA256 缓存读写
      audio_store.py               # runs/ 写入 + audio_url 生成
      prewarm.py                   # 批量预热
      timing.py                    # TimingCollector
    providers/
      base.py                      # TTSProvider ABC
      mock_provider.py
      melotts_provider.py          # 真实接入 + 不可用时的明确状态
      windows_sapi_provider.py     # Windows 兜底（不可用则跳过）
      kokoro_provider.py           # 占位：is_available=False
      edge_provider.py             # 占位
      doubao_provider.py           # 占位
    roles/
      role_profiles.py             # 加载 default_roles.json
      default_roles.json
    assets/
      prewarm_phrases.zh.json
  tests/
  runs/ .gitkeep
  cache/ .gitkeep
  models/ .gitkeep
```

---

## 3. 配置（环境变量）

| 变量 | 默认 | 说明 |
|------|------|------|
| `TTS_ATOM_HOST` | `127.0.0.1` | HTTP bind |
| `TTS_ATOM_PORT` | `9020` | HTTP port |
| `TTS_ATOM_DEFAULT_PROVIDER` | `melotts` | 系统默认 |
| `TTS_ATOM_DEFAULT_LANGUAGE` | `zh` | |
| `TTS_ATOM_AUDIO_ROOT` | `./runs` | 运行时输出 |
| `TTS_ATOM_CACHE_ROOT` | `./cache` | 缓存根 |
| `TTS_ATOM_MODELS_ROOT` | `./models` | MeloTTS 模型路径 |
| `TTS_ATOM_ENABLE_CACHE` | `true` | |
| `TTS_ATOM_MAX_TEXT_LENGTH` | `1000` | 超长拒绝 |
| `TTS_ATOM_DEFAULT_FORMAT` | `wav` | |
| `TTS_ATOM_DEFAULT_SAMPLE_RATE` | `24000` | |
| `TTS_ATOM_LOG_LEVEL` | `INFO` | |
| `TTS_ATOM_FORCE_MOCK` | `false` | `true` 时强制 Mock（测试用） |

---

## 4. Provider 抽象

### 4.1 接口

```python
class TTSProvider(ABC):
    name: str
    def is_available(self) -> bool: ...
    def list_voices(self, language: str | None = None) -> list[VoiceInfo]: ...
    def synthesize(self, request: TTSRequest) -> TTSProviderResult: ...
```

`TTSProviderResult`: `audio_bytes`, `duration_ms`, `provider`, `voice`, 可选 `metadata`.

### 4.2 路由（`provider=auto`）

1. `role_id` → `default_roles.json` → `primary_provider`
2. 请求显式 `provider`（若非 `auto`）
3. `TTS_ATOM_DEFAULT_PROVIDER`（`melotts`）
4. role 的 `fallback_provider`
5. `windows_sapi`（若 `is_available()`）
6. `mock`（仅当 `TTS_ATOM_FORCE_MOCK=true` 或 dev 模式；**不**作为生产 silent fallback）
7. 失败 → `TTS_PROVIDER_FAILED`，`details.attempted: string[]`

**合成失败链**（同一请求内）：primary → fallback → windows_sapi → 错误。

### 4.3 MockProvider

- 生成最短合法 WAV（静音或 440Hz 短 beep，实现选一种并固定）。
- `is_available()` 恒为 `true`。
- 用于 `pytest` 与无 MeloTTS 权重的本地开发。

### 4.4 MeloTTSProvider

- `is_available()`：检测模型路径/可选依赖 import。
- 不可用时：**不**自动顶替为 Mock（除非 `FORCE_MOCK`）；路由落到 fallback / 错误。
- 实现文件内注释说明模型安装步骤（README 链接）。

### 4.5 占位 Provider

`kokoro`, `edge`, `doubao`：`is_available() -> False`，`list_voices` 返回空；`/healthz` 与 `/api/tts/providers` 反映 `available: false`。

---

## 5. 核心模块行为

### 5.1 `core/engine.py`（CLI 与 HTTP 共用）

`Engine.synthesize(req) -> SynthesizeResponse`  
`Engine.split_synthesize(req) -> SplitSynthesizeResponse`  
`Engine.prewarm(req) -> PrewarmResponse`  
`Engine.list_providers() / list_voices(...)`

流程（单次合成）：

1. 校验 `text` 非空、长度 ≤ max
2. 解析 `role_id` → 合并默认 voice/provider/speed/pitch/volume/emotion
3. `emotion` → speed/pitch/volume 映射表（idea §9.2）
4. 计算 cache key → 命中则返回（`cached=true`）
5. `router.resolve_provider` → `provider.synthesize`
6. `audio_store.save` → `audio_path` + `audio_url`
7. 填充 `timing`（`cache_lookup_ms`, `synthesis_ms`, `file_write_ms`, `total_ms`）

### 5.2 缓存 key

```text
sha256(normalize(text) + "|" + provider + "|" + voice + "|" + language
       + "|" + emotion + "|" + speed + "|" + pitch + "|" + volume
       + "|" + format + "|" + sample_rate)
```

路径：`{CACHE_ROOT}/{provider}/{voice}/{hash}.{format}`

### 5.3 分句 `splitter.py`

- 分隔符：`。！？；` `.!?;` 及换行。
- 过短片段（< N 字符，默认 4）与下一句合并。
- 过长单句（> M 字符，默认 80）在逗号/空格处二次切分。
- 数字+运算符连续段不从中切断（简单正则保护 `[\d+\-*/=]+`）。

### 5.4 角色配置 `default_roles.json`

至少一条：

```json
{
  "role_id": "rabbit_officer",
  "display_name": "兔子警官",
  "tts_profile": {
    "primary_provider": "melotts",
    "fallback_provider": "windows_sapi",
    "voice": "zh_female_01",
    "language": "zh",
    "speed": 1.06,
    "pitch": 1.04,
    "volume": 1.0,
    "emotion_default": "cheerful"
  }
}
```

请求仅 `{ "role_id", "text" }` 时，由 engine 补全其余字段。

---

## 6. HTTP API

Base: `http://{host}:{port}`  
Content-Type: `application/json`  
错误：HTTP 4xx/5xx + body 统一 `{ "ok": false, "error": {...}, "timing": {...} }`

### 6.1 `GET /healthz`

```json
{
  "ok": true,
  "service": "tts-atom",
  "version": "0.1.0",
  "default_provider": "melotts",
  "providers": { "melotts": true, "mock": true, "kokoro": false, ... }
}
```

### 6.2 `GET /api/tts/providers`

返回 providers 列表（name, available, local, default, supports, features）。

### 6.3 `GET /api/tts/voices`

Query: `provider`, `language`, `role_id`（可选）。

### 6.4 `POST /api/tts/synthesize`

Request/Response 字段对齐 `idea.md` §8.4（`ok`, `provider`, `voice`, `role_id`, `audio_url`, `audio_path`, `format`, `sample_rate`, `duration_ms`, `cached`, `segments`, `timing`, `error`）。

`audio_url` 形如 `/audio/2026-05-19/{hash}.wav`。

### 6.5 `POST /api/tts/split-synthesize`

返回 `segments[]`：`index`, `text`, `audio_url`, `audio_path`, `duration_ms`, `cached`；顶层 `timing.split_ms`。

### 6.6 `POST /api/tts/prewarm`

批量合成短语列表；返回 `created`, `cached`, `failed`, `items[]`。

### 6.7 静态文件 `GET /audio/{path}`

挂载 `AUDIO_ROOT` 与 `CACHE_ROOT`（cache 子路径映射为 `/audio/cache/...`）。

---

## 7. CLI

| 命令 | 说明 |
|------|------|
| `tts-atom synth --text ... [--voice] [--role-id] [--provider] [--json]` | 单次合成 |
| `tts-atom speak TEXT` | synth + 系统播放（Windows 可选，失败仅警告） |
| `tts-atom serve [--host] [--port]` | 启动 Uvicorn |
| `tts-atom voices [--json] [--provider]` | 列出音色 |
| `tts-atom doctor [--json]` | 目录、配置、各 Provider 可用性 |
| `tts-atom cache clear [--provider]` | 清缓存（MVP） |

---

## 8. 错误码

| Code | HTTP | recoverable |
|------|------|-------------|
| `TTS_EMPTY_TEXT` | 400 | false |
| `TTS_TEXT_TOO_LONG` | 400 | false |
| `TTS_PROVIDER_NOT_FOUND` | 400 | false |
| `TTS_PROVIDER_UNAVAILABLE` | 503 | true |
| `TTS_PROVIDER_FAILED` | 502 | true |
| `TTS_VOICE_NOT_FOUND` | 400 | false |
| `TTS_UNSUPPORTED_FORMAT` | 400 | false |
| `TTS_AUDIO_WRITE_FAILED` | 500 | false |
| `TTS_CACHE_ERROR` | 500 | true |
| `TTS_INTERNAL_ERROR` | 500 | false |

`error` 对象：`code`, `message`, `source`, `recoverable`, `details`.

---

## 9. 依赖（pyproject.toml）

**Runtime**: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `typer`, `python-multipart`  
**Dev**: `pytest`, `httpx`, `pytest-asyncio`（若测 async client）

**Optional** `[melotts]`: 文档说明手动安装；不在默认 dev 依赖中强制。

---

## 10. 测试策略

| 文件 | 覆盖 |
|------|------|
| `test_schemas.py` | 模型校验、emotion 映射 |
| `test_splitter.py` | 中文多句、短句合并、数学片段 |
| `test_cache.py` | key 稳定、命中/未命中 |
| `test_synthesize_mock.py` | Engine + MockProvider，无模型 |
| `test_healthz.py` | TestClient `/healthz`, `/api/tts/synthesize` |

测试环境：`TTS_ATOM_FORCE_MOCK=true` 或默认 dev 配置指向 mock。

---

## 11. 验收矩阵（↔ goal Success Criteria）

| ID | Goal 标准 | 验证方式 |
|----|-----------|----------|
| SC-1 | CLI synth + cache | `tts-atom synth ... --json` ×2 |
| SC-2 | HTTP health + synthesize | `serve` + curl healthz + POST synthesize + GET audio_url |
| SC-3 | split-synthesize ≥2 segments | POST 固定长文本 |
| SC-4 | pytest 全绿 | `pytest -q` |
| SC-5 | CLI/HTTP 共用 engine | 代码审查 + 集成测试同一 Engine 实例 |

---

## 12. 明确排除（Spec 级）

- WebSocket 流式、`stream=true` 的真实流实现
- Kokoro/Edge/豆包真实合成
- Companion Launcher 进程管理
- HTTP 认证 / HTTPS 终止
- 业务 metadata 的解释与存储（仅透传字段）

---

## 13. 开放项（不阻塞 APPROVE）

| 项 | 决策 |
|----|------|
| CLI 框架 | **Typer**（goal 推荐） |
| Mock 音频 | 静音 WAV 100ms @ 24kHz |
| `speak` 命令 | Windows 用 `winsound`；其他平台打印 path 提示 |
| 超长文本 | **拒绝**（`TTS_TEXT_TOO_LONG`），不截断 |
