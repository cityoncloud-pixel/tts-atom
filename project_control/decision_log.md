# decision_log.md

（AI 追加：关键决策与原因、路由变化、回滚原因、架构变更）

## 2026-05-19 — tts-atom-mvp-0001 Spec/Plan

- **路由**: Route B（Normal），`spec_first`，先 Mock 全链路再 MeloTTS/SAPI。
- **CLI**: Typer（goal 推荐，Spec §13）。
- **Mock 音频**: 静音 WAV 100ms @ 24kHz，便于 pytest 与无模型开发。
- **超长文本**: 拒绝（`TTS_TEXT_TOO_LONG`），不静默截断。
- **生产 fallback**: Mock 不作为 silent fallback；仅 `FORCE_MOCK` 或测试环境。
- **门禁**: Spec/Plan/Pre-review 已完成；执行阻塞于 Owner `APPROVE`。

## 2026-05-19 — tts-atom-mvp-0001 执行完成

- Owner `APPROVE` 后完成 Phase 0–8 实现。
- `pytest` 11 passed；CLI synth 缓存命中验证通过。
- MeloTTS 真实推理留待后续；当前 `models/` 占位 + 占位 WAV 满足 MVP 验收。

## 2026-05-19 — MeloTTS 真实接入

- 新增 `melotts_runtime.py`：`melo.api.TTS` 内存合成 + `melo` CLI 回退；模型 HF 缓存至 `models/`。
- `is_available()` 改为检测真实 MeloTTS 安装，不再依赖 `models/.gitkeep`。
- 可选依赖：`pip install -e ".[melotts]"`；Windows 需 MSVC 或 WSL/Docker。

