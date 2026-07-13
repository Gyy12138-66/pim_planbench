# PIM-PlanBench 数据集 CHANGELOG v0.3 → v0.4

- 依据：`update_v04/docs/item_analysis_v0.4.md`（处置清单）、
  `update_v04/task_rewrites_v0.4/`（16 份重写规格）、
  `update_v04/docs/dataset_schema_v0.4.md`（落地格式，含 D1–D3 决定）。
- v0.4 = 完整快照（25 题 + 1 canary）；v0.3 文件原地冻结，按治理政策随
  v0.5 发布解密。构建可复现：`update_v04/scripts/build_dataset_v04.py`；
  校验：`update_v04/scripts/validate_dataset_v04.py`。
- 全库新增：`verifiable_claims`（28 条，含 selftest）、cap 规则结构化
  （`rule_id` + `trigger: claim|cue|generic`）、治理字段
  （`schema_version/scoring_version/revision/supersedes`）。

## 逐题记录

| id | revision | 变更摘要 |
|---|---|---|
| `easy_wave_1d_icbc_002` | rewritten | 支点=导数级速度 IC + 角点相容性；全 cue 题（能量阈值断言 v0.5 再机器化） |
| `easy_poisson_2d_source_003` | unchanged | 保留（区分健康）；执行子集规格迁入 claims（源系数 2π²） |
| `easy_burgers_1d_periodic_004` | rewritten | 支点=黏性层分辨经济学；公开预算 20k 点/30k 步 → 2 条预算合规 claims |
| `easy_advection_1d_periodic_005` | unchanged | 保留；执行子集规格迁入 claims（c=1.0） |
| `easy_reaction_diffusion_1d_006` | light_edit | 题面加行波前沿定量要求；2 条 cue cap；备选：与 013 槽位整合待 #1b |
| `medium_laplace_L_corner_007r` | relocated | 原 easy_laplace_2d_boundary_007 重定位为 L 形域凹角题（easy→medium）；指数 2/3 对账 claim |
| `medium_advection_diffusion_008` | unchanged | 保留（Péclet 权衡有效；023 预注册替补） |
| `medium_heat_inverse_alpha_009` | unchanged | 保留（反问题槽位正常）；补 task_type_decl=inverse |
| `medium_burgers_inverse_viscosity_010` | unchanged | A− 观察挂起（见下）；ν-已知断言迁入 claims（\bknown 词界修正） |
| `medium_poisson_source_recovery_011` | rewritten | 支点=源不可辨识性；"唯一恢复无正则化"claim |
| `medium_wave_sparse_sensors_012` | rewritten | 支点=可观测性论证强制化；全 cue 题（锥覆盖对账 v0.5 再机器化） |
| `medium_reaction_diffusion_noisy_013` | rewritten | 支点=噪声感知目标 + B 物种零观测；2 条 claims（未加权 MSE / B 被观测） |
| `medium_heat_mixed_bc_014` | rewritten | 兼并 001 槽位；支点=通量符号（k·u_x(1,t)=+q_in，外法向）+ 能量收支；3 条 claims |
| `medium_periodic_advdiff_015` | light_edit | 题面改枚举式承诺；值周期-无导数周期 trap 从 cue 升级为 claim |
| `hard_allen_cahn_016` | unchanged | A− 观察挂起（见下）；执行子集规格迁入 claims（d=1e-4） |
| `hard_cahn_hilliard_017` | rewritten | 支点=μ-分裂结构承诺；2 条 claims（口头 μ / 守恒无阈值）；v0.3 五条 cap 保留 |
| `hard_navier_stokes_2d_018` | rewritten | 支点=压力规范 + 散度控制；2 条 claims（绝对压力 / 软惩罚无监控） |
| `hard_darcy_heterogeneous_019` | rewritten | 支点=保守形式 vs 非法展开；2 条 claims（展开无光滑化声明 / 法向导数连续） |
| `hard_helmholtz_high_frequency_020` | light_edit | 题面公开 ≈20 波长量级；PPW 算术三元组 claim（内部一致性旗舰）+ 实值升级 claim |
| `hard_plus_helmholtz_staircase_021` | rewritten | 支点=角奇异×高频×预算分配；2 条 claims（指数 2/3 / 40k 预算） |
| `hard_plus_acoustic_scattering_maze_022` | rewritten | 支点=辐射条件 + 场分解；反射墙 forbidden_assertion claim |
| `hard_plus_euler_shock_023` | unchanged | 保留（全基准最佳题）；执行子集规格迁入 claims（γ=1.4） |
| `hard_plus_rayleigh_benard_024` | rewritten | 支点=Boussinesq 双向耦合 + Nu 双边收支；2 条 claims（动量无浮力 / 温度无平流） |
| `hard_plus_mhd_divergence_025` | unchanged | A− 观察挂起（见下） |
| `hard_plus_multiscale_darcy_026` | unchanged | 保留（单解 vs 算子代理支点有效） |
| `easy_heat_1d_dirichlet_001` | merged | **移除**：并入 014（同物理槽位，教科书题无支点可装）；v0.3 条目原地冻结即归档；编号槽位留给 #1b 新题 |
| `easy_laplace_2d_boundary_007` | relocated | **旧 id 退役**：重定位为 `medium_laplace_L_corner_007r`（见上）；v0.3 条目冻结归档 |
| `canary_pim_planbench_v0_4` | new | 污染探针（GSM1k 式）；评分与统计按 `canary_` 前缀排除 |

