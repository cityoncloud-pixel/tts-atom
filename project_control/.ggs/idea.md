# Idea

# TTS-ATOM 项目 Idea / Goal Seed

> 项目名称：`tts-atom`  
> 项目定位：本地文本转语音原子服务，用于儿童陪伴系统的角色语音输出，也可被其他项目复用。  
> 默认 Provider：MeloTTS  
> 可扩展 Provider：Kokoro、Edge TTS、Windows SAPI、豆包/火山 TTS 等  
> 推荐实现形态：CLI + HTTP API + 可被父进程托管的本地服务

---

## 1. 背景

当前儿童陪伴系统已经开始接入语音输入能力，例如 `voice-atom`，用于完成“语音 → 文字”的 ASR 原子能力。下一步需要补齐“文字 → 语音”的输出能力，让角色能够稳定、低延迟、可控地对孩子说话。

目前使用 Edge TTS 或类似云端 TTS 时，可能存在以下问题：

1. 首字延迟高；
2. 网络依赖强；
3. 代理、DNS、服务状态会影响体验；
4. 长文本必须等 LLM 完整返回后再合成，导致孩子等待时间长；
5. 无法很好地做本地缓存、角色音色配置、服务健康检查和统一降级。

因此需要构建一个本地 TTS 原子服务：`tts-atom`。

它不是一个单纯的 MeloTTS 脚本，而是一个可复用、可托管、可切换 Provider 的 TTS 服务层。儿童陪伴系统不直接绑定 MeloTTS，而是统一调用 `tts-atom`，由 `tts-atom` 决定使用 MeloTTS、Kokoro、Edge、Windows SAPI 或其他 Provider。

---

## 2. 项目核心目标

构建一个本地文本转语音原子服务 `tts-atom`，为儿童陪伴系统提供低延迟、可缓存、可切换 Provider、可按角色配置音色、可分句朗读的 TTS 能力。

核心目标包括：

1. 支持本地 TTS，默认使用 MeloTTS；
2. Provider 可插拔，后续可接入 Kokoro、Edge TTS、Windows SAPI、豆包/火山 TTS；
3. 同时提供 CLI 和 HTTP API；
4. 能被儿童陪伴系统的 Companion BFF 调用；
5. 能被 Companion Launcher 自动启动、健康检查和关闭；
6. 支持分句合成与播放队列友好返回；
7. 支持常用话术预热和缓存；
8. 支持角色音色配置，例如兔子警官、辅助角色、旁白角色等；
9. 返回清晰的 timing 信息，帮助判断慢在哪里；
10. 能作为云端 TTS 的本地 fallback，也能作为默认 TTS 服务运行。

---

## 3. 非目标 / 暂不做内容

第一阶段不要把项目做得过重。以下内容暂不作为 MVP 必须目标：

1. 不做复杂语音克隆；
2. 不做实时全双工语音对话；
3. 不做嘴型同步；
4. 不做复杂动作编排；
5. 不做多租户账号系统；
6. 不做云端计费系统；
7. 不要求第一版支持所有 Provider；
8. 不要求第一版音色达到商业儿童动画配音级别；
9. 不要求 WebSocket 流式音频作为第一阶段必需功能；
10. 不把 TTS 业务逻辑、角色陪伴逻辑、作业流程逻辑混入 `tts-atom`。

`tts-atom` 的职责是：**把文本稳定、快速、可控地转成音频**。  
角色对话、学习流程、番茄钟、作业陪伴、情绪策略等属于儿童陪伴系统的 Companion Orchestrator / BFF。

---

## 4. 系统定位

### 4.1 与 voice-atom 的关系

```text
voice-atom: 语音 → 文字
           用于听孩子/用户说话

tts-atom:   文字 → 语音
           用于让角色对孩子说话
```

两者是儿童陪伴系统语音闭环的两个基础原子能力。

### 4.2 与儿童陪伴系统的关系

推荐调用关系：

```text
儿童陪伴前端
    ↓
Companion BFF / Orchestrator
    ↓
TTS Router
    ↓
tts-atom
    ├── MeloTTSProvider
    ├── KokoroProvider
    ├── EdgeTTSProvider
    ├── WindowsSapiProvider
    └── DoubaoTTSProvider
```

