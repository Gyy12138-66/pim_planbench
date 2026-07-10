# 盲转写审计记录（2026-07-10，冻结前）

## 流程

- 50 个可执行臂（5 题 × [N1–N6, G, T, D1, D3] + 010 的 D2；D2×4 与 D3-010 为
  scorer-only 不转写）由 5 个相互隔离的盲转写代理完成：每个代理只接触
  `arms_blind/` 下随机码命名的匿名计划文本、转写清单与 defaults，
  不接触臂身份、模型名、plan_score、协议文档与 git 历史。
  码↔臂映射（`analysis_only/arm_code_map.csv`）仅分析侧持有。
- 逐旋钮决策日志：`transcription/mapping_log_{003,005,010,016,023}.csv`
  （约 950 条，含全部 unspecified / out_of_menu / conflict / omitted 记录与原文摘录）。

## 机器审计结果（validate_configs.py）

1. 50/50 配置 YAML 可加载、harness 2 步冒烟全部通过（含 D2/D3 的 pde.* 覆盖路径）。
2. 消融臂 expected_config 对照：全部命中。4 条"期望 0/false 但未写键"提示均为
   误报（defaults 本即 0/false，语义等价）。
3. **配对完整性**：每个 D 臂与其 parent G 的配置差异恰好局限于目标旋钮——
   D3 仅差 pde.*（4 题）；D1 仅差被删约束对应键（bc / periodic+harmonics / data / AV）；
   010-D2 差 4 个联动键（nu_fixed、data.enabled、weights.data、init_nu）。无泄漏差异。
4. **旋钮塌缩检查**（config_diversity.csv）：自然臂互异旋钮数 003:11 / 005:16 /
   010:11 / 016:5 / 023:12 —— 5 题全部具备 H4a 资格，预注册的剔除规则无需启用。

## 仲裁裁定（已固化进清单 §1.1）

转写代理共标记 ~30 条不确定判定；复核后全部接受其决策，其中四类共性问题
（符号形式是否算数值断言、区间取值、对冲语气、非顺序 optimizer 句式）已作为
清单 §1.1 仲裁澄清固化。个案接受理由均以代理日志中 "UNCERTAIN" 标记 + 本记录为准。

## 与协议 §5.4 的偏差声明（须如实写入论文）

- 转写者为 LLM 代理而非人类：盲性通过信息隔离实现（代理无法访问臂身份），
  但**协议要求的第二人 ≥20% 独立重转写审计仍待人类执行**；本文档的机器审计
  （expected_config 对照 + 配对差分）覆盖了 16/50 臂（G/D/T），自然臂 N1–N6 的
  人工抽审在冻结后、正式运行前补做，不一致处按清单 §3 仲裁并全量复查该旋钮。
