## cap 规则开/关重打分（cap 消融）

| 变体 | Kimi-K2.6 | GLM-4.7 | GLM-5.1 | DeepSeek-V4-Flash | deepseek-v4-pro | qwen3.7-max | 排名 τ vs 默认 | 变动行数/780 |
|---|---|---|---|---|---|---|---|---|
| full | 22.15 | 19.92 | 21.81 | 21.12 | 21.12 | 21.19 | 1.000 | 0 |
| no_ext | 22.15 | 20.19 | 21.81 | 21.12 | 21.38 | 21.42 | 0.966 | 10 |
| no_pf | 22.62 | 20.65 | 22.58 | 21.88 | 21.69 | 21.81 | 0.828 | 86 |
| no_caps | 22.62 | 20.92 | 22.58 | 21.88 | 21.96 | 22.04 | 0.966 | 96 |

基线臂在各变体下的均分/25（cap 对反模板防线的贡献）：

| 变体 | GOLD | S1 | S2 | T |
|---|---|---|---|---|
| full | 22.92 | 24.12 | 21.69 | 15.92 |
| no_ext | 23.35 | 24.77 | 22.27 | 16.50 |
| no_pf | 23.35 | 24.12 | 21.81 | 16.35 |
| no_caps | 23.77 | 24.77 | 22.38 | 17.08 |

pf_strict 内部 cap 生效行数（面板 780 行）：86

外部 cap（generic/hard-trap）触发原因 Top 10（面板行）：

- 3 次：smooth strong-form PINN without weak/integral/conservative shock-aware treatment
- 2 次：mentions value periodicity but not derivative or diffusive-flux periodicity
- 2 次：neural operator suggested without many coefficient fields or generalization protocol
- 2 次：does not model coupled velocity and magnetic induction fields
- 1 次：missing magnetic divergence control

全量数据：`generated/cap_onoff_v0.4.csv`。