前端不直接调用 MeloTTS。  
前端也不直接调用 `tts-atom`。  
前端只调用 Companion BFF。  
Companion BFF 负责调用 `tts-atom`。

这样可以保持：

1. 原子能力独立；
2. 业务系统统一编排；
3. 前端逻辑干净；
4. Provider 可替换；
5. 后续部署、日志、fallback 更容易管理。

---

## 5. 推荐技术栈

### 5.1 后端语言

推荐：Python

原因：

1. MeloTTS / Kokoro / Piper / sherpa-onnx 等 TTS 生态更容易接入；
2. FastAPI 适合快速封装本地 HTTP 服务；
3. 便于和现有 `voice-atom` 保持一致；
4. 便于在 CLI、HTTP、服务托管之间复用核心逻辑。

### 5.2 HTTP 框架

推荐：FastAPI + Uvicorn

### 5.3 CLI

推荐：Typer 或 argparse

命令形态建议：

```bash
tts-atom synth --text "你好，小警员" --voice zh_female_01 --json

tts-atom speak "你好，小警员"

tts-atom serve --host 127.0.0.1 --port 9020

tts-atom voices --json

tts-atom doctor --json
```

### 5.4 默认 Provider

默认 Provider：MeloTTS

原因：

1. 明确支持中文；
2. 适合先作为中文本地 TTS 基线；
3. 可用于儿童陪伴系统的本地语音输出；
4. 作为默认实现比直接绑定云端服务更稳定。

### 5.5 可选 Provider

预留以下 Provider：

```text
MeloTTSProvider      默认本地 Provider
KokoroProvider       轻量本地 Provider，可后续评估中文效果
EdgeTTSProvider      在线高质量 Provider，可作为可选云端/半云端方案
WindowsSapiProvider  Windows 本地兜底 Provider
DoubaoTTSProvider    高质量中文云端 Provider，可用于角色表演语音
```

---

## 6. 项目目录结构建议

```text
tts-atom/
  README.md
  pyproject.toml
  .env.example
  .gitignore

  tts_atom/
    __init__.py
    main.py                  # CLI 入口
    server.py                # FastAPI app
    config.py                # 配置读取
    schemas.py               # Pydantic 请求/响应模型
    errors.py                # 统一错误结构
    logging_config.py

    core/
      engine.py              # TTS 核心调度
      router.py              # provider 选择逻辑
      splitter.py            # 分句逻辑
      cache.py               # 缓存逻辑
      audio_store.py         # 音频文件保存和 URL 映射
      prewarm.py             # 预热逻辑
      timing.py              # timing 统计

    providers/
      base.py                # TTSProvider 抽象类
      melotts_provider.py
      kokoro_provider.py
      edge_provider.py
      windows_sapi_provider.py
      doubao_provider.py

    roles/
      role_profiles.py       # 角色音色配置
      default_roles.json

    assets/
      prewarm_phrases.zh.json

  runs/
    .gitkeep

  cache/
    .gitkeep

  models/
    .gitkeep

  tests/
    test_healthz.py
    test_splitter.py
    test_cache.py
    test_schemas.py
    test_synthesize_mock.py
```

---

## 7. 运行形态要求

`tts-atom` 必须支持三种运行形态。

### 7.1 CLI 一次式

用于脚本、Codex、Cursor、Hermes、GAEH 调用。

示例：

```bash
tts-atom synth --text "太棒了，小警员！" --voice zh_female_01 --json
```

输出：

```json
{
  "ok": true,
  "provider": "melotts",
  "voice": "zh_female_01",
  "audio_path": "runs/2026-05-19/abc123.wav",
  "duration_ms": 1420,
  "cached": false,
  "timing": {
    "queue_ms": 0,
    "synthesis_ms": 430,
    "file_write_ms": 18,
    "total_ms": 448
  },
  "error": null
}
```

### 7.2 HTTP 服务式

用于 Companion BFF 调用。

示例：

```bash
tts-atom serve --host 127.0.0.1 --port 9020
```

### 7.3 被父进程托管式

用于未来 Companion Launcher 托管：

