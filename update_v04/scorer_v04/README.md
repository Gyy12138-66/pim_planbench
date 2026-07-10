# Scorer v0.4：断言核验层（修订项 #2）

## 定位

v0.3 评分器（`scripts/score_3modeloutput_v03.py`，冻结）只做线索覆盖匹配，
能查"该提没提"，不能查"提了但说错"——实证缺陷见 `arms_v0.4_findings.md`
（D3 系数篡改与金计划同分、hallucination/wrong-task-type cap 零触发）与
`docs/item_analysis_v0.4.md` §2（唯一有效的规则恰是结构核验型的 pf_strict_cap）。

v0.4 = v0.3 覆盖层（给分）+ 本目录断言核验层（触发 cap）。两层各司其职,
不改动 v0.3 引擎。

## 文件

- `claim_verifier.py` —— 核验层：抽取计划文本中的断言,与任务实例化规格对账。
  三类检出：`numeric_contradiction`（数值断言与规格矛盾 → hallucination cap）、
  `wrong_task_type`（正/反问题声明矛盾,含"待估未知量被断言为已知值"）、
  `fabricated_component`（杜撰组件冠以"领域标准"名义并声称已知保证）。
  cap 按 rubric v0.3：受影响 facet 封顶 2（wrong-task-type 封 PF+MC）。
- `run_regression.py` —— 对抗回归套件（55 臂）,评分器发布门。
- `regression_report.md` —— 最近一次套件输出（当前:全部通过）。

## 回归套件判据（R1–R5）

| # | 判据 | 当前 |
|---|---|---|
| R1 | D3 数值篡改检出（003/005/016/023） | ✅ 4/4 |
| R2 | D3 幻觉组件检出（010） | ✅ |
| R3 | D2 任务类型检出（5 题） | ✅ 5/5 |
| R4 | G/T/N1–N6/D1 共 45 臂零误伤 | ✅ 0 误报 |
| R5 | cap 后 D2/D3 总分 < 同题 G | ✅ |

设计原则：**精确率优先**——cap 只在断言无歧义矛盾时触发；第一版符号白名单
方案因误伤自然臂的合法自定义损失（L_weak/L_entropy 等,023 高分臂的正当行为）
被否决,改为"虚假权威声明"模式（见 git 历史）。

## 已知边界（诚实声明）

1. **规格表只覆盖执行子集 5 题**（协议 §3 冻结实例化）。扩到 26 题的检查项
   清单已在 `item_analysis_v0.4.md` §4-B"可核验断言"列;随 #1 重写逐题落地。
2. **fabrication 检测窄**：只捕获"权威语+保证语"共现模式,换一种编造话术可绕过。
   泛化路径 = LLM 辅助抽取（计划→结构化 schema→确定性比对,含
   `is_labeled_assumption` 标志）,与修订项 #4 的 LLM-judge 第二意见共用基础设施。
3. **cap 幅度受 rubric 限制**：D3 篡改只出现在 PF 段落 → 只有 PF 被封,总分
   25→22,仍高于模板臂。若认为"篡改主方程系数应连带封 Physics Constraints"，
   属 rubric 修订决策（v0.4 rubric,待作者定夺）,不在核验层擅自扩大。
4. **任务类型模式在风格化臂文本上调校**,自然臂 45 例零误报;新模型输出风格
   变化时需重跑套件确认。

## 预注册纪律

- v0.3 冻结版继续服务 H4 执行效度实验;本层不参与 H4 打分。
- v0.4 全量重打分作为修订项 #2 报告（cap 加固前后对比即论文一栏结果）。
- 执行结果回传后的终极检验：v0.4 触发 cap 的臂,其执行误差是否系统性更高
  （H4c 在 v0.4 下重算）——cap 机制的预测效度从主张变为测量。

## 用法

```bash
cd update_v04/scorer_v04
python3 run_regression.py            # 发布门:exit 0 = 可发布
python3 claim_verifier.py --arms-csv ../execution_validation/arms_text/generated/arms_input_v0.4.csv
```
