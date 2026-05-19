# Assumptions (LLM Best-Effort)

当你回答不了、或信息缺失时，GGS 允许 LLM 给出“最优可执行假设”，但必须全部记录在这里，便于审计与回滚。

格式建议（每条一段）：

## A-0001
- Assumption: 本项目为**从零开始**的绿场仓库；`idea.md` 中 Context 未填写 Existing repo，当前工作区除 GAEH 脚手架外无业务代码。
- Rationale: `idea.md` §Context 为空；工作区无既有 `tts_atom` 包。
- Risk Level: low
- If wrong, fallback: 若已有私有代码需合并，Owner 在 `change_requests.md` 说明路径后调整 Scope/Inputs。

## A-0002
- Assumption: 主要运行平台为 **Windows 10+ 本地**；Companion Launcher 托管为后续阶段，MVP 以 CLI + HTTP 本地运行为主。
- Rationale: Owner 环境为 win32；`idea.md` §18 将 Launcher 标为“未来”。
- Risk Level: medium
- If wrong, fallback: 增加 Linux/macOS 启动说明与路径差异测试。

## A-0003
- Assumption: **无硬性截止日期**；按 MVP 分阶段交付，先 Mock 跑通再接入真实 MeloTTS。
- Rationale: `idea.md` Context 中 Deadline 未填写。
- Risk Level: low
- If wrong, fallback: Owner 在 `goal.md` 或 `approval.json` 补充日期后重排任务优先级。

## A-0004
- Assumption: Python **3.10+**，依赖管理使用 **pyproject.toml**（uv/pip 均可），HTTP 默认端口 **9020**，默认 Provider **melotts**。
- Rationale: `idea.md` §5、§17 明确推荐栈与配置项。
- Risk Level: low
- If wrong, fallback: 在 `config.py` / `.env` 中调整，不改架构。

## A-0005
- Assumption: MVP 验收**不强制**安装真实 MeloTTS 模型；**MockProvider**（或 Windows SAPI）必须使 `pytest` 与 HTTP 合成链路在无模型时通过。
- Rationale: `idea.md` §19、§21.3 第 9 条明确要求。
- Risk Level: medium
- If wrong, fallback: CI/本地文档补充 MeloTTS 模型下载步骤，并将 MeloTTS 真实合成标为 Phase 2 验收项。

## A-0006
- Assumption: 本项目**无面向终端儿童的 UI**；交互为 CLI 命令与 HTTP API；儿童陪伴前端仅通过 Companion BFF 间接调用。
- Rationale: 原子服务定位；`idea.md` §4.2 禁止前端直连。
- Risk Level: low
- If wrong, fallback: 若需管理台，单独立项，不纳入本 goal MVP。

## A-0007
- Assumption: `emotion` / `pitch` 等字段在 schema 中保留，MVP 可映射为 speed/volume 等参数，**不要求**底层 Provider 原生情感合成。
- Rationale: `idea.md` §9.2、§24.4。
- Risk Level: low
- If wrong, fallback: Phase 2 按 Provider 能力逐项实现。