```text
companion-launcher
    ├── 启动 tts-atom
    ├── 检查 /healthz
    ├── 发现挂掉后重启
    └── 主程序退出时关闭 tts-atom
```

要求：

1. 支持固定端口；
2. 支持环境变量配置；
3. 支持健康检查；
4. 支持静默启动；
5. 支持日志文件输出；
6. 支持优雅关闭。

---

## 8. HTTP API 设计

### 8.1 健康检查

```http
GET /healthz
```

响应：

```json
{
  "ok": true,
  "service": "tts-atom",
  "version": "0.1.0",
  "default_provider": "melotts",
  "providers": {
    "melotts": true,
    "kokoro": false,
    "edge": false,
    "windows_sapi": true
  }
}
```

---

### 8.2 Provider 列表

```http
GET /api/tts/providers
```

响应：

```json
{
  "ok": true,
  "providers": [
    {
      "name": "melotts",
      "available": true,
      "local": true,
      "default": true,
      "supports": ["zh", "en", "mixed_zh_en"],
      "features": ["speed", "speaker", "cache"]
    },
    {
      "name": "kokoro",
      "available": false,
      "local": true,
      "default": false,
      "supports": ["en", "zh"],
      "features": ["speed", "cache"]
    }
  ]
}
```

---

### 8.3 音色列表

```http
GET /api/tts/voices
```

可选参数：

```text
provider=melotts
language=zh
role_id=rabbit_officer
```

响应：

```json
{
  "ok": true,
  "voices": [
    {
      "voice": "zh_female_01",
      "provider": "melotts",
      "language": "zh",
      "gender": "female",
      "description": "中文女声，适合作为儿童陪伴默认音色",
      "recommended_roles": ["rabbit_officer", "assistant", "narrator"]
    }
  ]
}
```

---

### 8.4 单次合成

```http
POST /api/tts/synthesize
```

请求字段：

```json
{
  "text": "太棒了，小警员！我们继续下一题。",
  "role_id": "rabbit_officer",
  "voice": "zh_female_01",
  "provider": "auto",
  "language": "zh",
  "emotion": "cheerful",
  "speed": 1.05,
  "pitch": 1.02,
  "volume": 1.0,
  "format": "wav",
  "sample_rate": 24000,
  "cache": true,
  "stream": false,
  "sentence_split": false,
  "return_segments": false,
  "metadata": {
    "scene": "homework_focus",
    "mode": "encourage",
    "request_id": "req_xxx",
    "user_id": "local_child"
  }
}
```

响应字段：

```json
{
  "ok": true,
  "provider": "melotts",
  "voice": "zh_female_01",
  "role_id": "rabbit_officer",
  "audio_url": "/audio/2026-05-19/abc123.wav",
  "audio_path": "runs/2026-05-19/abc123.wav",
  "format": "wav",
  "sample_rate": 24000,
  "duration_ms": 2380,
  "cached": false,
  "segments": [],
  "timing": {
    "queue_ms": 3,
    "synthesis_ms": 420,
    "file_write_ms": 20,
    "total_ms": 443
  },
  "error": null
}
```

---

### 8.5 分句合成

```http
POST /api/tts/split-synthesize
```

请求：

```json
{
  "text": "好的，我们先看第一题。5加3等于几呢？你可以先数5个，再数3个。",
  "role_id": "rabbit_officer",
  "provider": "auto",
  "voice": "zh_female_01",
  "language": "zh",
  "emotion": "gentle",
  "speed": 1.05,
  "format": "wav",
  "cache": true,
  "return_segments": true
}
```

响应：

```json
{
  "ok": true,
  "provider": "melotts",
  "voice": "zh_female_01",
  "role_id": "rabbit_officer",
  "segments": [
    {
      "index": 0,
      "text": "好的，我们先看第一题。",
      "audio_url": "/audio/2026-05-19/seg001.wav",
      "audio_path": "runs/2026-05-19/seg001.wav",
      "duration_ms": 1500,
      "cached": false
    },
    {
      "index": 1,
      "text": "5加3等于几呢？",
      "audio_url": "/audio/2026-05-19/seg002.wav",
      "audio_path": "runs/2026-05-19/seg002.wav",
      "duration_ms": 1200,
      "cached": false
    },
    {
      "index": 2,
      "text": "你可以先数5个，再数3个。",
      "audio_url": "/audio/2026-05-19/seg003.wav",
      "audio_path": "runs/2026-05-19/seg003.wav",
      "duration_ms": 2100,
      "cached": false
    }
  ],
  "timing": {
    "split_ms": 2,
    "synthesis_ms": 980,
    "file_write_ms": 41,
    "total_ms": 1023
  },
  "error": null
}
```

