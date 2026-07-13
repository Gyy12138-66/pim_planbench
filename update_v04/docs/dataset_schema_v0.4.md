# dataset_schema_v0.4 —— v0.4 数据与断言落地格式（草案，待作者审批）

> 本文档敲定"重写规格 MD → 数据 + 评分器"的落地格式。16 份重写规格
> （`task_rewrites_v0.4/`）的内容审批可与本文档并行，但**任何一题转写进
> JSONL 之前，本文档必须先冻结**（避免 16 题转两遍）。
>
> 配套下游：`scorer_v04/claim_verifier.py` 从硬编码 `SPECS`（5 题）改为
> 通用加载器，读本文档定义的 `verifiable_claims` 字段（26 题全覆盖）。

## 0. 三个核心决定（本文档要作者拍板的）

| # | 决定 | 本稿立场 | 理由 |
|---|---|---|---|
| D1 | 断言放数据还是放代码 | **数据**：`references_private_v0.4.jsonl` 新增 `verifiable_claims` 字段；claim_verifier 改为通用加载器 | 私有数值硬编码在评分器代码里，与修订项 #6 治理主张（版本化公私划分、vN 参考随 vN+1 解密）直接矛盾；5→26 题扩展不可维护 |
| D2 | cap 判定双轨终结 | **单轨**：v0.4 评分器从 JSONL 读 `facet_cap_rules` 执行 cap；`hard_trap_caps()` 式逐题硬编码废止 | v0.3 现状是代码（`score_3modeloutput_v03.py:323`）与数据（JSONL `facet_cap_rules`）各存一份、内容不保证一致——治理节写不圆 |
| D3 | facet 命名钉死 | snake_case 为规范 id，显示名映射表见 §2.2 | 现状三处漂移：公开 schema "Validation Failure Risks"、MD 草案 "Validation & Failure Risks"、JSONL `validation_failure_risks` |

## 1. 文件布局与版本治理

```
dataset/
├── tasks_public_v0.3.jsonl          # 冻结不动
├── references_private_v0.3.jsonl    # 冻结不动（v0.4 发布时按治理政策解密）
├── tasks_public_v0.4.jsonl          # 新建：完整快照（非 delta 文件）
├── references_private_v0.4.jsonl    # 新建：完整快照
└── CHANGELOG_v0.4.md                # 新建：逐题记录 rewritten/merged/relocated/new/unchanged
```

- **完整快照**而非 delta：两个 v0.4 文件各自独立可用，不需要叠加 v0.3 读取。
  未重写的题（如 003、005、008–010、016、023、025、026）原条目复制进 v0.4
  文件，仅补 §3.1 的治理字段。
- **id 政策**：重写题保留原 id（如 `medium_heat_mixed_bc_014`）——重写是
  同一测量意图的修订，item 级纵向对比需要稳定锚点；改变测量意图的（007
  重定位）也保留 id，在 `CHANGELOG` 记录定位变化。被兼并题（001）不出现
  在 v0.4 文件中，由兼并方条目的 `supersedes` 字段与 CHANGELOG 双记录；
  001 的 v0.3 条目原地冻结即为归档（"标记 superseded, 归档不删除"）。
  新题（#1b 覆盖矩阵产出）用新 slug + 复用空出的编号槽位
  （如 `easy_<new_slug>_001`），完整 id 不与旧 id 冲突。
- **canary**：v0.4 两文件各加一条 `id: "canary_pim_planbench_v0_4"` 的
  哨兵条目（GSM1k 式污染探针），评分与统计管线按 id 前缀排除。

## 2. 公开任务文件 `tasks_public_v0.4.jsonl`

### 2.1 Schema：与 v0.3 完全一致，零新增字段

字段集合不变：`id, difficulty, domain, pde_system, task_type, tags,
source_provenance, problem, output_schema`。

- **公开侧继续不含私有数值**（TODO_FILL 设计不变）。题面中*允许*出现的
  数字仅限两类，且都是设计输入不是参考答案：
  1. **公开预算约束**（P3 反模板机制），如 004 新题面的 "at most 20,000
     residual collocation points … at most 30,000 optimizer steps"；
  2. **公开量级**（内部一致性断言的锚点），如 020 的 "roughly twenty
     wavelengths across the domain"（量级公开，精确 k 私有）。
- `problem` 直接取重写规格 MD"新公开题面（英文草案）"节的审定终稿。
- `tags` 随支点更新（如 014 增 `neumann_flux_injection`、`energy_balance`）。

