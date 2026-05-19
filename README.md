# tts-atom

本地文本转语音（TTS）原子服务，面向儿童陪伴系统的角色语音输出。默认 Provider 为 MeloTTS（MVP 可在无真实模型权重时用占位 WAV 跑通；测试环境使用 `mock`）。

## 安装

```bash
cd d:\01_PROJECT\TTS-atom
pip install -e ".[dev]"
```

复制环境变量：

```bash
copy .env.example .env
```

## 快速使用

```bash
# 诊断
tts-atom doctor --json

# 合成（JSON 输出）
tts-atom synth --text "你好，小警员，我们开始吧。" --json

# 启动 HTTP 服务（默认 127.0.0.1:9020）
tts-atom serve --port 9020
```

## HTTP API

| 方法 | 路径 |
|------|------|
| GET | `/healthz` |
| GET | `/api/tts/providers` |
| GET | `/api/tts/voices` |
| POST | `/api/tts/synthesize` |
| POST | `/api/tts/split-synthesize` |
| POST | `/api/tts/prewarm` |
| GET | `/audio/...` |

示例：

```bash
curl http://127.0.0.1:9020/healthz
curl -X POST http://127.0.0.1:9020/api/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"你好\",\"provider\":\"mock\"}"
```

## Provider

| 名称 | MVP 状态 |
|------|----------|
| `melotts` | 默认；`models/` 有内容即可 `is_available`；真实 melotts 包接入待完善 |
| `mock` | 测试/强制：`TTS_ATOM_FORCE_MOCK=true` |
| `windows_sapi` | 需 `pyttsx3`（Windows） |
| `kokoro` / `edge` / `doubao` | 占位，未接入 |

## 角色音色

`tts_atom/roles/default_roles.json` 定义 `rabbit_officer` 等角色。请求可只传：

```json
{ "role_id": "rabbit_officer", "text": "小警员，我们开始吧！" }
```

## 缓存

- 目录：`cache/{provider}/{voice}/{sha256}.wav`
- 清理：`tts-atom cache clear`

## MeloTTS 模型（可选）

将模型文件放入 `models/`，或创建 `models/.melotts_ready` 标记。安装真实 MeloTTS 后可在 `melotts_provider.py` 中扩展合成调用。

## Companion BFF 接入

BFF 调用 `POST http://127.0.0.1:9020/api/tts/synthesize`，将返回的 `audio_url` 交给前端播放。分句场景使用 `/api/tts/split-synthesize` 获取 `segments[]` 播放队列。

## 测试

```bash
pytest -q
```

测试默认 `TTS_ATOM_FORCE_MOCK=true`（见 `tests/conftest.py`）。

## GAEH

本项目使用 [GAEH](GAEH_Implementation_Spec.md) 管理目标与迭代。目标见 `project_control/goal.md`。