---

### 8.6 预热常用话术

```http
POST /api/tts/prewarm
```

请求：

```json
{
  "role_id": "rabbit_officer",
  "provider": "auto",
  "voice": "zh_female_01",
  "language": "zh",
  "phrases": [
    "太棒了！",
    "我们继续。",
    "没关系，我们再试一次。",
    "小警员，请集中注意力。",
    "做完这一题，我们就休息一下。"
  ]
}
```

响应：

```json
{
  "ok": true,
  "created": 5,
  "cached": 0,
  "failed": 0,
  "items": [
    {
      "text": "太棒了！",
      "audio_url": "/audio/cache/xxx.wav",
      "cached": false
    }
  ]
}
```

---

## 9. 核心请求字段说明

### 9.1 必备字段

| 字段 | 类型 | 说明 |
|---|---|---|
| text | string | 待合成文本 |
| provider | string | `auto` / `melotts` / `kokoro` / `edge` / `windows_sapi` / `doubao` |
| voice | string | 具体音色 ID |
| role_id | string | 角色 ID，例如 `rabbit_officer` |
| language | string | `zh` / `en` / `mixed_zh_en` |
| format | string | `wav` / `mp3` / `ogg` / `pcm` |
| cache | bool | 是否启用缓存 |

### 9.2 语气控制字段

| 字段 | 类型 | 说明 |
|---|---|---|
| emotion | string | 情绪标签 |
| speed | float | 语速倍率 |
| pitch | float | 音高倍率或抽象参数 |
| volume | float | 音量倍率 |

推荐 emotion：

```text
cheerful   鼓励、开心
gentle     温柔、安抚
serious    规则提醒
thinking   思考中
praise     表扬
warning    轻微提醒
neutral    默认中性
```

第一阶段如果底层 Provider 不支持真实 emotion，可以将 emotion 映射为 speed / pitch / volume / pause。

示例：

```json
{
  "cheerful": { "speed": 1.08, "pitch": 1.05, "volume": 1.0 },
  "gentle":   { "speed": 0.95, "pitch": 0.98, "volume": 0.95 },
  "serious":  { "speed": 0.92, "pitch": 0.95, "volume": 1.0 },
  "praise":   { "speed": 1.12, "pitch": 1.08, "volume": 1.0 },
  "warning":  { "speed": 0.95, "pitch": 0.96, "volume": 1.0 }
}
```

### 9.3 性能与播放字段

| 字段 | 类型 | 说明 |
|---|---|---|
| sentence_split | bool | 是否分句 |
| return_segments | bool | 是否返回分段音频 |
| stream | bool | 是否请求流式输出，MVP 可先不实现 |
| sample_rate | int | 采样率，例如 24000 |
| metadata | object | 调用方上下文 |

---

## 10. 角色音色配置

不要让儿童陪伴系统到处写具体 voice 名称。应该支持角色配置。

示例：

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

儿童陪伴系统可以只传：

```json
{
  "role_id": "rabbit_officer",
  "text": "小警员，我们开始吧！"
}
```

`tts-atom` 负责根据 `role_id` 查找对应音色、Provider 和默认语气参数。

---

## 11. Provider 抽象设计

### 11.1 统一接口

```python
class TTSProvider:
    name: str

    def is_available(self) -> bool:
        ...

    def list_voices(self) -> list[VoiceInfo]:
        ...

    def synthesize(self, request: TTSRequest) -> TTSProviderResult:
        ...
```

### 11.2 Provider 选择逻辑

当 `provider = auto` 时，按以下顺序选择：

```text
1. role_id 对应的 primary_provider
2. 系统默认 provider：melotts
3. fallback_provider
4. windows_sapi
5. 返回明确错误
```

