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

## MeloTTS 真实合成

基于 [MeloTTS](https://github.com/myshell-ai/MeloTTS)（`from melo.api import TTS`），支持 **Python API** 与 **`melo` CLI** 双路径。

### 安装

```bash
# 推荐：从 GitHub 安装（PyPI 的 melotts 包可能损坏）
pip install -e ".[melotts]"

# Windows 可运行脚本
powershell -ExecutionPolicy Bypass -File scripts/install_melotts.ps1
```

首次合成会从 HuggingFace 下载权重，缓存目录默认 `models/`（通过 `HF_HOME` / `HUGGINGFACE_HUB_CACHE`）。

**Windows 方式 A（推荐，已在本项目验证）**：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_melotts.ps1
```

要点：
- `fugashi>=1.5.2` 使用预编译 wheel，**无需 MSVC**
- `transformers`/`tokenizers` 使用 Py3.12 有 wheel 的版本，**无需 Rust**
- 首次 `doctor` 会从 HuggingFace 下载多语言 BERT（仅中文合成也会预拉取，耗时较长）
- 中英混合文本需 NLTK：`nltk.download('averaged_perceptron_tagger_eng')`（安装脚本已包含）

若仍失败，可参考 [MeloTTS install.md](https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md) 或使用 WSL2。

### 配置（`.env`）

| 变量 | 说明 |
|------|------|
| `TTS_ATOM_MELOTTS_DEVICE` | `auto` / `cpu` / `cuda` |
| `TTS_ATOM_MELOTTS_USE_HF` | 从 HuggingFace 拉取模型（默认 true） |
| `TTS_ATOM_MELOTTS_CKPT_PATH` | 可选本地 checkpoint |
| `TTS_ATOM_MELOTTS_CLI_PATH` | 可选 `melo.exe` 路径 |

### 验证

```bash
tts-atom doctor --json    # 查看 melotts.backend: python_api | cli | none
tts-atom synth --text "你好，小警员" --provider melotts --json
```

### 音色映射

| voice_id | MeloTTS |
|----------|---------|
| `zh_female_01` | ZH / ZH |
| `en_us` | EN / EN-US |
| `en_default` | EN / EN-Default |

详见 `tts_atom/providers/melotts_runtime.py` 中 `VOICE_SPEAKER_MAP`。

## Companion BFF 接入

BFF 调用 `POST http://127.0.0.1:9020/api/tts/synthesize`，将返回的 `audio_url` 交给前端播放。分句场景使用 `/api/tts/split-synthesize` 获取 `segments[]` 播放队列。

## 测试

```bash
pytest -q
```

测试默认 `TTS_ATOM_FORCE_MOCK=true`（见 `tests/conftest.py`）。

## GAEH

本项目使用 [GAEH](GAEH_Implementation_Spec.md) 管理目标与迭代。目标见 `project_control/goal.md`。