### 2.2 facet 规范命名（全仓唯一映射表）

| facet_id（snake_case，JSONL/统计） | 显示名（output_schema / verifier / 模型输出解析） |
|---|---|
| `problem_formalization` | `Problem Formalization` |
| `physics_constraints` | `Physics Constraints` |
| `model_choice` | `Model Choice` |
| `training_strategy` | `Training Strategy` |
| `validation_failure_risks` | `Validation Failure Risks` |

- 显示名以 v0.3 公开 `output_schema` 现文为准——**没有 "&"**。重写 MD
  草案中出现的 "Validation & Failure Risks" 等变体在转写时一律折到上表。
- 转写校验脚本（§6）强制：cap 规则与 claims 中的 facet 引用只允许
  snake_case id。

## 3. 私有参考文件 `references_private_v0.4.jsonl`

### 3.1 保留字段 + 顶层新增

v0.3 全部字段语义不变（`canonical_pde, constraints, parameter_values,
reference_conditions, analytic_solution, critical_points, failure_traps,
facet_cap_rules, rubric, facet_score_scale, …`）。顶层新增 4 个治理字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema_version` | int | 本文档定义的结构版本，v0.4 = `2` |
| `scoring_version` | str | `"pim_planscore_private_v0.4"`（替换 v0.3 值） |
| `revision` | str | `"rewritten" \| "light_edit" \| "relocated" \| "new" \| "unchanged"` |
| `supersedes` | list[str] | 兼并的旧 id，如 014 的 `["easy_heat_1d_dirichlet_001"]`；无则 `[]` |

### 3.2 新增字段 `verifiable_claims`（D1 的落地）

把重写规格 MD 的"可核验断言（P2）"节结构化。每条 claim：

```
{
  "claim_id":   str,            # 题内唯一，snake_case
  "type":       str,            # 见下表，封闭集合
  "basis":      "spec" | "plan_internal",
  "facets":     [facet_id],     # 在哪些 facet 的文本上做抽取
  "description": str,           # 人读的一句话（进 IAA 标注材料与论文附录）
  ...类型特定字段（见下表）,
  "on_contradiction": str       # 指向 facet_cap_rules 的 rule_id
}
```

`basis` 对应 README 的两类断言：`spec` = 规格对账（判定需要本条目的私有
值）；`plan_internal` = 内部一致性（只用计划自己给出的数 + 公开量级）。
两类都存私有文件（抽取模式公开会诱导规避性措辞——反 Goodhart），`basis`
字段本身是给治理节和论文叙事用的分类标签。

**claim 类型封闭集合**（对齐 claim_verifier 现有三类 + 重写 MD 新需求）：

| `type` | 类型特定字段 | 判定语义 | finding kind |
|---|---|---|---|
| `param_value` | `param, true_value, rtol, patterns[]` | 抽取计划声称的参数值，与私有真值比对；超容差即矛盾 | `numeric_contradiction` |
| `asserted_known_unknown` | `param, patterns[]` | 待估未知量被断言为已知值（不论数值）——反问题专用 | `wrong_task_type` |
| `sign_relation` | `quantity, canonical, sign_patterns[]` | 抽取带符号关系式，符号与 `canonical`（含外法向约定的规范式）比对 | `numeric_contradiction` |
| `arithmetic_consistency` | `quantities{name: patterns[]}, expression` | 计划给出的多个数代入 `expression`（如 `total >= 0.1*(ppw*n_wl)**2`）；**全部**量抽到且表达式为假才矛盾（精确率优先）。单量 + 上界表达式（`n <= 20000`）即公开预算合规检查的惯用法 | `internal_inconsistency` |
| `co_occurrence` | `pattern_a, pattern_b, scope` | 两个模式共现即结构矛盾（如"通量条件"ד值约束式"）；`scope: "facet" \| "plan"` | `structural_contradiction` |
| `claim_without_support` | `pattern, support_patterns[], scope` | 断言出现（pattern）且**全篇无任何**支撑表述（support_patterns 宽松、多同义）即矛盾——"承诺缺口"型：声称唯一恢复无正则化（011）、口头 μ 无结构承诺（017）、软惩罚无监控（018）、实值表示无复数处理（020）、逐项残差缺耦合项（024） | `unsupported_claim` |
| `forbidden_assertion` | `patterns[]` | 断言本身与规格矛盾，出现即检出：B 物种被观测（013）、绝对压力可恢复（018）、法向导数连续（019）、截断边界反射墙（022） | `spec_contradiction` |

- `patterns` 为正则列表，恰一个数值捕获组（`sign_patterns` 捕获符号
  token）；命中首个模式即停（沿用 claim_verifier 现行为，避免宽模式重复计）。
- **任务级字段** `task_type_decl: "forward" | "inverse"` 与 claims 并列
  （正/反声明的抽取模式是全局的，留在 verifier 代码里；哪个方向是错的
  由本字段决定）。`fabricated_component` 检测与任务无关，整体留在代码。
- **精确率优先政策不变**（scorer_v04 README）：cap 只在断言无歧义矛盾时
  触发。每条 claim 的 patterns 必须过 §6 的回归套件（金计划零误伤）才算
  转写完成。
- 机器化不了的断言**不硬塞**：写不出高精确率 patterns 的支点，退到
  `facet_cap_rules` 的 `trigger: "cue"`（v0.3 线索覆盖机制），并在
  CHANGELOG 记"暂未机器化"。宁可少一条 claim，不可多一次误伤。
  （v0.4 落地结果：002/006/012 为全 cue 题，见 `dataset/CHANGELOG_v0.4.md`。）
- **`selftest` 字段（必填）**：每条 claim 自带 `{gold, tamper}` 两段测试文本，
  金文本必须零误伤、篡改文本必须检出——测试向量与 patterns 同址存放，
  `validate_dataset_v04.py` 全量回放，全绿是"转写完成"的机器判据（§5 步骤 3）。
- **两条标准规则由构建自动附加**、无需 claim 显式引用：`cap_wrong_task_type`
  （有 `task_type_decl` 的条目；正/反声明模式是全局的，留在 verifier 代码）、
  `cap_fabricated_component`（全条目；杜撰组件检测与任务无关）。

### 3.3 `facet_cap_rules` v0.4 结构（D2 的落地）

v0.3 的四字段（`condition, affected_facets, max_score, rationale`）保留，
新增 2 个：

| 字段 | 类型 | 说明 |
|---|---|---|
| `rule_id` | str | 题内唯一，snake_case；claims 的 `on_contradiction` 引用它 |
| `trigger` | str | `"claim"`：由 verifier 的 finding 触发（机器判定）；`"cue"`：由 v0.3 线索覆盖层判定；`"generic"`：全题通用规则（generic-PINN cap） |

- **单一事实源**：v0.4 评分器只从本字段执行 cap。`trigger: "claim"` 的
  规则由 verifier 的 findings 触发；`"cue"/"generic"` 的沿 v0.3
  机制，但规则文本以 JSONL 为准，代码不再内嵌逐题条件。
- **`affected_facets: []` 约定**：空列表 = 封顶"检出所在 facet"（v0.3
  hallucination cap 语义——数值矛盾封顶它出现的那个 facet）。
- 015/017/020 等"判定方式升级"的既有规则：保留 v0.3 的 `condition` 原文，
  `trigger` 从 `"cue"` 改 `"claim"` 并挂上新 claim——CHANGELOG 可直接
  diff 出"升级了判定、没改判定内容"，这就是论文里"cap 规则开/关重打分"
  消融（修订项 #2）需要的可追溯性。

### 3.4 评分器消费契约

```
findings = verify_arm(task_id, {display_name: text})   # 读 verifiable_claims
caps     = resolve(findings → on_contradiction → rule_id)
scores   = coverage_layer(...)                          # v0.3 给分层不变
final    = apply_caps(scores, caps ∪ cue_caps ∪ generic_caps)
```

- verifier 内部统一用 facet_id，入口处按 §2.2 映射表把显示名折成 id。
- cap 语义不变：受影响 facet 封顶 `max_score`；多规则命中取最小值。

## 4. 全样例：`medium_heat_mixed_bc_014`（重写 + 兼并 001 槽位）

以下两条即 014 在 v0.4 两个 JSONL 文件中的完整条目草案。
（`// ←` 注释仅本文档标注用，实际文件为纯 JSONL。）

