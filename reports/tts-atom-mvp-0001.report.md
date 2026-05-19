# Report: tts-atom-mvp-0001

| 字段 | 值 |
|------|-----|
| Task | tts-atom-mvp-0001 |
| Status | **COMPLETED** |
| Owner Approval | APPROVED (chat) |
| Date | 2026-05-19 |

---

## 交付摘要

实现 `tts-atom` v0.1.0 Python 包：CLI + FastAPI HTTP、Provider 抽象、Mock/MeloTTS/WindowsSAPI(可选)、缓存、分句、角色配置、预热 API、统一错误与 timing。

---

## 验收结果（goal.md Success Criteria）

| ID | 标准 | 结果 | 证据 |
|----|------|------|------|
| SC-1 | CLI synth + cache | **PASS** | `tts-atom synth` 两次；第二次 `cached: true` |
| SC-2 | HTTP health + synthesize | **PASS** | `tests/test_healthz.py` |
| SC-3 | split-synthesize ≥2 segments | **PASS** | `tests/test_healthz.py::test_split_synthesize` |
| SC-4 | pytest 全绿 | **PASS** | `11 passed` |
| SC-5 | CLI/HTTP 共用 engine | **PASS** | `tts_atom.core.engine.get_engine()` |

### 命令日志

```text
pytest -q
# 11 passed in 2.29s

tts-atom doctor --json
# melotts: true, mock: true, windows_sapi: false

tts-atom synth --text "你好，小警员，我们开始吧。" --json  # cached: false
tts-atom synth --text "你好，小警员，我们开始吧。" --json  # cached: true
```

---

## 已知限制

1. **MeloTTS 真实合成**：当前为占位 WAV（时长随文本略变）；需安装 melotts 并扩展 `melotts_provider.py`。
2. **Windows SAPI**：未安装 `pyttsx3` 时 `windows_sapi` 不可用（本机 doctor 为 false）。
3. **静态路由**：缓存音频 URL 为 `/audio/cache/...` 专用路由；runs 下文件为 `/audio/{date}/...`。

---

## 变更文件（主要）

- `pyproject.toml`, `tts_atom/**`, `tests/**`
- `README.md`, `.env.example`, `.gitignore`

---

## 下一步建议（非本任务范围）

- 接入真实 MeloTTS 推理
- Companion BFF 联调
- Companion Launcher 托管 `tts-atom serve`