## A− 三题裁决记录（依执行效度解盲结果，2026-07-13）

预注册判据（item_analysis §4-A−）：H4a 任务内 ρ **显著**为负则保留，且裁决
依赖修订项 #3（×5 采样）。解盲结果（`update_v04/execution_validation/analysis_v0.4/`）：

- **010**：H4a ρ = −0.205（p=0.63，N 臂）/ −0.537（p=0.11，全臂）——方向对、
  不显著（n_arms=8 功效不足）。H4b 侧强证据：ν 恢复误差 T/D 臂为自然臂的
  20–52 倍。**处置：保留 + 观察挂起至 ×5 采样**；反问题维度按 §5 接口
  反馈覆盖矩阵扩容论证。
- **016**：H4a ρ = −0.611（p=0.108）——全子集最接近显著、方向正确。
  **处置：保留 + 观察挂起**。
- **025**：不在执行子集，无新证据。**处置：保留 + 观察挂起至 ×5 采样**。

三题均打 `review_flags` 观察标记；未触发重写，v0.5 依 ×5 采样与（可选）
执行效度第二轮复裁。

## 全 cue 题（schema §3.2 机器化政策的如实记录）

002 / 006 / 012 三题重写后暂无 verifiable_claims：其支点断言（能量漂移阈值、
前沿尺度公式、影响锥覆盖）需要高精确率抽取模式，v0.4 版本写不出即不硬塞，
全部 cap 以 `trigger:"cue"` 落地，v0.5 复评机器化可行性。

## Scorer 侧同步

- 执行效度 5 题（003/005/010/016/023）的硬编码规格
  （`scorer_v04/claim_verifier.py` SPECS，协议 §3 冻结）已全量迁入
  `verifiable_claims`；010 的 known-viscosity 模式补 `\b` 词界（原模式会误中
  "unknown viscosity"，迁移时修正，v0.3 SPECS 文件不动保持冻结）。
- 新核验器：`scorer_v04/claim_verifier_v04.py`（通用加载器，7 种 claim 类型
  + 2 全局检查）；cap 应用完全由数据侧 `facet_cap_rules` 驱动，
  `score_3modeloutput_v03.py` 的 `hard_trap_caps()` 硬编码路径在 v0.4 废止（D2）。
- 28 条 claims 每条自带 gold/tamper selftest，
  `validate_dataset_v04.py` 全绿为转写完成判据（金零误伤 / 篡改必检出）。
- **迁移等价性证据**：55 臂回归集上新旧核验器 cap 级输出逐臂对拍，
  0 不一致（10 篡改臂检出、45 臂零误伤维持）；规格对账类 claim 的扫描
  范围为全部 5 facet（还原 v0.3"断言出现在哪个 facet 都算"语义，封顶
  检出所在 facet）。

## 待作者定稿（不阻塞面板重跑准备）

- 各重写题私有实例值目前为占位（`human_review: DRAFT ...pending author
  finalization`）；014 符号规范式已 RESOLVED（2026-07-13）。
- 006 的槽位整合备选、021/022 私有几何精确参数化、#1b 新题（001/007 空出
  槽位）随覆盖矩阵推进。