> **✔ 符号规范式已确认（2026-07-13）**：私有规范式采用
> `k·u_x(L,t) = +q_in`（q_in > 0）。约定：外法向 n = +x̂，边界外流通量
> = −k·u_x(L,t)，"注入"⇔ 外流为负 ⇔ k·u_x(L,t) = +q_in。
> 重写规格 MD 初稿曾误写 `−k·u_x(L,t) = +q（注入）`——物理上是抽热，
> **符号陷阱抓住了规格作者自己**，转写核对时检出。事故记录保留于
> `task_rewrites_v0.4/014_heat_mixed_bc.md` 编写注记，作为"符号支点必须
> 机器核验"的一手证据（论文设计决策表素材）。

### 4.1 `tasks_public_v0.4.jsonl` 条目

```jsonc
{
  "id": "medium_heat_mixed_bc_014",
  "difficulty": "medium",
  "domain": "heat_transfer",
  "pde_system": "1D heat equation",
  "task_type": "boundary_condition_handling",
  "tags": ["1d", "parabolic_pde", "mixed_bc", "dirichlet_bc",
           "neumann_bc", "neumann_flux_injection",          // ← 新增
           "energy_balance", "pinn"],                        // ← 新增
  "source_provenance": {
    "category": "canonical_pde",
    "primary_reference": "Classic PDE / boundary condition stress test",
    "note": "Adapted as a natural-language planning task; no numerical data copied."
  },
  "problem": "A researcher models heat conduction in a one-dimensional rod. One end is held at a fixed temperature. At the other end, heat is injected into the rod at a prescribed constant rate through the boundary surface. The initial temperature profile is known, and the material properties are given. Design a physics-informed modeling workflow for the temperature field. Make the boundary treatment fully explicit: write the flux condition as a signed relation between the outward normal derivative and the stated injection rate, and explain how you verify the sign is physically correct. Include in your validation an energy-balance check relating the change of total thermal energy in the rod to the boundary fluxes, with a tolerance.",   // ← MD 题面草案原文
  "output_schema": ["Problem Formalization", "Physics Constraints",
                    "Model Choice", "Training Strategy",
                    "Validation Failure Risks"]              // ← §2.2 规范显示名
}
```