### 11.3 Provider fallback 要求

如果 MeloTTS 合成失败：

```text
MeloTTSProvider failed
    ↓
KokoroProvider if available
    ↓
WindowsSapiProvider if available
    ↓
error
```

错误必须包含：

```json
{
  "code": "TTS_PROVIDER_FAILED",
  "message": "MeloTTS synthesis failed",
  "source": "melotts",
  "recoverable": true,
  "details": {}
}
```

---

## 12. 缓存设计

### 12.1 缓存目标

儿童陪伴系统会大量重复短句：

```text
太棒了！
我们继续。
没关系，我们再试一次。
小警员，请集中注意力。
做完这一题，我们就休息一下。
```

这些话术应该预热并缓存，避免每次重新合成。

### 12.2 缓存 key

缓存 key 必须包含：

```text
text
provider
voice
language
emotion
speed
pitch
volume
format
sample_rate
```

推荐：

```text
sha256(normalized_text + provider + voice + language + emotion + speed + pitch + volume + format + sample_rate)
```

### 12.3 缓存目录

```text
cache/
  melotts/
    zh_female_01/
      <hash>.wav
```

### 12.4 缓存策略

MVP：

1. 命中缓存直接返回；
2. 不做复杂淘汰；
3. 提供 `tts-atom cache clear` 命令；
4. 提供缓存大小统计。

后续：

1. 最大缓存容量；
2. LRU 清理；
3. 按角色清理；
4. 按日期清理。

---

## 13. 分句策略

### 13.1 为什么必须分句

儿童陪伴系统需要低延迟。不能等 LLM 生成完整长段后再合成完整音频。

推荐流程：

```text
LLM 流式返回
    ↓
按标点切句
    ↓
每句送入 tts-atom
    ↓
前端播放队列依次播放
```

### 13.2 中文分句标点

至少支持：

```text
。！？；
.
!
?
;
换行
```

### 13.3 分句约束

1. 太短的碎片可合并；
2. 太长的句子需要二次切分；
3. 数学表达不要乱切；
4. 括号动作说明可由上游处理，MVP 不强制。

---

## 14. 音频文件管理

### 14.1 输出目录

```text
runs/
  2026-05-19/
    abc123.wav
    seg001.wav
```

### 14.2 静态访问

HTTP 服务需要暴露音频文件：

```text
/audio/2026-05-19/abc123.wav
/audio/cache/xxx.wav
```

### 14.3 文件命名

推荐使用：

```text
日期 + hash + segment_index
```

避免中文文件名和特殊字符。

---

## 15. 统一错误结构

所有 API 错误必须使用统一结构：

```json
{
  "ok": false,
  "error": {
    "code": "TTS_PROVIDER_FAILED",
    "message": "MeloTTS synthesis failed",
    "source": "melotts",
    "recoverable": true,
    "details": {
      "provider": "melotts"
    }
  },
  "timing": {
    "total_ms": 231
  }
}
```

推荐错误码：

```text
TTS_EMPTY_TEXT
TTS_TEXT_TOO_LONG
TTS_PROVIDER_NOT_FOUND
TTS_PROVIDER_UNAVAILABLE
TTS_PROVIDER_FAILED
TTS_VOICE_NOT_FOUND
TTS_UNSUPPORTED_FORMAT
TTS_AUDIO_WRITE_FAILED
TTS_CACHE_ERROR
TTS_INTERNAL_ERROR
```

---

## 16. Timing 观测要求

每次请求必须返回 timing 信息，便于判断慢在哪里。

字段建议：

```json
{
  "timing": {
    "queue_ms": 3,
    "split_ms": 2,
    "cache_lookup_ms": 1,
    "synthesis_ms": 420,
    "file_write_ms": 20,
    "total_ms": 446
  }
}
```

这对排查“到底是 DeepSeek 慢、TTS 慢、还是播放慢”非常重要。

---

## 17. 配置项

`.env.example`：

