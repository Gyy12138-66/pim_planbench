# 计算任务总控（run 文件夹）

每个待计算项对应一个脚本与一条命令。全部脚本可从任意目录调用（内部自行定位）。

## A 阶段：随时可跑（验证性，分钟级，不依赖任何待定决策）

| # | 计算内容 | 脚本 | 命令 | 耗时 | 输出 |
|---|---|---|---|---|---|
| 01 | 参考解自检（Sod 星区/Burgers 奇对称/AC 值域） | `01_references_selftest.sh` | `bash update_v04/run/01_references_selftest.sh` | 5–15 分钟 | 终端 PASS/FAIL |
| 05 | 评分器 v0.4 回归套件（R1–R5 发布门） | `05_scorer_regression.sh` | `bash update_v04/run/05_scorer_regression.sh` | <1 分钟 | `scorer_v04/regression_report.md` |
| 06 | Item 区分度指标（26 题 spread/ρ/饱和率，可复现版） | `06_item_metrics.py` | `python3 update_v04/run/06_item_metrics.py` | <1 分钟 | `docs/item_metrics_v0.4.csv` + 终端表 |

## B 阶段：全量执行运行（等你选路启动，唯一的重计算）

| # | 计算内容 | 脚本 | 命令 | 耗时 | 输出 |
|---|---|---|---|---|---|
| 02 | **全量 150 次训练（本机 MPS 路线）**：生成镜像配置+后台启动+断点续跑 | `02_full_run_mps.sh` | `bash update_v04/run/02_full_run_mps.sh` | ≈2.5–3 天（后台） | `execution_validation/results_v0.4.csv` |
| 02b | 同上（云 CUDA 路线，租用机上执行） | `02b_full_run_cuda.sh` | 租用机 repo 根目录：`bash update_v04/run/02b_full_run_cuda.sh` | ≈15–20 GPU·时 | 同上 |
| 03 | 运行进度查看（多天任务的看板） | `03_status.sh` | `bash update_v04/run/03_status.sh` | 即时 | 已完成 run 数/151、最近日志 |
| 04 | **执行效度分析（H4a/H4b/H4c 解盲出报告）** | `04_analyze_validity.sh` | `bash update_v04/run/04_analyze_validity.sh` | 1–2 分钟 | `execution_validation/analysis_v0.4/validity_summary.md` + 散点图 |

前置链：01 →（02 或 02b）→ 03 监控 → 04。02 与 02b 二选一,**全部 150 次同一设备**
（设备一致性决策见 `execution_validation/RUN_LOCAL_MPS.md`）。中断后重复同一命令续跑。

## C 阶段：等外部输入后的计算

| # | 计算内容 | 脚本 | 命令 | 等什么 | 输出 |
|---|---|---|---|---|---|
| 07 | IAA 一致性分析（加权 κ / Krippendorff α / 排名 τ + 判定） | `07_analyze_iaa.sh`（调 `scripts/analyze_iaa.py`，已含 `--demo` 自检） | `bash update_v04/run/07_analyze_iaa.sh --demo`（现在）/ `bash update_v04/run/07_analyze_iaa.sh <iaa_scores_raw.csv>`（数据到位后） | 外部标注者完成打分 | `iaa_report_v0.4.md` |
| 06 复跑 | 重写题验收（满分率<15%、spread≥4、难度梯度、trap 复活） | 同 06 | 同 06（换新评分 CSV：`--scored-csv <path>`） | ③ 重写定稿 + 6 模型重新作答与打分 | 验收对照表 |

## D 阶段：需要 API key 的计算（暂无脚本，待设计）

| 计算内容 | 依赖 | 归属 |
|---|---|---|
| 6 模型对重写题重新作答（06 复跑的前置） | 模型 API（复用 `scripts/run_llm_planner.py`） | #1 验收 |
| 每模型 ×5 采样 + 前沿闭源锚点 + 温度敏感性 | 模型 API，几美元级 | #3 |
| canonical vs colloquial 口语化变体重打分 | 模型 API（同一参考,仅换题面） | 效度框架新增项 |
| LLM 辅助断言抽取（scorer v0.4 泛化） | 模型 API | #2 待你拍板 |

## 当前状态速览

- 唯一硬阻塞的计算 = B 阶段全量运行（等你选 02 或 02b）
- A 阶段三项均已通过（01 于 GPU 机与本机各验证过一次;05/06 本次提交时复验）
- 07 的 `--demo` 自检通过,正式运行等标注数据（协议纪律：脚本先于数据冻结）