### 4.2 `references_private_v0.4.jsonl` 条目

```jsonc
{
  "id": "medium_heat_mixed_bc_014",
  "schema_version": 2,                                       // ← §3.1
  "scoring_version": "pim_planscore_private_v0.4",           // ← §3.1
  "revision": "rewritten",                                   // ← §3.1
  "supersedes": ["easy_heat_1d_dirichlet_001"],              // ← §3.1（兼并 001）
  "public_metadata": { /* 同公开条目，略 */ },

  "canonical_pde": "u_t = alpha * u_xx, with alpha = 1.0",
  "variables": ["x", "t", "u(x,t)"],
  "known_parameters": ["alpha = 1.0", "k = 1.0", "q_in = 0.5"],
  "unknowns": ["u(x,t)"],
  "constraints": {
    "initial_condition": "u(x,0) is given; reference instance: u(x,0)=0",
    "boundary_conditions": [
      "Dirichlet u(0,t)=0 at the left end",
      "flux injection at the right end: k*u_x(1,t) = q_in, i.e. -k*du/dn = q_in with outward normal n=+x"
    ]                                                        // ← 符号规范式，待作者复核（见 ⚠）
  },
  "domain_spec": {"space": "x in [0,1]", "time": "t in [0,1]"},
  "parameter_values": {"alpha": "1.0", "k": "1.0", "q_in": "0.5"},  // ← 私有实例值，作者定稿
  "reference_conditions": {
    "initial": "u(x,0)=0",
    "boundary": ["u(0,t)=0", "k*u_x(1,t)=+0.5 (injection)"]
  },
  "analytic_solution": "steady state u_s(x)=q_in*x/k plus classical eigenfunction transient; series solution available for the reference instance",   // ← MD delta"常通量+定温端经典级数解"

  "task_type_decl": "forward",                               // ← §3.2 任务级字段

  "verifiable_claims": [                                     // ← §3.2 新字段
    {
      "claim_id": "flux_sign",
      "type": "sign_relation",
      "basis": "spec",
      "facets": ["physics_constraints"],
      "description": "计划写出的右端通量条件符号必须与'注入'方向一致（外法向约定）",
      "quantity": "k*u_x(1,t) vs q_in",
      "canonical": "+",                                      // ← k*u_x(L,t) = +q_in
      "sign_patterns": [
        "([+-]?)\\s*k\\s*\\*?\\s*u_x\\(\\s*(?:1|L)\\s*,\\s*t\\s*\\)\\s*=\\s*([+-]?)\\s*q",
        "([+-]?)\\s*k\\s*(?:\\*|\\s)\\s*(?:du/dn|u_n)\\s*=\\s*([+-]?)\\s*q"
      ],
      "on_contradiction": "cap_flux_sign"
    },
    {
      "claim_id": "flux_as_value_constraint",
      "type": "co_occurrence",
      "basis": "plan_internal",
      "facets": ["physics_constraints", "training_strategy"],
      "description": "通量条件被当作 u 的值约束施加（而非法向导数约束）",
      "pattern_a": "u\\(\\s*(?:1|L)\\s*,\\s*t\\s*\\)\\s*=\\s*q",
      "pattern_b": "\\b(?:flux|Neumann|injection)\\b",
      "scope": "facet",
      "on_contradiction": "cap_flux_as_value"
    },
    {
      "claim_id": "alpha_value",
      "type": "param_value",
      "basis": "spec",
      "facets": ["problem_formalization", "physics_constraints"],
      "description": "计划若断言具体 alpha 数值，须与私有实例一致（公开题面无数值）",
      "param": "alpha",
      "true_value": 1.0,
      "rtol": 0.01,
      "patterns": [
        "(?:diffusivity|alpha)\\s*(?:=|of)\\s*([0-9.eE+-]+)"
      ],
      "on_contradiction": "cap_hallucinated_value"
    }
  ],

  "facet_cap_rules": [                                       // ← §3.3 结构
    {
      "rule_id": "cap_generic_pinn",
      "trigger": "generic",                                  // ← v0.3 通用规则原样保留
      "condition": "answer gives only a generic PINN workflow without task-specific residuals, constraints, or risks",
      "affected_facets": ["problem_formalization", "physics_constraints",
                          "model_choice", "training_strategy",
                          "validation_failure_risks"],
      "max_score": 3,
      "rationale": "Generic correctness should not receive full credit in a task-specific planning benchmark."
    },
    {
      "rule_id": "cap_flux_sign",
      "trigger": "claim",                                    // ← 机器判定（新）
      "condition": "flux boundary condition stated without an explicit sign convention tied to the outward normal, or with a sign inconsistent with the stated physical direction of heat flow",
      "affected_facets": ["physics_constraints", "training_strategy"],
      "max_score": 2,
      "rationale": "Sign error turns heating into cooling; execution necessarily diverges from the reference."
    },
    {
      "rule_id": "cap_flux_as_value",
      "trigger": "claim",                                    // ← 机器判定（新）
      "condition": "flux condition enforced as a value constraint on u rather than on its normal derivative",
      "affected_facets": ["physics_constraints"],
      "max_score": 2,
      "rationale": "Mistakes the mathematical type of the boundary condition."
    },
    {
      "rule_id": "cap_no_energy_balance",
      "trigger": "cue",                                      // ← 暂不机器化（§3.2 政策）
      "condition": "validation contains no energy-balance or flux-consistency check",
      "affected_facets": ["validation_failure_risks"],
      "max_score": 3,
      "rationale": "The energy budget d/dt ∫u dx = boundary net flux is the fundamental physical consistency check for this task."
    },
    {
      "rule_id": "cap_hallucinated_value",
      "trigger": "claim",
      "condition": "plan asserts a specific numeric value contradicting the private instance (public statement contains no numbers)",
      "affected_facets": ["problem_formalization", "physics_constraints"],
      "max_score": 2,
      "rationale": "Hallucinated specification values."
    },
    {
      "rule_id": "cap_same_bc_type",
      "trigger": "cue",                                      // ← v0.3 规则保留
      "condition": "treats both boundaries as the same type",
      "affected_facets": ["physics_constraints", "training_strategy"],
      "max_score": 2,
      "rationale": "The stress test is mixed BC handling."
    }
  ],

  "failure_traps": [                                         // ← v0.3 + MD delta 三条
    "treats both boundaries as Dirichlet",
    "omits derivative boundary loss",
    "omits initial condition",
    "flux sign inconsistent with stated direction",
    "flux enforced as value constraint",
    "no energy balance validation"
  ],
  "critical_points": {
    "problem_formalization": [
      "identifies 1D heat equation with mixed Dirichlet/flux boundary conditions",
      "translates 'heat injected' into a signed normal-derivative condition",
      "states the outward-normal sign convention explicitly"
    ],
    "physics_constraints": [
      "includes heat residual and initial-condition loss",
      "includes Dirichlet value loss at x=0",
      "includes signed flux (Neumann derivative) loss at x=1 with correct sign",
      "does not enforce the flux as a value constraint on u"
    ],
    "model_choice": [
      "chooses PINN with autodiff for the boundary derivative",
      "justifies how the derivative constraint is represented"
    ],
    "training_strategy": [
      "samples interior, initial, Dirichlet-boundary, and flux-boundary points",
      "balances derivative and value boundary losses",
      "verifies the flux sign against the physical direction before training"
    ],
    "validation_failure_risks": [
      "energy-balance check: rate of change of total thermal energy vs net boundary flux, with tolerance",
      "field error against the series/steady reference",
      "separate Dirichlet and flux boundary errors",
      "names flux sign error as an explicit failure risk"
    ]
  },
  "expected_loss_terms": [ /* v0.3 基础上随支点微调，略 */ ],
  "expected_training_strategy": [ /* 同上，略 */ ],
  "expected_validation": [ /* 同上 + energy balance，略 */ ],
  "rubric": {"problem_formalization": 2, "physics_constraints": 2,
             "model_choice": 2, "training_strategy": 2,
             "validation_failure_risks": 2},
  "facet_score_scale": { /* v0.3 原样，略 */ },
  "human_review": "RESOLVED v0.4: sign convention k*u_x(1,t)=+q_in confirmed (outward normal, injection positive); instance values q_in/alpha/IC pending author finalization",
  "scoring_tags": ["medium", "heat_equation", "mixed_bc", "neumann_flux",
                   "sign_convention", "energy_balance"],
  "review_flags": []
}
```