```env
TTS_ATOM_HOST=127.0.0.1
TTS_ATOM_PORT=9020
TTS_ATOM_DEFAULT_PROVIDER=melotts
TTS_ATOM_DEFAULT_LANGUAGE=zh
TTS_ATOM_AUDIO_ROOT=./runs
TTS_ATOM_CACHE_ROOT=./cache
TTS_ATOM_MODELS_ROOT=./models
TTS_ATOM_ENABLE_CACHE=true
TTS_ATOM_MAX_TEXT_LENGTH=1000
TTS_ATOM_DEFAULT_FORMAT=wav
TTS_ATOM_DEFAULT_SAMPLE_RATE=24000
TTS_ATOM_LOG_LEVEL=INFO
```

---

## 18. 与 Companion Launcher 的关系

未来儿童陪伴系统不应该依靠用户手动打开多个 PowerShell 窗口。

正确目标：

```text
双击儿童陪伴系统
    ↓
Companion Launcher 自动启动：
    - Companion BFF
    - voice-atom
    - tts-atom
    - 前端 / Electron
    ↓
检查所有服务 /healthz
    ↓
打开儿童界面
```

`tts-atom` 必须满足：

1. 可固定端口启动；
2. 可静默启动；
3. 可健康检查；
4. 可被父进程终止；
5. 可输出日志文件；
6. 启动失败时返回明确错误。

---

## 19. MVP 范围

第一阶段必须完成：

1. Python 项目骨架；
2. CLI：`synth`、`serve`、`voices`、`doctor`；
3. FastAPI 服务；
4. `/healthz`；
5. `/api/tts/providers`；
6. `/api/tts/voices`；
7. `/api/tts/synthesize`；
8. `/api/tts/split-synthesize`；
9. `/api/tts/prewarm`；
10. Provider 抽象；
11. MeloTTSProvider 默认实现；
12. WindowsSapiProvider 或 MockProvider 作为兜底/测试；
13. 缓存机制；
14. 音频文件保存与 `/audio/...` 访问；
15. 统一错误结构；
16. timing 返回；
17. README 使用说明；
18. 基础测试。

第一阶段可以暂不完成：

1. WebSocket 流式音频；
2. Kokoro 真正接入；
3. 豆包 TTS 真正接入；
4. 嘴型时间戳；
5. 复杂角色动作；
6. 语音克隆。

---

## 20. 验收标准

### 20.1 CLI 验收

运行：

```bash
tts-atom synth --text "你好，小警员，我们开始吧。" --json
```

应返回：

1. `ok = true`；
2. 生成音频文件；
3. 返回 `audio_path`；
4. 返回 `provider`；
5. 返回 `timing`；
6. 第二次同样请求应 `cached = true`。

### 20.2 HTTP 验收

运行：

```bash
tts-atom serve --port 9020
```

访问：

```http
GET http://127.0.0.1:9020/healthz
```

应返回 `ok = true`。

调用：

```http
POST http://127.0.0.1:9020/api/tts/synthesize
```

应返回可播放的 `audio_url`。

### 20.3 分句合成验收

输入：

```text
好的，我们先看第一题。5加3等于几呢？你可以先数5个，再数3个。
```

应返回至少 2 个 segment，每个 segment 有：

1. `text`；
2. `audio_url`；
3. `duration_ms`；
4. `cached`。

### 20.4 儿童陪伴系统接入验收

Companion BFF 调用 `tts-atom` 后：

1. 能获取音频 URL；
2. 前端能播放音频；
3. TTS 服务不可用时 BFF 能返回明确错误；
4. 超时不会卡死；
5. 常用话术能预热；
6. 重复话术能走缓存。

---

## 21. Cursor / GAEH 任务目标建议

可以把以下内容作为交给 Cursor / GAEH 的目标输入。

### 21.1 总目标

构建 `tts-atom`：一个本地文本转语音原子服务，默认使用 MeloTTS，支持 Provider 可插拔、CLI、HTTP API、缓存、分句合成、角色音色配置、健康检查和 timing 观测，服务于儿童陪伴系统的角色语音输出。

### 21.2 第一阶段任务

