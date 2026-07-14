# 基线与消融包（修订项 #2）

一条命令：`bash update_v04/run/08_baselines_v04.sh`（纯本地重打分，分钟级，无 API）。
产出 `baselines_report.md`；威胁模型定义与全部结论见报告本身。

## 脚本（按执行顺序）

| 脚本 | 作用 | 输出 |
|---|---|---|
| `build_baseline_arms.py` | 构造 T / S1 / S2 / GOLD 四臂 × 26 题 × 5 facet | `generated/baseline_arms_input_v0.4.csv` |
| `score_baselines.py` | 冻结评分器打分（subprocess）+ 与 6 模型面板对比 + T 臂交叉回归 | `generated/baseline_arms_scored_v0.4.csv`、`generated/baseline_task_totals_v0.4.csv` |
| `cap_onoff_rescore.py` | cap 消融：full / no_ext / no_pf / no_caps 四变体重打分 | `generated/cap_onoff_v0.4.csv` |
| `eq5_sensitivity.py` | Eq.5 九常数 OAT + 200 次联合扰动，排名稳定性 | `generated/eq5_sensitivity_v0.4.csv` |
| `make_report.py` | 拼装 `generated/sections/*.md` → 报告 | `baselines_report.md` |

`scorer_mirror.py` 是公共模块：冻结评分器的参数化镜像 + 特征缓存 +
守卫断言（默认参数逐行复现冻结评分器，不等即中止）。

## 纪律

- 冻结评分器 `scripts/score_3modeloutput_v03.py` 只被调用，绝不修改
- 全链确定性可复现（联合扰动随机种子固定 20260713）
- 与修订项 #1 的关系：S1 失守是重写包"可核验断言"设计的实证动机；
  v0.4 重打分后本报告各表复算即论文的 before/after 对比