### 4.3 本题验收对账（对重写规格 MD"验收判据"）

- `cap_flux_sign` 至少在 1 个模型输出上触发（MD：符号 cap ≥1 次）
- 均分从 23.3 显著下降；spread ≥ 4
- 55 臂回归套件加 014 的金计划臂 + 符号篡改臂：金计划零误伤、篡改臂必中

## 5. 转写流程（每题；已于 2026-07-13 全量执行）

1. 重写规格 MD 审定 → `problem` 终稿、claims、cap 规则、私有实例值确定
2. 写公开条目（§2）+ 私有条目（§3）——落地为
   `update_v04/scripts/rewrites_v04_payloads.py`（逐题 payload）+
   `build_dataset_v04.py`（v0.3 基线合成，可复现构建）
3. 每条 claim 配一对回归文本：金表述（不许误伤）+ 篡改（必须检出），
   以 `selftest` 字段随 claim 同址存放
4. 过校验脚本（§6）+ selftest 全绿 → 该题标记"转写完成"

消费端：`update_v04/scorer_v04/claim_verifier_v04.py`（通用加载器，
取代 v0.3 硬编码 SPECS；执行子集 5 题规格已迁入数据，见 CHANGELOG）。

## 6. 校验脚本（`update_v04/scripts/validate_dataset_v04.py`）

