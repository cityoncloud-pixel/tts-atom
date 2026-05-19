# Plan: tts-atom-mvp-0001

| 字段 | 值 |
|------|-----|
| Spec | `specs/tts-atom-mvp.spec.md` |
| Goal | `project_control/goal.md` |
| Route | B — Normal |
| 状态 | **等待 Owner `APPROVE`** |

---

## 目标

在绿场仓库实现 `tts-atom` MVP v0.1.0，满足 `goal.md` 五条 Success Criteria；优先 Mock 全链路，再接入 MeloTTS 可用性检测与合成路径。

---

## 执行阶段

### Phase 0 — 脚手架（预估 1 轮）

- [ ] `pyproject.toml` + `tts_atom` 包结构 + `.gitignore` + `.env.example`
- [ ] `config.py`（pydantic-settings）
- [ ] `runs/`, `cache/`, `models/` + `.gitkeep`
- [ ] 空 CLI `main.py`（Typer app）可 `tts-atom --help`

**验证**: `pip install -e ".[dev]"` 成功

---

### Phase 1 — Schema + 错误 + Timing（预估 1 轮）

- [ ] `schemas.py`：TTSRequest, SynthesizeResponse, Segment, Prewarm*, VoiceInfo, Timing
- [ ] `errors.py`：错误码 + `make_error()`
- [ ] `timing.py`：TimingCollector 上下文管理器
- [ ] `tests/test_schemas.py`

**验证**: `pytest tests/test_schemas.py`

---

### Phase 2 — MockProvider + Engine 骨架（预估 1–2 轮）

- [ ] `providers/base.py`, `mock_provider.py`
- [ ] `providers/melotts_provider.py`（stub + `is_available` 检测）
- [ ] 占位 providers（kokoro/edge/doubao → unavailable）
- [ ] `core/router.py`（auto 路由逻辑）
- [ ] `core/engine.py`（单次 synthesize，无 cache）
- [ ] `tests/test_synthesize_mock.py`

**验证**: Engine 单元测试返回 `ok=true` + wav bytes

---

### Phase 3 — 缓存 + 音频存储（预估 1 轮）

- [ ] `core/cache.py`（SHA256 key）
- [ ] `core/audio_store.py`（日期目录 + hash 文件名 + audio_url）
- [ ] Engine 集成 cache
- [ ] `tests/test_cache.py`

**验证**: 同请求第二次 `cached=true`

---

### Phase 4 — 分句 + 角色（预估 1 轮）

- [ ] `core/splitter.py`
- [ ] `roles/default_roles.json` + `role_profiles.py`
- [ ] emotion → speed/pitch/volume 映射
- [ ] Engine `split_synthesize`
- [ ] `tests/test_splitter.py`

**验证**: 固定中文长句 → ≥2 segments

---

### Phase 5 — HTTP API（预估 1–2 轮）

- [ ] `server.py`：FastAPI app, CORS 关闭（本地）, `/healthz`
- [ ] `/api/tts/providers`, `/voices`, `/synthesize`, `/split-synthesize`, `/prewarm`
- [ ] 静态 `/audio` 挂载
- [ ] `core/prewarm.py` + `assets/prewarm_phrases.zh.json`
- [ ] `tests/test_healthz.py`（httpx TestClient）

**验证**: TestClient 全覆盖；手动 `serve` + curl（报告记录）

---

### Phase 6 — CLI（预估 1 轮）

- [ ] `synth`, `serve`, `voices`, `doctor`, `cache clear`, `speak`（可选）
- [ ] CLI 与 HTTP 共用 `Engine` 单例工厂

**验证**: SC-1 CLI 命令（报告）

---

### Phase 7 — Windows SAPI + MeloTTS 路径（预估 1 轮）

- [ ] `windows_sapi_provider.py`（仅 Windows 尝试 import pywin32/SAPI）
- [ ] `melotts_provider.py` 真实合成钩子（依赖可选；文档说明）
- [ ] `doctor` 输出各 provider 状态

**验证**: `tts-atom doctor --json` 结构正确；Windows 上 sapi 可选绿

---

### Phase 8 — 文档与收尾（预估 1 轮）

- [ ] `README.md`：安装、dev、API 示例、BFF 接入、MeloTTS 模型
- [ ] 更新 `project_control/phase_status.md`
- [ ] `reports/tts-atom-mvp-0001.report.md`（验证日志）
- [ ] `reviews/tts-atom-mvp-0001.review.md`（执行后审查）

**验证**: 完整 `pytest -q` + goal 验收矩阵 SC-1～SC-5

---

## 依赖顺序

```mermaid
flowchart LR
  P0[Phase 0 Scaffold] --> P1[Phase 1 Schema]
  P1 --> P2[Phase 2 Mock+Engine]
  P2 --> P3[Phase 3 Cache+Audio]
  P3 --> P4[Phase 4 Split+Roles]
  P4 --> P5[Phase 5 HTTP]
  P5 --> P6[Phase 6 CLI]
  P6 --> P7[Phase 7 SAPI+MeloTTS]
  P7 --> P8[Phase 8 Docs+Report]
```

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| MeloTTS 安装失败 | Mock 保证 SC-1～4；MeloTTS 为 Phase 7 增强 |
| Windows SAPI 不可用 | fallback 链跳过；doctor 标明原因 |
| 分句误切数学式 | test_splitter 覆盖；迭代规则 |

---

## 回滚策略

- 每 Phase 结束 `pytest` 必须通过再进入下一阶段。
- 若 Phase 7 阻塞，可合并为“仅 Mock + SAPI”，MeloTTS 文档化 deferred，需在 report 中声明并与 Owner 确认（CR）。

---

## Owner 门禁

**本 Plan 不包含实现提交**，直至收到：

- 聊天：`APPROVE` 或 `APPROVE tts-atom-mvp-0001`
- 或 `approval.json` → `init-approval` / `tts-atom-mvp-0001-approval` → `APPROVED`