1. 创建 Python 项目骨架；
2. 设计 Pydantic schema；
3. 实现 TTSProvider 抽象；
4. 实现 MockProvider，保证无模型时测试可跑；
5. 实现 MeloTTSProvider 的接入占位和真实接入路径；
6. 实现 FastAPI 服务；
7. 实现 CLI；
8. 实现缓存；
9. 实现分句；
10. 实现音频文件保存；
11. 实现 `/audio` 静态文件访问；
12. 实现 `/healthz`；
13. 实现 `/api/tts/synthesize`；
14. 实现 `/api/tts/split-synthesize`；
15. 实现 `/api/tts/prewarm`；
16. 增加 README；
17. 增加测试；
18. 输出 dev 启动说明和接入说明。

### 21.3 技术约束

1. 不允许把儿童陪伴业务逻辑写进 `tts-atom`；
2. 不允许前端直接绑定 MeloTTS；
3. Provider 必须可替换；
4. 所有 API 必须有统一错误结构；
5. 所有合成请求必须返回 timing；
6. 所有音频输出必须有稳定访问路径；
7. 服务必须提供 `/healthz`；
8. CLI 和 HTTP 必须复用同一套核心逻辑；
9. MVP 必须能在没有真实 MeloTTS 模型时通过 MockProvider 跑通基础测试；
10. 端口、目录、默认 Provider 必须可配置。

---

## 22. 推荐开发顺序

### Step 1：项目骨架

创建目录、配置、README、CLI 入口和 FastAPI app。

### Step 2：Schema 和错误结构

先定义请求、响应、错误、ProviderResult、VoiceInfo。

### Step 3：MockProvider

用 MockProvider 生成简单 wav 或静音 wav，先跑通全链路。

### Step 4：缓存与音频存储

实现 hash 缓存、runs 输出、audio_url 映射。

### Step 5：HTTP API

实现 healthz、providers、voices、synthesize、split-synthesize、prewarm。

### Step 6：CLI

实现 synth、serve、voices、doctor。

### Step 7：MeloTTSProvider

接入真实 MeloTTS。

### Step 8：儿童陪伴系统接入

由 Companion BFF 调用 `tts-atom`，前端播放返回的 `audio_url`。

### Step 9：Launcher 托管

后续加入 Companion Launcher，实现单入口启动，不再依赖多个 PowerShell 手动窗口。

---

## 23. 推荐 README 内容

README 至少包含：

1. 项目定位；
2. 安装方法；
3. MeloTTS 模型准备；
4. CLI 使用；
5. HTTP API 使用；
6. Provider 配置；
7. 角色音色配置；
8. 缓存说明；
9. 儿童陪伴系统接入方式；
10. 常见问题；
11. 开发期启动方式；
12. 正式托管方式规划。

---

## 24. 风险与注意事项

### 24.1 MeloTTS 中文音色效果需要实测

默认采用 MeloTTS 是合理的，但最终音色是否适合儿童陪伴角色，需要实际试听。

### 24.2 本地 TTS 不一定比云端更好听

本地 TTS 优势是稳定、低延迟、可离线、无按量费用。  
云端 TTS 优势是音色自然、情绪表现强。  
因此最佳策略是：

```text
本地负责快和兜底
云端负责高质量表演
```

### 24.3 不要把多个 PowerShell 窗口作为正式方案

多个窗口可以用于开发调试，但正式使用必须通过 Launcher、服务管理或 Docker Compose 统一托管。

### 24.4 字段要预留，但功能不要过早复杂化

可以在 schema 中预留 `emotion`、`pitch`、`role_id`、`stream`、`metadata` 等字段，但 MVP 不需要全部真实实现。

---

## 25. 一句话定义

`tts-atom` 是儿童陪伴系统的本地语音输出原子服务：默认使用 MeloTTS，支持 Provider 可替换、角色音色配置、分句合成、缓存、健康检查、CLI/HTTP 双接口，并能被 Companion Launcher 托管，最终让角色能够稳定、快速、可控地对孩子说话。



## Context (Optional)

- Existing repo?: 绿场（无既有业务代码）
- Target users?: 儿童陪伴系统开发者 / 本地部署
- Deadline?: 无硬性截止（MVP 优先）

## Q&A (GGS)

- **GGS iteration 1**：`idea.md` 已含完整规格；Context 空白项按 `assumptions.md` A-0001～A-0003 补全，未阻塞 goal 导出。