机械检查，全部可自动化：

- [x] 两文件 id 集合一致；公开条目字段集合 = v0.3 schema
- [x] 公开条目不含 `parameter_values`/`reference_conditions` 等私有字段名
- [x] `output_schema` 与 §2.2 显示名逐字一致
- [x] claims/cap 规则中的 facet 引用均为合法 snake_case id
- [x] 每个 `on_contradiction` 都指向本题存在的 `rule_id`；每个
      `trigger:"claim"` 的规则至少被一条 claim 引用（标准自动规则除外）
- [x] `patterns` 均可编译、捕获组数与类型匹配（param_value/quantities 恰 1，
      sign_patterns 恰 2）；`expression` 只引用已定义量
- [x] `supersedes` 引用的 id 存在于 v0.3 文件且不存在于 v0.4 文件
- [x] `revision` 字段与 CHANGELOG_v0.4.md 逐题一致（含被移除条目的记录行）
- [x] 全部 claim 的 selftest 回放：金零误伤 / 篡改必检出（28×2 = 56 用例）

（2026-07-13 首次全量运行：26 条目 / 28 claims / 56 selftests，PASS。）

## 7. 开放项（作者决策）

~~0. 014 符号规范式~~ ——已拍板（2026-07-13）：`k·u_x(L,t) = +q_in`，见 §4。

1. **q_in / alpha / IC 的私有实例值**：样例中 `q_in=0.5, alpha=k=1.0,
   u(x,0)=0` 为占位，作者定稿。
2. **能量收支断言的机器化层级**：本稿按"暂不机器化"（`trigger:"cue"`）；
   若作者要机器化，可加 `arithmetic_consistency` claim 抽取计划声明的
   收支两侧——但高精确率 patterns 难写，建议 v0.4 先 cue、v0.5 再升级。
3. **`basis:"plan_internal"` 的 claims 是否随论文公开**：本稿立场是抽取
   模式全私有、只公开分类统计（几题几条、两类占比）；若审稿人要透明度，
   可公开 claim 的 `description` 层（不含 patterns）。
