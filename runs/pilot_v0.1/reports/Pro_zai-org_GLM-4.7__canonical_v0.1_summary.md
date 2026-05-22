# Pro/zai-org/GLM-4.7 Pilot v0.1 Normalized Output Summary

## Overview

- Normalized file: `C:\Users\user\Desktop\EMNLP2026\pim_planbench\runs\pilot_v0.1\normalized\Pro_zai-org_GLM-4.7__canonical_v0.1.jsonl`
- Total records: **26**
- Schema-valid records: **26/26**
- Schema-invalid records: **0**

## Task Coverage

| Difficulty | Count |
|---|---:|
| easy | 7 |
| medium | 8 |
| hard | 5 |
| hard_plus | 6 |

## Format Diagnostics

All records satisfy the normalized five-section schema. This run is ready for manual scoring.

## Content Pattern Snapshot

These are lightweight text-pattern diagnostics, not benchmark scores.

| Pattern | Count |
|---|---:|
| boundary handling | 26 |
| frequency/spectral strategy | 24 |
| optimizer detail | 23 |
| missing-info awareness | 20 |
| mentions PINN | 12 |
| stiffness awareness | 10 |
| inverse/identifiability awareness | 8 |

## Per-Task Compact Review

| ID                                     | Schema | Model Choice Snapshot                                                                                                                                                      | Training Snapshot                                                                                                                                                            | Risk Snapshot                                                                                                                                                              | Flags                                                                                                                                                           |
| -------------------------------------- | -----: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| easy_heat_1d_dirichlet_001             |     ok | A fully connected Multi-Layer Perceptron (MLP) is selected. Inputs are coordinates $(x, t)$ and output is temperature $u$. The architecture uses 4 hidden layers with 3... | Minimize a composite loss function $L = L_{PDE} + \lambda_{IC} L_{IC} + \lambda_{BC} L_{BC}$. Use random sampling (or Latin Hypercube) to generate collocation points f...   | Potential failure modes include spectral bias preventing the capture of sharp features in the initial profile, optimization getting trapped in local minima leading to...  | optimizer detail, frequency/spectral strategy, boundary handling                                                                                                |
| easy_wave_1d_icbc_002                  |     ok | A standard fully-connected Multi-Layer Perceptron (MLP) with Swish or Tanh activation functions is recommended. The network takes $(x, t)$ as input and outputs $u$. Th... | Employ a physics-informed loss function combining the PDE residual, initial conditions, and boundary conditions: $L = \lambda_{pde}L_{pde} + \lambda_{ic}L_{ic} + \lamb...   | The workflow cannot proceed without defining the domain bounds $L$ and $T$. There is a risk of spectral bias, where the network fails to capture high-frequency feature... | optimizer detail, missing-info awareness, frequency/spectral strategy, boundary handling                                                                        |
| easy_poisson_2d_source_003             |     ok | A fully connected Multi-Layer Perceptron (MLP) is selected. The network takes spatial coordinates $(x, y)$ as input and outputs the scalar field $u$. Hyperbolic tangen... | The loss function is a weighted sum of the PDE residual and boundary condition loss: $L = \lambda_{pde} \mathbb{E}[r_{pde}^2] + \lambda_{bc} \mathbb{E}[r_{bc}^2]$. Col...   | Primary risks include spectral bias, where the network struggles to learn high-frequency features of the source term or boundary conditions, and 'boundary leakage,' wh... | optimizer detail, frequency/spectral strategy, boundary handling                                                                                                |
| easy_burgers_1d_periodic_004           |     ok | A Fully Connected Neural Network (FCNN) with Sinusoidal Representation Networks (SIREN) or Fourier Feature embeddings is recommended. The periodic nature of the proble... | The loss function is a weighted sum: $\mathcal{L} = \lambda_{pde} \mathcal{L}_{pde} + \lambda_{ic} \mathcal{L}_{ic} + \lambda_{bc} \mathcal{L}_{bc}$. $\mathcal{L}_{pde...   | 1. Spectral Bias: Standard networks may struggle to converge to the sharp gradients of the shock profile; Fourier features mitigate but do not eliminate this risk. 2....  | optimizer detail, missing-info awareness, frequency/spectral strategy, boundary handling                                                                        |
| easy_advection_1d_periodic_005         |     ok | A fully connected Multi-Layer Perceptron (MLP) is suitable for this regression task. To inherently satisfy the periodic boundary conditions without soft penalty terms,... | The loss function combines the PDE residual and the initial condition: Loss = λ_pde * MSE(u_t + c u_x) + λ_ic * MSE(u(x,0) - u_0(x)). Collocation points (x, t) are sam...   | Spectral bias in standard MLPs may cause the network to fail in capturing high-frequency components present in the initial profile u_0(x), leading to overly smooth sol... | optimizer detail, frequency/spectral strategy, boundary handling                                                                                                |
| easy_reaction_diffusion_1d_006         |     ok | A Fully Connected Neural Network (FCNN) / Multi-Layer Perceptron (MLP) is selected. The network takes coordinates (x, t) as input and outputs the scalar concentration...  | The loss function is a composite: L = lambda_pde * MSE(f) + lambda_ic * MSE(u(x,0) - u_0) + lambda_bc * MSE(u_boundary - g). Collocation points are sampled randomly (M...   | Primary risks include spectral bias, which may hinder the resolution of sharp gradients or fast transients typical in reaction-diffusion systems. Stiffness in the reac... | optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                                   |
| easy_laplace_2d_boundary_007           |     ok | A Fully Connected Neural Network (MLP) with 3 to 5 hidden layers and 50-100 neurons per layer is recommended. The input layer takes spatial coordinates $(x, y)$, and t... | The loss function is defined as $L = \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc}$, where $L_{pde}$ is the mean squared error of the Laplacian residual and $L_{bc}$ is...    | 1. Spectral bias may prevent the network from accurately learning high-frequency boundary data if $g(x, y)$ is complex. 2. Soft enforcement of boundary conditions may...  | optimizer detail, missing-info awareness, frequency/spectral strategy, boundary handling                                                                        |
| medium_advection_diffusion_008         |     ok | A standard Fully Connected Neural Network (MLP) with 4-6 hidden layers and 50-100 neurons per layer is selected. The activation function should be smooth (e.g., Tanh o... | The loss function is defined as $L = \lambda_{IC} L_{IC} + \lambda_{BC} L_{BC} + \lambda_{PDE} L_{PDE}$. $L_{IC}$ and $L_{BC}$ are Mean Squared Errors (MSE) against th...   | If the advection speed $v$ is high relative to diffusion $D$ (high Peclet number), sharp gradients (shocks) may form, which standard MLPs struggle to resolve due to sp... | optimizer detail, frequency/spectral strategy, boundary handling                                                                                                |
| medium_heat_inverse_alpha_009          |     ok | A Physics-Informed Neural Network (PINN) is selected. The architecture is a fully connected Multi-Layer Perceptron (MLP) with inputs $(x, t)$ and output $u$. The therm... | Loss Function: $\mathcal{L} = \lambda_{data} \mathcal{L}_{data} + \lambda_{PDE} \mathcal{L}_{PDE} + \lambda_{BC} \mathcal{L}_{BC} + \lambda_{IC} \mathcal{L}_{IC}$. $\m...   | 1. Ill-posedness: Without explicit BCs/ICs, the solution is non-unique; the model may converge to a field that fits the data but violates physical reality. 2. Noise Ov... | mentions PINN, optimizer detail, missing-info awareness, frequency/spectral strategy, inverse/identifiability awareness, boundary handling                      |
| medium_burgers_inverse_viscosity_010   |     ok | A Physics-Informed Neural Network (PINN) is suitable because it handles irregular data and naturally incorporates PDE constraints. A fully connected network with input... | The loss function combines data mismatch and physics residual: $L = \lambda_{data} MSE(u_{pred}, u_{obs}) + \lambda_{PDE} MSE(f, 0)$. Since data is sparse, collocation...   | The primary risk is non-uniqueness due to unspecified BCs/ICs; different combinations of $ u$ and boundary values could fit the sparse data. Noise in measurements may...  | mentions PINN, optimizer detail, missing-info awareness, inverse/identifiability awareness, boundary handling                                                   |
| medium_poisson_source_recovery_011     |     ok | Two separate Multi-Layer Perceptrons (MLPs) are selected: $\mathcal{N}_u$ with parameters $\theta$ to approximate the potential field, and $\mathcal{N}_f$ with paramet... | The composite loss function is $L = \lambda_{data} L_{data} + \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc} + \lambda_{reg} L_{reg}$. $L_{data}$ is the MSE on observed p...   | The primary risk is solution non-uniqueness; sparse data may allow multiple valid $(u, f)$ pairs, leading to unphysical oscillations in the recovered source. Spectral...  | optimizer detail, missing-info awareness, frequency/spectral strategy, inverse/identifiability awareness, boundary handling                                     |
| medium_wave_sparse_sensors_012         |     ok | A Physics-Informed Neural Network (PINN) is selected. A fully connected network with inputs $(x,t)$ and output $u$ will approximate the solution. Sinusoidal or Swish a... | Optimization uses a weighted loss balancing data fidelity and physics adherence. Collocation points are sampled randomly (Latin Hypercube) across the domain to enforce...   | Primary risks include solution non-uniqueness due to under-specified boundaries or initial states, leading to physically implausible reconstructions. The model may ove... | mentions PINN, optimizer detail, missing-info awareness, frequency/spectral strategy, inverse/identifiability awareness, boundary handling                      |
| medium_reaction_diffusion_noisy_013    |     ok | A Physics-Informed Neural Network (PINN) with a shared backbone and two output heads for $u$ and $v$. A Multi-Layer Perceptron (MLP) with sinusoidal activations (SIREN... | Minimize a composite loss function $L = \lambda_{data} L_{data} + \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc}$. $L_{data}$ is the MSE between predictions and sparse no...   | 1. Overfitting Noise: The model may fit the measurement noise in $L_{data}$ if the regularization from $L_{pde}$ is insufficient or if the data is extremely sparse. 2.... | mentions PINN, optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, inverse/identifiability awareness, boundary handling |
| medium_heat_mixed_bc_014               |     ok | A fully connected neural network (MLP) with sine or tanh activations is suitable for capturing the smooth dynamics of heat diffusion. The network takes inputs $(x, t)$... | The loss function combines the PDE residual, initial condition, and boundary condition errors: $\mathcal{L} = \lambda_{pde} \mathbb{E}[R^2] + \lambda_{ic} \mathbb{E}[(...   | Risks include poor generalization if the sampling density is insufficient near the boundaries, particularly the Neumann boundary where gradient accuracy is critical. S... | optimizer detail, frequency/spectral strategy, boundary handling                                                                                                |
| medium_periodic_advdiff_015            |     ok | A fully connected neural network (MLP) with periodic input encoding is selected. The raw spatial coordinates $\mathbf{x}$ are transformed into Fourier features $[\sin(... | The loss function is defined as $\mathcal{L} = \lambda_{PDE} \mathcal{L}_{PDE} + \lambda_{IC} \mathcal{L}_{IC}$. No boundary loss term is required due to the hard cons...   | 1. Spectral Bias: The network may fail to resolve high-frequency features in the initial condition or sharp gradients generated by advection, leading to overly smooth...  | optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                                   |
| hard_allen_cahn_016                    |     ok | A Sinusoidal Representation Network (SIREN) or Fourier Feature Neural Network is selected. Standard MLPs suffer from spectral bias, making them inefficient at capturin... | To address stiffness and interface dynamics, employ a time-marching (sequential) training approach, solving for short time intervals $[t_i, t_{i+1}]$ and using the sol...   | The primary risk is interface smearing, where the network fails to capture the sharp transition due to insufficient capacity or spectral bias. Training instability is...  | missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                                                     |
| hard_cahn_hilliard_017                 |     ok | To mitigate the difficulty of training fourth-order derivatives, the model will use a system formulation that decomposes the fourth-order equation into two second-orde... | The loss function is defined as $L = \lambda_{eq1} L_{eq1} + \lambda_{eq2} L_{eq2} + \lambda_{IC} L_{IC} + \lambda_{BC} L_{BC} + \lambda_{mass} L_{mass}$. $L_{eq1}$ en...   | Key risks include: 1) Mass Leakage: The PINN may fail to strictly conserve mass, drifting away from the physical solution over long time horizons. 2) Spectral Bias: Th... | mentions PINN, optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                    |
| hard_navier_stokes_2d_018              |     ok | A Physics-Informed Neural Network (PINN) is selected. The architecture is a fully connected Multi-Layer Perceptron (MLP) with sinusoidal (SIREN) or tanh activations to... | The loss function combines data fidelity and physics residuals: $L = \lambda_{data} L_{data} + \lambda_{mom} L_{mom} + \lambda_{cont} L_{cont}$. $L_{data}$ is the Mean...   | 1) **Ill-posedness due to missing BCs**: Without explicit boundary conditions, the solution may not be unique, potentially leading to unphysical extrapolation near dom... | mentions PINN, missing-info awareness, frequency/spectral strategy, inverse/identifiability awareness, boundary handling                                        |
| hard_darcy_heterogeneous_019           |     ok | A Fully Connected Neural Network (FCNN) or Multi-Layer Perceptron (MLP) is selected to approximate the hydraulic head function $\hat{h}(x; heta)$. The network takes sp... | The loss function is a weighted sum of the PDE residual loss and the boundary condition loss: $L = \lambda_{r} L_{r} + \lambda_{b} L_{b}$. The residual loss $L_{r}$ is...   | The primary risk is the inability of the PINN to converge to an accurate solution if the permeability field $K(x)$ has high contrast (sharp discontinuities or large va... | mentions PINN, optimizer detail, frequency/spectral strategy, inverse/identifiability awareness, boundary handling                                              |
| hard_helmholtz_high_frequency_020      |     ok | A SIREN (Sinusoidal Representation Network) or Fourier Feature Network is selected. Standard MLPs with ReLU activations suffer from spectral bias, making them incapabl... | The loss function combines the PDE residual and boundary conditions: $L = \lambda_{PDE} \mathbb{E}_{x \in \Omega} [\|\nabla^2 u_\theta + k^2 u_\theta - f\|^2] + \lambda_... | The primary risk is spectral bias, where the model converges to a low-frequency 'smoothed' solution that fails to capture the oscillations. If the collocation point de... | optimizer detail, missing-info awareness, frequency/spectral strategy, boundary handling                                                                        |
| hard_plus_helmholtz_staircase_021      |     ok | A standard Physics-Informed Neural Network (PINN) is likely insufficient due to spectral bias (difficulty learning high-frequency functions) and the complex non-convex... | Employ a two-stage optimization strategy: first, use Adam with a learning rate schedule, then switch to L-BFGS for fine-tuning. Implement **curriculum learning** by st...   | Key risks include spectral bias preventing the capture of high oscillations, leading to a trivial zero solution or low-frequency approximation. The sharp corners of th... | mentions PINN, optimizer detail, missing-info awareness, frequency/spectral strategy, boundary handling                                                         |
| hard_plus_acoustic_scattering_maze_022 |     ok | A SIREN (Sinusoidal Representation Networks) based Physics-Informed Neural Network (PINN) is selected. SIRENs are chosen over standard ReLU MLPs because acoustic scatt... | The loss function combines PDE residual, boundary condition enforcement on maze walls, and radiation conditions at the outer limits: $L = \lambda_{pde}L_{pde} + \lambd...   | Primary risks include 'leakage' where the neural network approximates a non-zero field inside solid obstacles due to imperfect boundary enforcement, and spectral bias...  | mentions PINN, optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                    |
| hard_plus_euler_shock_023              |     ok | Standard PINNs relying on pointwise automatic differentiation are unsuitable due to their inability to handle discontinuities. A Conservative Neural Network (CNN) arch... | The loss function should combine: (1) an integral conservation loss evaluated over control volumes (finite volume formulation) rather than pointwise residuals; (2) a b...   | Risks include: (1) Gibbs phenomenon or smearing of shocks if the network acts as a low-pass filter; (2) violation of strict conservation if the architecture does not e... | mentions PINN, optimizer detail, missing-info awareness, stiffness awareness, boundary handling                                                                 |
| hard_plus_rayleigh_benard_024          |     ok | A Physics-Informed Neural Network (PINN) with a Fourier Feature embedding layer is selected. The Fourier features are crucial to capture the high-frequency gradients c... | The loss function combines PDE residuals ($L_{f}$), boundary condition residuals ($L_{b}$), and initial condition residuals ($L_{i}$): $L = \lambda_f L_f + \lambda_b L...   | Primary risks include the inability to resolve thin boundary layers (leading to inaccurate Nusselt number predictions) and violation of mass conservation ($ abla \cdot... | mentions PINN, missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                                      |
| hard_plus_mhd_divergence_025           |     ok | To strictly enforce the divergence-free constraints and avoid unphysical divergence errors inherent in soft penalty methods, the workflow employs a **potential-based n... | 1. **Loss Function**: Minimize a weighted sum of PDE residuals: $L = \lambda_{mom} \mathcal{L}_{mom} + \lambda_{ind} \mathcal{L}_{ind} + \lambda_{cont} \mathcal{L}_{co...   | 1. **Boundary Condition Implementation**: Enforcing specific velocity or magnetic field boundary conditions via potentials ($\psi, A$) can be ill-posed (e.g., difficul... | optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, inverse/identifiability awareness, boundary handling                |
| hard_plus_multiscale_darcy_026         |     ok | The choice depends on the specific goal. For learning across a family of coefficient fields to enable fast inference, a **Neural Operator** (e.g., Fourier Neural Opera... | The loss function combines the PDE residual ($L_{r}$), boundary condition enforcement ($L_{b}$), and potentially data mismatch ($L_{d}$). To handle high-contrast perme...   | Primary risks include spectral bias, where the network fails to capture high-frequency features in the permeability field, leading to inaccurate pressure gradients. St... | mentions PINN, optimizer detail, missing-info awareness, stiffness awareness, frequency/spectral strategy, boundary handling                                    |

## Full Normalized Answers

### easy_heat_1d_dirichlet_001

#### Problem Formalization

Define the spatial domain $x \in [0, L]$ and temporal domain $t \in [0, T]$. The objective is to approximate the temperature field $u(x,t)$ governed by the heat equation $\frac{\partial u}{\partial t} = \alpha \frac{\partial^2 u}{\partial x^2}$. The initial condition is $u(x, 0) = f(x)$ and Dirichlet boundary conditions are $u(0, t) = u_{left}$ and $u(L, t) = u_{right}$. Specific values for $L, T, \alpha, f(x), u_{left}, u_{right}$ are treated as known inputs.

#### Physics Constraints

The model must satisfy the heat equation residual $r = \frac{\partial u}{\partial t} - \alpha \frac{\partial^2 u}{\partial x^2} \approx 0$ throughout the domain. It must strictly adhere to the initial condition $u(x, 0) = f(x)$ and the boundary conditions $u(0, t) = u_{left}$, $u(L, t) = u_{right}$.

#### Model Choice

A fully connected Multi-Layer Perceptron (MLP) is selected. Inputs are coordinates $(x, t)$ and output is temperature $u$. The architecture uses 4 hidden layers with 32 neurons each and Tanh activation functions. This choice provides sufficient capacity to approximate the smooth solution of the diffusion equation while remaining computationally efficient.

#### Training Strategy

Minimize a composite loss function $L = L_{PDE} + \lambda_{IC} L_{IC} + \lambda_{BC} L_{BC}$. Use random sampling (or Latin Hypercube) to generate collocation points for the PDE loss. Sample specifically at $t=0$ for IC and $x=0, L$ for BC. Optimize using Adam for initial convergence followed by L-BFGS for high precision. Weights $\lambda$ are tuned to balance the loss components.

#### Validation Failure Risks

Potential failure modes include spectral bias preventing the capture of sharp features in the initial profile, optimization getting trapped in local minima leading to unphysical solutions, and imbalance in loss terms causing the model to prioritize boundary conditions over the governing PDE in the interior.

### easy_wave_1d_icbc_002

#### Problem Formalization

The objective is to approximate the solution $u(x,t)$ to the 1D wave equation $u_{tt} = c^2 u_{xx}$. The spatial domain is $x \in [0, L]$ and the temporal domain is $t \in [0, T]$. Note: The specific values for the string length $L$ and the final simulation time $T$ are not provided in the task description and must be defined to establish the computational domain. The inputs to the model are coordinates $(x, t)$, and the output is the scalar displacement $u$.

#### Physics Constraints

The model must minimize the residual of the wave equation $f = u_{tt} - c^2 u_{xx}$. It must satisfy the initial displacement condition $u(x, 0) = u_0(x)$ and the initial velocity condition $u_t(x, 0) = v_0(x)$. Finally, it must adhere to the fixed endpoint boundary conditions $u(0, t) = 0$ and $u(L, t) = 0$.

#### Model Choice

A standard fully-connected Multi-Layer Perceptron (MLP) with Swish or Tanh activation functions is recommended. The network takes $(x, t)$ as input and outputs $u$. This architecture is chosen for its simplicity and effectiveness in solving low-dimensional PDEs via automatic differentiation. It is sufficiently expressive to capture the continuous, smooth nature of wave propagation.

#### Training Strategy

Employ a physics-informed loss function combining the PDE residual, initial conditions, and boundary conditions: $L = \lambda_{pde}L_{pde} + \lambda_{ic}L_{ic} + \lambda_{bc}L_{bc}$. Use random sampling (Latin Hypercube or uniform) to generate collocation points in the interior of the domain for the PDE loss, and specific samplers for the boundaries ($t=0$, $x=0$, $x=L$). Optimize using Adam for initial convergence followed by L-BFGS for high precision. Dynamic loss weighting may be required to balance the influence of the PDE against the constraints.

#### Validation Failure Risks

The workflow cannot proceed without defining the domain bounds $L$ and $T$. There is a risk of spectral bias, where the network fails to capture high-frequency features present in the initial conditions. Additionally, soft enforcement of boundary conditions via loss terms may result in 'boundary leakage' (non-zero displacement at endpoints), which can be mitigated by using hard constraints or increasing boundary sampling density.

### easy_poisson_2d_source_003

#### Problem Formalization

The objective is to approximate the scalar field $u(x,y)$ satisfying the Poisson equation $\nabla^2 u = f(x,y)$ on a rectangular domain $\Omega$. Dirichlet boundary conditions $u = g(x,y)$ are prescribed on the boundary $\partial \Omega$. The specific dimensions of the rectangle, the functional form of the source term $f(x,y)$, and the boundary values $g(x,y)$ are not specified; these must be explicitly defined by the user to instantiate the workflow.

#### Physics Constraints

The model must satisfy the governing partial differential equation (PDE) residual $r_{pde} = \frac{\partial^2 u}{\partial x^2} + \frac{\partial^2 u}{\partial y^2} - f(x,y) = 0$ at all collocation points within the domain. Additionally, the solution must strictly adhere to the Dirichlet boundary condition constraint $r_{bc} = u(x,y) - g(x,y) = 0$ on the edges of the rectangle.

#### Model Choice

A fully connected Multi-Layer Perceptron (MLP) is selected. The network takes spatial coordinates $(x, y)$ as input and outputs the scalar field $u$. Hyperbolic tangent ($\tanh$) or Sine ($\sin$) activation functions are recommended to ensure the necessary smoothness for computing second-order derivatives. This architecture is appropriate for continuous field approximation on simple geometries where mesh generation is unnecessary.

#### Training Strategy

The loss function is a weighted sum of the PDE residual and boundary condition loss: $L = \lambda_{pde} \mathbb{E}[r_{pde}^2] + \lambda_{bc} \mathbb{E}[r_{bc}^2]$. Collocation points are sampled using Quasi-Monte Carlo (Sobol) sequences for the interior and uniform sampling for the boundaries. Optimization is performed using the Adam optimizer for initial convergence, followed by the L-BFGS-B algorithm for high-precision refinement. Dynamic loss weighting may be employed if the PDE and BC losses scale disparately.

#### Validation Failure Risks

Primary risks include spectral bias, where the network struggles to learn high-frequency features of the source term or boundary conditions, and 'boundary leakage,' where the model prioritizes the PDE residual over boundary accuracy. Since the complexity of $f(x,y)$ is unknown, an insufficient network width/depth may result in underfitting. Validation must include monitoring the residual error on a separate hold-out set of collocation points to ensure generalization.

### easy_burgers_1d_periodic_004

#### Problem Formalization

The objective is to approximate the velocity field $u(x,t)$ governed by the viscous Burgers equation: $\frac{\partial u}{\partial t} + u \frac{\partial u}{\partial x} = \nu \frac{\partial^2 u}{\partial x^2}$. The spatial domain is periodic, defined as $x \in [0, L]$, and the temporal domain is $t \in [0, T]$. The initial condition is $u(x, 0) = u_0(x)$ (known). The boundary conditions are periodic: $u(0, t) = u(L, t)$ and $\frac{\partial u}{\partial x}(0, t) = \frac{\partial u}{\partial x}(L, t)$. The viscosity coefficient $\nu$ is known. Missing parameters: The domain length $L$ and final simulation time $T$ are not specified and must be defined to set the coordinate scaling.

#### Physics Constraints

The model must satisfy three primary constraints: 1. The PDE residual, representing the conservation of momentum with viscous diffusion, must be minimized across the spatiotemporal domain. 2. The initial condition constraint must be strictly enforced at $t=0$. 3. The periodic boundary conditions must be enforced, ensuring continuity of both the field variable $u$ and its spatial flux $\frac{\partial u}{\partial x}$ at the domain boundaries.

#### Model Choice

A Fully Connected Neural Network (FCNN) with Sinusoidal Representation Networks (SIREN) or Fourier Feature embeddings is recommended. The periodic nature of the problem and the potential for steep gradients (high frequencies) make spectral inductive biases advantageous over standard ReLU or Tanh networks. The network will take coordinates $(x, t)$ as input and output the velocity $u$. The architecture should be sufficiently deep/wide to capture the non-linearity of the convective term.

#### Training Strategy

The loss function is a weighted sum: $\mathcal{L} = \lambda_{pde} \mathcal{L}_{pde} + \lambda_{ic} \mathcal{L}_{ic} + \lambda_{bc} \mathcal{L}_{bc}$. $\mathcal{L}_{pde}$ is the mean squared error of the Burgers equation residual evaluated on collocation points sampled via a Sobol sequence. $\mathcal{L}_{ic}$ enforces the known initial profile. $\mathcal{L}_{bc}$ enforces $u(0,t)=u(L,t)$ and $u_x(0,t)=u_x(L,t)$. An adaptive sampling strategy (e.g., residual-based refinement) should be used to dynamically increase collocation points in regions where steep gradients develop. Optimization should proceed with Adam followed by L-BFGS for precision.

#### Validation Failure Risks

1. Spectral Bias: Standard networks may struggle to converge to the sharp gradients of the shock profile; Fourier features mitigate but do not eliminate this risk. 2. Boundary Violations: If $\lambda_{bc}$ is too low, the solution may drift from periodicity at the boundaries, creating artificial discontinuities. 3. Optimization Imbalance: The PDE loss may dominate the IC loss, leading to a solution that fits the dynamics but ignores the initial state. 4. Viscosity Sensitivity: If $\nu$ is very small, the problem approaches the inviscid limit, making the shock steeper and harder to resolve without adaptive sampling.

### easy_advection_1d_periodic_005

#### Problem Formalization

The task is to solve the 1D linear advection equation ∂u/∂t + c ∂u/∂x = 0 on a spatial domain x ∈ [0, L] and temporal domain t ∈ [0, T]. The objective is to approximate the scalar field u(x, t) given a known constant advection speed c and a known initial profile u_0(x). The domain is periodic, implying u(0, t) = u(L, t). Specific numerical values for L, T, c, and the functional form of u_0(x) are required inputs to the workflow but are not specified in the prompt.

#### Physics Constraints

The model must satisfy the governing PDE residual f = u_t + c u_x = 0 at collocation points within the domain. It must strictly satisfy the initial condition u(x, 0) = u_0(x). The solution must adhere to periodic boundary conditions, requiring continuity of the field and its spatial derivative: u(0, t) = u(L, t) and u_x(0, t) = u_x(L, t).

#### Model Choice

A fully connected Multi-Layer Perceptron (MLP) is suitable for this regression task. To inherently satisfy the periodic boundary conditions without soft penalty terms, the input coordinate x should be transformed using Fourier features (e.g., sin(2πx/L), cos(2πx/L)) before entering the network layers. This architectural choice enforces periodicity by construction and fits the smooth nature of advection problems. The network takes (x, t) as input and outputs u.

#### Training Strategy

The loss function combines the PDE residual and the initial condition: Loss = λ_pde * MSE(u_t + c u_x) + λ_ic * MSE(u(x,0) - u_0(x)). Collocation points (x, t) are sampled randomly via Latin Hypercube Sampling (LHS) across the spatiotemporal domain. Initial condition points are sampled deterministically or randomly at t=0. Optimization should use Adam for initial convergence followed by L-BFGS-B for high precision. Weights λ should be balanced or dynamically adjusted.

#### Validation Failure Risks

Spectral bias in standard MLPs may cause the network to fail in capturing high-frequency components present in the initial profile u_0(x), leading to overly smooth solutions. If the advection speed c is large, sharp gradients may form, requiring careful sampling density. Relying on soft constraints for periodicity (if architectural enforcement is not used) risks boundary leakage. Finally, error accumulation over long time horizons T may occur without temporal resampling.

### easy_reaction_diffusion_1d_006

#### Problem Formalization

The objective is to approximate the scalar concentration field u(x, t) governed by the reaction-diffusion equation: u_t = D * u_xx + R(u). The domain is defined as x in [x_min, x_max] and t in [0, T]. Missing specific values include the diffusion coefficient D, the explicit functional form of the nonlinear reaction term R(u), the domain bounds, and the specific functions for initial and boundary conditions. These must be supplied as inputs to the workflow.

#### Physics Constraints

The model must satisfy the PDE residual f = u_t - D * u_xx - R(u) = 0 at interior collocation points. It must strictly adhere to the initial condition u(x, 0) = u_0(x) and boundary conditions (e.g., Dirichlet u(x_min, t) = g_L, u(x_max, t) = g_R, or Neumann). Physical constraints such as non-negativity of concentration (u >= 0) should be enforced if physically relevant.

#### Model Choice

A Fully Connected Neural Network (FCNN) / Multi-Layer Perceptron (MLP) is selected. The network takes coordinates (x, t) as input and outputs the scalar concentration u. This architecture is appropriate for continuous function approximation on simple 1D geometries and effectively handles the non-linearity of the reaction term via automatic differentiation.

#### Training Strategy

The loss function is a composite: L = lambda_pde * MSE(f) + lambda_ic * MSE(u(x,0) - u_0) + lambda_bc * MSE(u_boundary - g). Collocation points are sampled randomly (Monte Carlo) or quasi-randomly (Latin Hypercube) within the spatiotemporal domain. Optimization utilizes Adam for initial convergence followed by L-BFGS for fine-tuning. Dynamic loss weighting is advised to balance the PDE residual against boundary and initial condition losses.

#### Validation Failure Risks

Primary risks include spectral bias, which may hinder the resolution of sharp gradients or fast transients typical in reaction-diffusion systems. Stiffness in the reaction term can cause optimization instability. Furthermore, if the diffusion coefficient D is small, boundary layers may form that are difficult to capture without adaptive sampling or hard constraint enforcement.

### easy_laplace_2d_boundary_007

#### Problem Formalization

The objective is to solve the Laplace equation $\nabla^2 u = 0$ on a rectangular domain $\Omega = [x_{min}, x_{max}] \times [y_{min}, y_{max}]$. The boundary conditions are Dirichlet type on all four sides, defined as $u(x, y) = g(x, y)$ for $(x, y) \in \partial \Omega$. Missing information includes the specific dimensions of the rectangle and the explicit function $g(x, y)$ defining the boundary values; these must be supplied as inputs to the workflow.

#### Physics Constraints

The solution must satisfy the elliptic PDE $\frac{\partial^2 u}{\partial x^2} + \frac{\partial^2 u}{\partial y^2} = 0$ at all points inside the domain. The solution must strictly adhere to the prescribed Dirichlet boundary conditions on the entire perimeter. The solution is expected to be smooth (harmonic) and satisfy the maximum principle within the interior.

#### Model Choice

A Fully Connected Neural Network (MLP) with 3 to 5 hidden layers and 50-100 neurons per layer is recommended. The input layer takes spatial coordinates $(x, y)$, and the output layer predicts the potential $u$. Activation functions such as Tanh or Sin (SIREN) are preferred to model the smooth potential field. This architecture is chosen for its universal approximation capabilities and compatibility with automatic differentiation for computing the Laplacian.

#### Training Strategy

The loss function is defined as $L = \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc}$, where $L_{pde}$ is the mean squared error of the Laplacian residual and $L_{bc}$ is the mean squared error on the boundaries. Collocation points are sampled inside the domain using Latin Hypercube Sampling or uniform sampling. Boundary points are sampled along all four edges. Optimization should utilize the Adam algorithm for initial training followed by L-BFGS for fine-tuning to achieve high precision.

#### Validation Failure Risks

1. Spectral bias may prevent the network from accurately learning high-frequency boundary data if $g(x, y)$ is complex. 2. Soft enforcement of boundary conditions may result in boundary leakage, where the solution deviates from the exact values at the edges. 3. Imbalanced loss weights ($\lambda_{pde}$ vs $\lambda_{bc}$) can lead to optimization stagnation where the PDE is satisfied but boundaries are incorrect, or vice versa. 4. Insufficient sampling near corners may lead to local inaccuracies in the solution.

### medium_advection_diffusion_008

#### Problem Formalization

The objective is to approximate the solution $u(x,t)$ of the 1D Advection-Diffusion Equation: $\frac{\partial u}{\partial t} + v \frac{\partial u}{\partial x} = D \frac{\partial^2 u}{\partial x^2}$. The domain is defined as $x \in [x_L, x_R]$ and $t \in [0, T]$. Inputs are spatial coordinate $x$ and time $t$. Known parameters include the advection speed $v$ and diffusion coefficient $D$. The workflow utilizes provided initial condition data $u(x, 0)$ and boundary data at $x_L$ and $x_R$. Note that the specific types of boundary conditions (Dirichlet, Neumann, or Robin) are not specified; the workflow must infer or accept these as fixed inputs.

#### Physics Constraints

The model must satisfy the governing PDE residual $f = \frac{\partial u}{\partial t} + v \frac{\partial u}{\partial x} - D \frac{\partial^2 u}{\partial x^2} \approx 0$ throughout the domain. It must also strictly adhere to the initial condition $u(x,0) = u_0(x)$ and the provided boundary conditions at $x_L$ and $x_R$ for all $t > 0$. The physics-informed loss will penalize deviations from these constraints.

#### Model Choice

A standard Fully Connected Neural Network (MLP) with 4-6 hidden layers and 50-100 neurons per layer is selected. The activation function should be smooth (e.g., Tanh or Sin) to allow for accurate calculation of second-order derivatives required for the diffusion term. This architecture is chosen for its ability to approximate continuous functions and its compatibility with automatic differentiation for computing PDE residuals.

#### Training Strategy

The loss function is defined as $L = \lambda_{IC} L_{IC} + \lambda_{BC} L_{BC} + \lambda_{PDE} L_{PDE}$. $L_{IC}$ and $L_{BC}$ are Mean Squared Errors (MSE) against the provided initial and boundary data. $L_{PDE}$ is the MSE of the PDE residual evaluated on a set of collocation points sampled via Latin Hypercube Sampling (LHS) across the $(x,t)$ domain. Optimization will use Adam for the first 1,000 iterations followed by L-BFGS for rapid convergence to a low residual state.

#### Validation Failure Risks

If the advection speed $v$ is high relative to diffusion $D$ (high Peclet number), sharp gradients (shocks) may form, which standard MLPs struggle to resolve due to spectral bias. Incompatibility between the initial condition and boundary conditions at the corners $(x_L, 0)$ and $(x_R, 0)$ can cause optimization instability. Additionally, if the weighting factors $\lambda$ are poorly balanced, the model may prioritize fitting the boundary data over satisfying the transport physics in the interior.

### medium_heat_inverse_alpha_009

#### Problem Formalization

The task is an inverse problem for the 1D heat equation $u_t = \alpha u_{xx}$ on a spatial domain $x \in [0, L]$ and time interval $t \in [0, T]$. The objective is to reconstruct the continuous temperature field $u(x,t)$ and infer the thermal diffusivity $\alpha$ (assumed constant) using sparse, noisy observations $\{(x_i, t_i, u_i)\}$. Missing Information: The Boundary Conditions (BCs) at $x=0, L$ and the Initial Condition (IC) at $t=0$ are not specified. These must be provided or assumed (e.g., Dirichlet, Neumann, or Periodic) to ensure a well-posed formulation.

#### Physics Constraints

1. PDE Residual: The model must satisfy $f(x,t) = u_t - \alpha u_{xx} = 0$ at all collocation points. 2. Positivity: The diffusivity parameter must satisfy $\alpha > 0$. 3. Boundary/Initial Consistency: The solution must adhere to the (required) BCs and ICs. 4. Smoothness: The temperature field $u(x,t)$ is expected to be smooth in space and time for standard heat diffusion.

#### Model Choice

A Physics-Informed Neural Network (PINN) is selected. The architecture is a fully connected Multi-Layer Perceptron (MLP) with inputs $(x, t)$ and output $u$. The thermal diffusivity $\alpha$ is treated as a trainable scalar variable. Justification: PINNs are effective for inverse problems as they embed the PDE directly into the loss function, allowing the model to learn from sparse data while respecting the underlying physics, and they handle the continuous nature of the solution without requiring a mesh.

#### Training Strategy

Loss Function: $\mathcal{L} = \lambda_{data} \mathcal{L}_{data} + \lambda_{PDE} \mathcal{L}_{PDE} + \lambda_{BC} \mathcal{L}_{BC} + \lambda_{IC} \mathcal{L}_{IC}$. $\mathcal{L}_{data}$ is the MSE on the sparse observations. $\mathcal{L}_{PDE}$ is the MSE of the residual evaluated on random collocation points. $\mathcal{L}_{BC}$ and $\mathcal{L}_{IC}$ enforce the (user-specified) boundary and initial conditions. Optimization: Use Adam for initial convergence followed by L-BFGS for high precision. Sampling: Use Latin Hypercube Sampling (LHS) for collocation points to ensure domain coverage.

#### Validation Failure Risks

1. Ill-posedness: Without explicit BCs/ICs, the solution is non-unique; the model may converge to a field that fits the data but violates physical reality. 2. Noise Overfitting: Sparse, noisy data may lead the network to fit the noise rather than the trend, resulting in poor generalization of $\alpha$. 3. Spectral Bias: The network may struggle to reconstruct sharp gradients in the initial temperature profile or boundary layers. 4. Identifiability: If the data is insufficiently rich (e.g., only steady-state), $\alpha$ may not be uniquely identifiable from the loss landscape.

### medium_burgers_inverse_viscosity_010

#### Problem Formalization

The task is an inverse problem for the 1D viscous Burgers equation: $u_t + u u_x = 
u u_{xx}$. The goal is to estimate the unknown constant viscosity parameter $
u$ and reconstruct the velocity field $u(x,t)$ using sparse, noisy measurements. The domain is 1D space $x$ and time $t$. Since boundary and initial conditions are not provided, they must be treated as unknowns or inferred from the data, which introduces non-uniqueness risks.

#### Physics Constraints

The primary constraint is the Burgers PDE residual: $f = u_t + u u_x - 
u u_{xx} = 0$. The viscosity $
u$ is a learnable scalar parameter. Boundary conditions (BCs) and initial conditions (ICs) are physically required for a well-posed forward problem but are missing here. The workflow must either assume generic BCs (e.g., periodic or Dirichlet based on data extent) or treat them as additional learnable parameters constrained by the data.

#### Model Choice

A Physics-Informed Neural Network (PINN) is suitable because it handles irregular data and naturally incorporates PDE constraints. A fully connected network with inputs $(x,t)$ and output $u$ will approximate the solution. The viscosity $
u$ will be a trainable variable. This approach fits the PDE type (non-linear, parabolic) and allows simultaneous estimation of the field and parameter.

#### Training Strategy

The loss function combines data mismatch and physics residual: $L = \lambda_{data} MSE(u_{pred}, u_{obs}) + \lambda_{PDE} MSE(f, 0)$. Since data is sparse, collocation points for the PDE loss will be sampled uniformly across the domain. Adam optimizer will be used for initial training, potentially followed by L-BFGS for precision. $
u$ will be initialized with a positive value and constrained to remain positive to ensure physical stability.

#### Validation Failure Risks

The primary risk is non-uniqueness due to unspecified BCs/ICs; different combinations of $
u$ and boundary values could fit the sparse data. Noise in measurements may lead to overfitting if the physics loss weight is too low. The optimization may also converge to local minima where $
u$ is inaccurate. Validation requires checking consistency on a held-out set of measurements and monitoring the PDE residual.

### medium_poisson_source_recovery_011

#### Problem Formalization

The task is to solve the inverse problem for the Poisson equation $\nabla^2 u(x,y) = f(x,y)$ on a domain $\Omega \subset \mathbb{R}^2$. Given sparse observations of the potential field $u$ at coordinates $\{x_i, y_i\}$ and boundary data on $\partial \Omega$, the goal is to jointly reconstruct the continuous field $u(x,y)$ and recover the unknown source term $f(x,y)$. Missing specifications include the exact domain geometry (assumed rectangular), the specific type of boundary conditions (Dirichlet or Neumann), and the noise level in the observations. The workflow assumes Dirichlet boundary conditions on a unit square but remains adaptable to defined geometries.

#### Physics Constraints

The model must satisfy the Poisson PDE residual $r_{pde} = \nabla^2 \hat{u} - \hat{f} \approx 0$ at all collocation points within the domain. It must also satisfy the boundary constraint $\hat{u}|_{\partial \Omega} = u_{bc}$ (or the equivalent flux condition if Neumann) and the data fidelity constraint $\hat{u}(x_i, y_i) \approx u_{obs}$. To stabilize the ill-posed inverse problem, a regularization term enforcing smoothness or boundedness on the recovered source $\hat{f}$ is recommended.

#### Model Choice

Two separate Multi-Layer Perceptrons (MLPs) are selected: $\mathcal{N}_u$ with parameters $\theta$ to approximate the potential field, and $\mathcal{N}_f$ with parameters $\phi$ to approximate the source term. Decoupling the networks allows for distinct capacity requirements and prevents gradient interference where the field reconstruction might dominate the source learning. Smooth activation functions like Tanh or Sin (SIREN) are preferred to ensure accurate calculation of the second-order derivatives required for the Laplacian.

#### Training Strategy

The composite loss function is $L = \lambda_{data} L_{data} + \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc} + \lambda_{reg} L_{reg}$. $L_{data}$ is the MSE on observed points; $L_{pde}$ is the MSE of the physics residual on random collocation points; $L_{bc}$ enforces boundary conditions; $L_{reg}$ penalizes the magnitude or roughness of $\mathcal{N}_f$. Optimization utilizes Adam for initial convergence followed by L-BFGS for high precision. Dynamic weighting (e.g., SoftAdapt) is suggested to balance the loss terms as the solution evolves.

#### Validation Failure Risks

The primary risk is solution non-uniqueness; sparse data may allow multiple valid $(u, f)$ pairs, leading to unphysical oscillations in the recovered source. Spectral bias in the neural networks may fail to capture high-frequency features in the source term. Incorrect assumptions regarding boundary condition types (e.g., assuming Dirichlet when Neumann is true) will cause global divergence. Finally, overfitting to noisy observation data can violate the physics constraint, necessitating a validation set to monitor PDE residual error.

### medium_wave_sparse_sensors_012

#### Problem Formalization

The objective is to reconstruct the spatiotemporal wave field $u(x,t)$ in 1D given sparse sensor observations $\{u(x_i, t_j)\}$ and a known wave speed $c$. The system is governed by the wave equation $u_{tt} = c^2 u_{xx}$. The problem is ill-posed due to data sparsity and potentially missing initial conditions ($u(x,0), u_t(x,0)$) and boundary conditions ($u(0,t), u(L,t)$). The workflow must explicitly identify these missing constraints and determine if they can be inferred or must be assumed.

#### Physics Constraints

The core constraint is the PDE residual $R = u_{tt} - c^2 u_{xx} = 0$. Boundary conditions (BCs) and initial conditions (ICs) are necessary for well-posedness. If BCs are unknown, the workflow requires assumptions (e.g., Dirichlet, Neumann, periodic) or the inclusion of boundary values as trainable parameters. If ICs are unknown, the model relies on the sparse data and PDE constraint to infer the state, provided the temporal coverage is sufficient for identifiability.

#### Model Choice

A Physics-Informed Neural Network (PINN) is selected. A fully connected network with inputs $(x,t)$ and output $u$ will approximate the solution. Sinusoidal or Swish activation functions are preferred to capture wave-like oscillations. The model minimizes a composite loss function $L = \lambda_{data} L_{data} + \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc} + \lambda_{ic} L_{ic}$, allowing the physics to regularize the solution in regions lacking data.

#### Training Strategy

Optimization uses a weighted loss balancing data fidelity and physics adherence. Collocation points are sampled randomly (Latin Hypercube) across the domain to enforce the PDE. Sensor points are used for the data loss. If BCs/ICs are missing, a sensitivity analysis is required: attempt to train with only data and PDE loss; if the solution diverges or is non-unique, introduce parameterized BCs/ICs and optimize them. The training schedule should use Adam for initial progress followed by L-BFGS for fine-tuning.

#### Validation Failure Risks

Primary risks include solution non-uniqueness due to under-specified boundaries or initial states, leading to physically implausible reconstructions. The model may overfit to sparse sensor noise if the PDE weight is too low. An incorrect wave speed $c$ will cause phase errors. Validation metrics must include the PDE residual on a hold-out set of collocation points and, if possible, verification of wave characteristics (e.g., dispersion relation) at sensor locations.

### medium_reaction_diffusion_noisy_013

#### Problem Formalization

Reconstruct the spatiotemporal concentration fields $u(x,t)$ and $v(x,t)$ for two species from sparse, noisy point measurements. The system is governed by coupled reaction-diffusion equations $\partial_t u = D_u 
abla^2 u + R(u,v)$ and $\partial_t v = D_v 
abla^2 v + R(u,v)$, where the reaction form $R$ is known. Missing information includes the domain geometry (assumed 1D or 2D), boundary conditions (assumed zero-flux/Neumann), initial conditions, and diffusion coefficients $D_u, D_v$ (treated as learnable parameters). The workflow must solve an inverse problem to infer the fields and parameters while filtering noise.

#### Physics Constraints

1. PDE Residuals: The network predictions must minimize the residual of the reaction-diffusion equations at sampled collocation points. 2. Boundary Conditions: Enforce $
abla u \cdot n = 0$ and $
abla v \cdot n = 0$ (Neumann) at domain boundaries to conserve mass, unless specific Dirichlet conditions are provided. 3. Positivity: Concentrations must be non-negative ($u, v \ge 0$), enforced via a softplus output activation. 4. Initial Conditions: The solution must match the state at $t=0$, which may be treated as a learnable parameter if unknown.

#### Model Choice

A Physics-Informed Neural Network (PINN) with a shared backbone and two output heads for $u$ and $v$. A Multi-Layer Perceptron (MLP) with sinusoidal activations (SIREN) or Swish is preferred to better represent spectral content of diffusion fields. PINNs are selected because they naturally handle sparse, irregularly sampled data by embedding the governing PDE directly into the loss function, allowing the model to act as a mesh-free differentiable solver that generalizes beyond the noisy observations.

#### Training Strategy

Minimize a composite loss function $L = \lambda_{data} L_{data} + \lambda_{pde} L_{pde} + \lambda_{bc} L_{bc}$. $L_{data}$ is the MSE between predictions and sparse noisy measurements; $L_{pde}$ is the MSE of the PDE residuals evaluated on random collocation points. Use adaptive loss weighting (e.g., SoftAdapt or uncertainty weighting) to dynamically balance the noisy data fidelity against the physics constraints. Optimization should proceed with Adam for global search followed by L-BFGS for fine-tuning.

#### Validation Failure Risks

1. Overfitting Noise: The model may fit the measurement noise in $L_{data}$ if the regularization from $L_{pde}$ is insufficient or if the data is extremely sparse. 2. Boundary Condition Mismatch: Incorrect assumptions about boundary types (e.g., assuming Neumann when Dirichlet is true) will corrupt the global solution. 3. Stiffness and Gradient Imbalance: Reaction-diffusion systems often involve stiff dynamics, leading to vanishing gradients or difficulty balancing the loss terms for $u$ and $v$. 4. Parameter Identifiability: The diffusion coefficients $D_u, D_v$ may be unidentifiable if the data lacks sufficient temporal or spatial variation.

### medium_heat_mixed_bc_014

#### Problem Formalization

The task involves solving the 1D heat equation $u_t = \alpha u_{xx}$ on a spatial domain $x \in [0, L]$ and time interval $t \in [0, T]$. The boundary conditions are mixed: a Dirichlet condition $u(0, t) = u_{fixed}$ at one end and a Neumann condition $u_x(L, t) = q_{prescribed}$ at the other. The initial condition is $u(x, 0) = u_{init}(x)$. The thermal diffusivity $\alpha$, domain length $L$, time horizon $T$, fixed temperature $u_{fixed}$, flux $q_{prescribed}$, and the specific function $u_{init}(x)$ are not specified. These parameters must be defined or treated as learnable/hyperparameters to proceed with the workflow.

#### Physics Constraints

The model must satisfy the heat equation PDE residual $R = u_t - \alpha u_{xx} = 0$ at all collocation points in the interior. It must strictly enforce the Dirichlet boundary condition $u(0, t) - u_{fixed} = 0$ and the Neumann boundary condition $u_x(L, t) - q_{prescribed} = 0$ at the respective boundaries. The initial condition $u(x, 0) - u_{init}(x) = 0$ must be satisfied at $t=0$. Conservation of energy is implicitly handled by the PDE residual.

#### Model Choice

A fully connected neural network (MLP) with sine or tanh activations is suitable for capturing the smooth dynamics of heat diffusion. The network takes inputs $(x, t)$ and outputs temperature $u$. To handle the mixed boundary conditions effectively, the output can be constructed as $\hat{u}(x,t) = u_{fixed} + x \cdot q_{prescribed} + x(x-L) \cdot NN(x,t)$, where the first term enforces the Dirichlet condition at $x=0$, the second term enforces the Neumann condition at $x=L$ (approximately, or via exact construction), and the last term ensures the PDE is solved in the interior. This architecture reduces the optimization burden by embedding boundary constraints directly into the solution structure.

#### Training Strategy

The loss function combines the PDE residual, initial condition, and boundary condition errors: $\mathcal{L} = \lambda_{pde} \mathbb{E}[R^2] + \lambda_{ic} \mathbb{E}[(u(x,0)-u_{init})^2] + \lambda_{bc} \mathbb{E}[(u(0,t)-u_{fixed})^2 + (u_x(L,t)-q_{prescribed})^2]$. Collocation points should be sampled using Latin Hypercube Sampling (LHS) or a quasi-Monte Carlo method to ensure coverage of the space-time domain. Points should be dynamically re-sampled or weighted to focus on regions of high residual. Optimization should use Adam or L-BFGS, starting with Adam for global search and switching to L-BFGS for precision.

#### Validation Failure Risks

Risks include poor generalization if the sampling density is insufficient near the boundaries, particularly the Neumann boundary where gradient accuracy is critical. Spectral bias may prevent the network from learning high-frequency components in the initial condition if $u_{init}(x)$ is complex. Failure to converge may occur if the weights $\lambda$ are unbalanced; adaptive weighting schemes (e.g., soft-adapt) are recommended. Overfitting to the boundary conditions at the expense of the PDE residual is possible if the boundary loss dominates.

### medium_periodic_advdiff_015

#### Problem Formalization

The task is to solve the Advection-Diffusion equation $\frac{\partial u}{\partial t} + \mathbf{v} \cdot \nabla u = D \nabla^2 u$ on a spatial domain $\Omega \subset \mathbb{R}^d$ over time $t \in [0, T]$. The domain is periodic, meaning $\mathbf{x}$ and $\mathbf{x} + \mathbf{L}$ are identified. The solution $u(\mathbf{x}, t)$ must satisfy periodic boundary conditions $u(\mathbf{x}, t) = u(\mathbf{x} + \mathbf{L}, t)$ and $\nabla u(\mathbf{x}, t) = \nabla u(\mathbf{x} + \mathbf{L}, t)$, along with the initial condition $u(\mathbf{x}, 0) = u_0(\mathbf{x})$. Missing information includes the specific velocity field $\mathbf{v}$ (constant or variable), the diffusion coefficient $D$, the domain dimensions $\mathbf{L}$, and the specific form of the initial condition $u_0$. These must be defined as parameters or inputs to the workflow.

#### Physics Constraints

The model must satisfy the Advection-Diffusion PDE residual exactly at collocation points. It must strictly enforce periodicity in all spatial dimensions to ensure mass conservation and solution continuity across domain boundaries. The initial condition must be satisfied at $t=0$. If the velocity field is non-zero, the transport of the scalar field must be physically consistent with the direction and magnitude of advection relative to diffusion.

#### Model Choice

A fully connected neural network (MLP) with periodic input encoding is selected. The raw spatial coordinates $\mathbf{x}$ are transformed into Fourier features $[\sin(2\pi \mathbf{x}/\mathbf{L}), \cos(2\pi \mathbf{x}/\mathbf{L})]$ before being fed into the network. This architecture choice imposes periodicity as a hard constraint, guaranteeing that the network output is identical at opposite boundaries regardless of the training weights. This is superior to soft penalty methods for periodic domains which often suffer from boundary leakage.

#### Training Strategy

The loss function is defined as $\mathcal{L} = \lambda_{PDE} \mathcal{L}_{PDE} + \lambda_{IC} \mathcal{L}_{IC}$. No boundary loss term is required due to the hard constraint encoding. $\mathcal{L}_{PDE}$ is the Mean Squared Error (MSE) of the PDE residual evaluated on random collocation points sampled uniformly across the spatiotemporal domain. $\mathcal{L}_{IC}$ is the MSE against the initial condition at $t=0$. Optimization uses a two-stage approach: Adam for initial convergence followed by L-BFGS-B for high-precision minimization of the residual.

#### Validation Failure Risks

1. Spectral Bias: The network may fail to resolve high-frequency features in the initial condition or sharp gradients generated by advection, leading to overly smooth solutions. 2. Stiffness: If the Peclet number (ratio of advection to diffusion) is high, the problem becomes advection-dominated, making optimization difficult and prone to instability. 3. Parameter Sensitivity: Incorrect assumptions about missing parameters ($D$, $\mathbf{v}$) will lead to unphysical dynamics. 4. Temporal Drift: Without explicit boundary enforcement, numerical errors might accumulate over time, though the Fourier encoding mitigates spatial drift.

### hard_allen_cahn_016

#### Problem Formalization

The objective is to approximate the solution $u(x,t)$ of the Allen-Cahn equation $\partial_t u = \epsilon^2 \Delta u - f(u)$, where $f(u) = u^3 - u$, on a spatial domain $\Omega$ over time $t \in [0, T]$. The problem involves tracking moving interfaces where $u$ transitions rapidly between phases. Missing specifications include the exact geometry of $\Omega$, the time horizon $T$, the specific boundary condition types (e.g., Dirichlet, Neumann, or Periodic), the explicit initial condition profile $u_0(x)$, and the value of the interface parameter $\epsilon$. These must be defined as inputs to the workflow.

#### Physics Constraints

The model must minimize the residual of the Allen-Cahn PDE. It must strictly satisfy the initial condition $u(x, 0) = u_0(x)$ and the boundary conditions provided (e.g., $\partial_n u = 0$ for no-flux). A key physical constraint is the Lyapunov functional property: the Ginzburg-Landau free energy $E[u] = \int_\Omega (\frac{\epsilon^2}{2}|\nabla u|^2 + F(u)) dx$ must decrease over time ($dE/dt \le 0$), where $F$ is the double-well potential.

#### Model Choice

A Sinusoidal Representation Network (SIREN) or Fourier Feature Neural Network is selected. Standard MLPs suffer from spectral bias, making them inefficient at capturing the high-frequency gradients characteristic of sharp phase interfaces. SIRENs utilize periodic activation functions that allow the network to represent derivatives and high-frequency details natively, which is critical for resolving the interface width $\epsilon$ accurately.

#### Training Strategy

To address stiffness and interface dynamics, employ a time-marching (sequential) training approach, solving for short time intervals $[t_i, t_{i+1}]$ and using the solution at $t_{i+1}$ as the initial condition for the next step. Use residual-based adaptive sampling (RAS) to dynamically concentrate collocation points near the moving interfaces where the PDE residual is highest. Utilize adaptive loss weights (e.g., gradient-based normalization) to prevent boundary/initial condition losses from dominating the stiff PDE loss.

#### Validation Failure Risks

The primary risk is interface smearing, where the network fails to capture the sharp transition due to insufficient capacity or spectral bias. Training instability is likely if the interface parameter $\epsilon$ is very small, leading to a stiff loss landscape. Additionally, the model might violate the energy dissipation law, resulting in unphysical oscillations. Validation metrics must include the $L_2$ error on the interface location and the monitoring of free energy decay.

### hard_cahn_hilliard_017

#### Problem Formalization

The task involves modeling the Cahn-Hilliard equation, a fourth-order nonlinear PDE describing phase separation. The governing equations are $\partial_t c = \nabla \cdot (M \nabla \mu)$ and $\mu = f'(c) - \epsilon^2 \nabla^2 c$, where $c$ is the concentration order parameter, $\mu$ is the chemical potential, $M$ is mobility, and $\epsilon$ is the interface width parameter. Missing specifications include the domain geometry (1D/2D/3D), boundary conditions (BCs), initial condition $c_0(x)$, and specific parameter values ($M, \epsilon$). The workflow will assume a generic domain $\Omega$ and periodic or zero-flux Neumann BCs ($\nabla c \cdot n = 0, \nabla \mu \cdot n = 0$) if not provided, as these are standard for conserved dynamics.

#### Physics Constraints

The primary constraints are: 1) Mass Conservation: The integral of $c$ over the domain must remain constant over time ($\frac{d}{dt} \int_\Omega c \, dx = 0$). 2) Free Energy Dissipation: The system should minimize the Ginzburg-Landau free energy, implying $\frac{dF}{dt} \leq 0$. 3) Fourth-Order Physics: The system requires computing fourth-order spatial derivatives, which imposes strict smoothness requirements on the solution and challenges numerical stability. 4) Boundary Conditions: Two sets of boundary conditions are required (e.g., for $c$ and $\mu$) to close the fourth-order problem.

#### Model Choice

To mitigate the difficulty of training fourth-order derivatives, the model will use a system formulation that decomposes the fourth-order equation into two second-order equations. A single neural network $NN_c(x,t)$ with SIREN (Sinusoidal Representation Networks) activation functions will be used to predict the concentration field $c$. SIREN is chosen for its ability to represent high-frequency derivatives and complex phase boundaries better than standard Tanh/ReLU networks. The chemical potential $\mu$ will be computed analytically from the network output using automatic differentiation ($\mu = NN_c^3 - NN_c - \epsilon^2 \nabla^2 NN_c$). This approach reduces the order of automatic differentiation required during backpropagation and improves stability.

#### Training Strategy

The loss function is defined as $L = \lambda_{eq1} L_{eq1} + \lambda_{eq2} L_{eq2} + \lambda_{IC} L_{IC} + \lambda_{BC} L_{BC} + \lambda_{mass} L_{mass}$. $L_{eq1}$ enforces the chemical potential definition, and $L_{eq2}$ enforces the conservation law. A specific soft constraint $L_{mass} = || \int_\Omega c(x,t) dx - \int_\Omega c_0(x) dx ||^2$ is added to penalize mass drift. Collocation points will be sampled using Sobol sequences. To handle stiffness, the training will use a two-stage optimizer: Adam for initial feature learning followed by L-BFGS for high-precision convergence. Gradient clipping will be applied to prevent exploding gradients from high-order terms.

#### Validation Failure Risks

Key risks include: 1) Mass Leakage: The PINN may fail to strictly conserve mass, drifting away from the physical solution over long time horizons. 2) Spectral Bias: The network may struggle to resolve sharp interfaces between phases, resulting in blurred solutions. 3) Derivative Instability: Numerical errors in computing high-order derivatives via automatic differentiation can lead to training instability or convergence to incorrect local minima. 4) Boundary Condition Violation: Simultaneously satisfying boundary conditions for both $c$ and $\mu$ can be difficult, potentially causing artifacts near domain walls. Validation metrics must include global mass conservation error and energy dissipation rate alongside standard $L_2$ residuals.

### hard_navier_stokes_2d_018

#### Problem Formalization

The objective is to reconstruct the velocity field $(u, v)$ and pressure field $p$ for a 2D incompressible flow given sparse, partial observations of velocity. The inputs are spatial coordinates $(x, y)$ and time $t$. The outputs are the flow variables $u(x,y,t)$, $v(x,y,t)$, and $p(x,y,t)$. The problem is an inverse task where the governing equations are known, but boundary conditions (BCs), initial conditions (ICs), and the Reynolds number (viscosity $
u$) are not specified. These missing parameters must be treated as assumptions or learnable variables, which introduces uncertainty into the solution.

#### Physics Constraints

The model must enforce the incompressible Navier-Stokes equations. 1) Momentum conservation: $rac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot 
abla)\mathbf{u} = -rac{1}{
ho}
abla p + 
u 
abla^2 \mathbf{u}$. 2) Mass conservation (Incompressibility): $
abla \cdot \mathbf{u} = 0$. Since BCs and ICs are not provided, the workflow must either assume generic conditions (e.g., periodic or zero-flux) or rely on the PDE residuals to constrain the solution within the observed domain, acknowledging that this may lead to ill-posedness.

#### Model Choice

A Physics-Informed Neural Network (PINN) is selected. The architecture is a fully connected Multi-Layer Perceptron (MLP) with sinusoidal (SIREN) or tanh activations to handle the spectral nature of fluid dynamics. The network takes $(x, y, t)$ as input and outputs $(u, v, p)$. This choice is justified by the need to incorporate physical laws directly into the loss function, allowing the model to infer the pressure field and flow dynamics in regions lacking data by satisfying the PDE constraints.

#### Training Strategy

The loss function combines data fidelity and physics residuals: $L = \lambda_{data} L_{data} + \lambda_{mom} L_{mom} + \lambda_{cont} L_{cont}$. $L_{data}$ is the Mean Squared Error (MSE) between predicted and observed velocities. $L_{mom}$ and $L_{cont}$ are the MSE of the Navier-Stokes and continuity residuals evaluated on collocation points sampled within the domain. Since pressure is unobserved, it is learned implicitly through the momentum equation coupling. If viscosity $
u$ is unknown, it is treated as a trainable parameter. Adaptive weighting (e.g., activation-based weighting) is used to balance the loss terms.

#### Validation Failure Risks

1) **Ill-posedness due to missing BCs**: Without explicit boundary conditions, the solution may not be unique, potentially leading to unphysical extrapolation near domain boundaries. 2) **Pressure sensitivity**: Pressure is determined by the divergence of velocity; small errors in velocity gradients can lead to large oscillations or inaccuracies in the predicted pressure field. 3) **Optimization imbalance**: The optimizer might converge to a solution that fits the sparse data well but violates the incompressibility constraint, or vice versa. 4) **Parameter identifiability**: If viscosity is not known, it may be difficult to distinguish between the effects of viscosity and turbulent fluctuations in the sparse data.

### hard_darcy_heterogeneous_019

#### Problem Formalization

The objective is to solve for the hydraulic head field $h(x)$ in a spatial domain $\Omega$. The governing equation is the steady-state Darcy flow equation with spatially varying permeability $K(x)$: $
abla \cdot (K(x) 
abla h(x)) = 0$. The permeability field $K(x)$ is a known function of space. Boundary conditions are available but their specific types (Dirichlet, Neumann, or mixed) and values are not specified in the prompt; the workflow must be flexible to accept these as inputs. The geometry of $\Omega$ is also unspecified and must be defined as a hyper-rectangle or a complex bounded domain depending on the specific geoscience application.

#### Physics Constraints

The primary physical constraint is the conservation of mass for an incompressible fluid in a steady state, combined with Darcy's Law. This results in the elliptic partial differential equation (PDE) $
abla \cdot (K(x) 
abla h) = 0$. The solution must satisfy the boundary conditions provided (e.g., fixed head $h|_{\partial\Omega_D} = h_0$ or flux $-K 
abla h \cdot n|_{\partial\Omega_N} = q$). The model must respect the heterogeneity of the medium, meaning the gradient of the head is inversely proportional to the local permeability.

#### Model Choice

A Fully Connected Neural Network (FCNN) or Multi-Layer Perceptron (MLP) is selected to approximate the hydraulic head function $\hat{h}(x; 	heta)$. The network takes spatial coordinates $(x, y)$ as inputs and outputs a scalar head value. To handle the heterogeneous coefficient $K(x)$, it is treated as a known external field evaluated at the collocation points during loss calculation rather than a network input, ensuring the PDE residual explicitly contains the spatial variation. Activation functions such as $	anh$ or Swish are preferred for their smoothness, which aids in calculating the second-order derivatives required for the differential operator.

#### Training Strategy

The loss function is a weighted sum of the PDE residual loss and the boundary condition loss: $L = \lambda_{r} L_{r} + \lambda_{b} L_{b}$. The residual loss $L_{r}$ is the Mean Squared Error (MSE) of $
abla \cdot (K(x) 
abla \hat{h})$ evaluated at collocation points sampled inside the domain. The boundary loss $L_{b}$ enforces the available boundary conditions. Given the heterogeneity, sampling should focus on regions with high gradients in $K(x)$; therefore, a Quasi-Monte Carlo method (e.g., Sobol sequence) or adaptive sampling based on residual magnitude is recommended. Optimization will use Adam for initial convergence followed by L-BFGS for high-precision minimization.

#### Validation Failure Risks

The primary risk is the inability of the PINN to converge to an accurate solution if the permeability field $K(x)$ has high contrast (sharp discontinuities or large variations), as standard PINNs struggle with discontinuous coefficients. Spectral bias may prevent the network from capturing fine-scale features of the heterogeneity. Additionally, if the boundary conditions are not enforced strongly enough (poor weighting $\lambda_{b}$), the solution may drift. Validation must include checking mass conservation error (global flux balance) and comparing against a numerical baseline (e.g., Finite Volume Method) if available.

### hard_helmholtz_high_frequency_020

#### Problem Formalization

The objective is to solve the frequency-domain Helmholtz equation $\nabla^2 u(x,y) + k^2 u(x,y) = f(x,y)$ in a bounded 2D domain $\Omega$. The solution $u$ is complex-valued, and the wavenumber $k$ is large, implying a highly oscillatory solution with wavelength $\lambda = 2\pi/k$. Missing specifications include the exact geometry of $\Omega$, the specific functional form of the source term $f$, and the type and values of the prescribed boundary conditions (Dirichlet, Neumann, or Robin) on $\partial \Omega$. These parameters must be defined to instantiate the specific physics loss.

#### Physics Constraints

The model must minimize the residual of the Helmholtz operator $R = \nabla^2 u_\theta + k^2 u_\theta - f$ at collocation points within the domain. It must strictly satisfy the boundary conditions on $\partial \Omega$. The physics requires the network to handle complex-valued outputs (representing real and imaginary parts). The high wavenumber $k$ imposes a resolution constraint: the model must capture spatial variations on the order of $\lambda$, requiring a representation capacity capable of high-frequency features.

#### Model Choice

A SIREN (Sinusoidal Representation Network) or Fourier Feature Network is selected. Standard MLPs with ReLU activations suffer from spectral bias, making them incapable of efficiently representing high-frequency oscillatory solutions. SIREN uses periodic sine activations that naturally map to the wave-like structure of the Helmholtz solution and allow for exact derivative calculation. The network will take 2D coordinates $(x, y)$ as input and output two scalars representing the real and imaginary parts of the field $u$.

#### Training Strategy

The loss function combines the PDE residual and boundary conditions: $L = \lambda_{PDE} \mathbb{E}_{x \in \Omega} [|\nabla^2 u_\theta + k^2 u_\theta - f|^2] + \lambda_{BC} \mathbb{E}_{x \in \partial \Omega} [|u_\theta - u_{BC}|^2]$. Sampling density must exceed the Nyquist rate relative to the wavelength $\lambda$ to resolve oscillations; uniform sampling or quasi-Monte Carlo methods should be used. An adaptive sampling strategy based on residual magnitude is recommended to focus computation on difficult regions. Optimization should utilize Adam with gradient clipping to manage instability from high-frequency derivatives.

#### Validation Failure Risks

The primary risk is spectral bias, where the model converges to a low-frequency 'smoothed' solution that fails to capture the oscillations. If the collocation point density is too low, aliasing will occur, preventing the model from learning the correct wave structure. The optimization landscape is highly non-convex for large $k$, increasing the risk of convergence to poor local minima. Furthermore, soft enforcement of boundary conditions may result in significant boundary leakage, where the solution fails to satisfy constraints due to the dominance of the PDE residual loss.

### hard_plus_helmholtz_staircase_021

#### Problem Formalization

The objective is to solve the time-harmonic Helmholtz equation $\nabla^2 u + k^2 u = f$ in a two-dimensional domain $\Omega$ defined by a staircase geometry. The solution $u(x,y)$ represents the wave field. Boundary conditions (BCs) are specified on $\partial \Omega$ (e.g., Dirichlet, Neumann, or Robin). Missing specific details include the exact wavenumber $k$ (magnitude of high frequency), the explicit functional form of the source term $f$, the specific BC values, and the precise geometric coordinates defining the staircase steps. These parameters must be defined to instantiate the loss function; the workflow assumes generic Dirichlet/Neumann conditions and a sufficiently large $k$ to challenge the model.

#### Physics Constraints

The primary constraint is the Helmholtz PDE governing wave propagation. Boundary conditions must be strictly enforced on the irregular staircase boundary, including sharp re-entrant corners where geometric singularities may occur. If the domain represents a scattering problem, Sommerfeld radiation conditions would apply, but for a bounded staircase domain, standard wall conditions apply. The physics requires the network to capture high spatial oscillations proportional to the wavenumber $k$ and maintain solution continuity across the complex geometry.

#### Model Choice

A standard Physics-Informed Neural Network (PINN) is likely insufficient due to spectral bias (difficulty learning high-frequency functions) and the complex non-convex geometry. The recommended model is a **SIREN (Sinusoidal Representation Network)** or a **Fourier Feature Network** to mitigate spectral bias, combined with **Domain Decomposition (XPINN)**. The staircase domain should be partitioned into rectangular subdomains. SIREN allows for better representation of high-frequency derivatives, while XPINN handles the complex geometry by simplifying the boundary representation in each subdomain and enforcing interface continuity.

#### Training Strategy

Employ a two-stage optimization strategy: first, use Adam with a learning rate schedule, then switch to L-BFGS for fine-tuning. Implement **curriculum learning** by starting with a low wavenumber $k$ and progressively increasing it to the target high frequency to guide the optimizer through the loss landscape. Use **adaptive sampling** (e.g., residual-based sampling) to dynamically increase collocation points in regions where the PDE residual is high, particularly near the sharp corners of the staircase. Weight the boundary loss significantly higher than the PDE loss to ensure strict adherence to the irregular walls.

#### Validation Failure Risks

Key risks include spectral bias preventing the capture of high oscillations, leading to a trivial zero solution or low-frequency approximation. The sharp corners of the staircase may cause gradient instability or failure to satisfy boundary conditions precisely. The optimization landscape for high-frequency Helmholtz equations is highly non-convex, increasing the risk of convergence to local minima. Finally, without domain decomposition, the network may struggle to generalize across the disjointed regions of the staircase geometry.

### hard_plus_acoustic_scattering_maze_022

#### Problem Formalization

The objective is to solve for the acoustic pressure field $u(x, y, t)$ in a 2D domain $\Omega$ containing a complex maze of internal obstacles $\Gamma_{obs}$. The system is governed by the scalar wave equation $rac{\partial^2 u}{\partial t^2} - c^2 
abla^2 u = 0$ (or the Helmholtz equation $
abla^2 u + k^2 u = 0$ if time-harmonic). The total field is decomposed as $u = u_{inc} + u_{scat}$, where $u_{inc}$ is the known incident wave. The domain boundaries $\partial \Omega$ require absorbing conditions to simulate an open environment. Missing specifications include the exact coordinate representation of the maze walls (e.g., CAD, point cloud, or implicit function), the specific boundary condition type on obstacles (Neumann/Dirichlet), and the frequency content of the incident wave. These gaps require the workflow to support flexible geometry encoding and generic boundary handling.

#### Physics Constraints

The model must satisfy the governing wave equation in the fluid region. On the internal maze walls, boundary conditions must be enforced strictly (e.g., $
abla u \cdot n = 0$ for rigid walls). At the outer boundaries of the computational domain, Perfectly Matched Layers (PML) or absorbing boundary conditions (ABC) are required to minimize non-physical reflections. The solution must maintain causality (if time-domain) and energy conservation principles. The wave speed $c$ is assumed constant or spatially varying based on provided material properties.

#### Model Choice

A SIREN (Sinusoidal Representation Networks) based Physics-Informed Neural Network (PINN) is selected. SIRENs are chosen over standard ReLU MLPs because acoustic scattering in a maze involves high-frequency spatial variations and sharp interference patterns that standard networks struggle to approximate due to spectral bias. The network will take coordinates $(x, y)$ (and time $t$ if applicable) and the Signed Distance Function (SDF) to the nearest maze wall as inputs to explicitly encode the complex geometry, allowing the network to strictly respect boundaries.

#### Training Strategy

The loss function combines PDE residual, boundary condition enforcement on maze walls, and radiation conditions at the outer limits: $L = \lambda_{pde}L_{pde} + \lambda_{wall}L_{wall} + \lambda_{rad}L_{rad}$. Sampling is critical: collocation points will be generated using rejection sampling to ensure high density near maze walls and corners to capture diffraction and scattering gradients. A curriculum learning approach will be used, initially training on a simplified geometry or lower frequency wave to establish a baseline before introducing the full maze complexity. Optimization will utilize Adam with adaptive weight re-balancing (e.g., adaptive activation functions) to handle the stiff gradients near boundaries.

#### Validation Failure Risks

Primary risks include 'leakage' where the neural network approximates a non-zero field inside solid obstacles due to imperfect boundary enforcement, and spectral bias causing the smoothing of sharp diffraction patterns at maze corners. The complex multi-path scattering may lead to convergence issues where the model settles for a local minimum satisfying the PDE but missing specific interference fringes. Validation must include point-wise error checks on high-gradient regions (corners) and integral checks on energy conservation to detect unphysical dissipation or amplification.

### hard_plus_euler_shock_023

#### Problem Formalization

The objective is to solve the compressible Euler equations $\partial_t \mathbf{U} + 
abla \cdot \mathbf{F}(\mathbf{U}) = 0$ for conserved variables $\mathbf{U} = [
ho, 
ho \mathbf{v}, E]^T$ (density, momentum, total energy). The system is hyperbolic and supports discontinuous solutions (shocks, contact discontinuities) arising from piecewise initial data. The workflow must predict the spatiotemporal evolution of $\mathbf{U}$ without assuming smoothness. Missing specifications include the spatial dimension (1D or 2D), specific initial state (e.g., Riemann problem configuration), boundary conditions (e.g., transmissive, reflective), and the equation of state parameters (assumed ideal gas with $\gamma=1.4$). The workflow must be designed to accept these as inputs or default to standard benchmarks like the Sod shock tube.

#### Physics Constraints

The solution must strictly satisfy conservation of mass, momentum, and energy. Across discontinuities, the Rankine-Hugoniot jump conditions must hold. The entropy condition must be enforced to select the physically correct weak solution (preventing non-physical expansion shocks). The equation of state $p = (\gamma - 1)(E - rac{1}{2}
ho|\mathbf{v}|^2)$ closes the system. The domain of dependence characteristic of hyperbolic PDEs must be respected, and boundary conditions must be compatible with the flow regime (e.g., non-reflective outflow).

#### Model Choice

Standard PINNs relying on pointwise automatic differentiation are unsuitable due to their inability to handle discontinuities. A Conservative Neural Network (CNN) architecture is recommended, where the network predicts fluxes or cell-averaged states to ensure global conservation by construction. Alternatively, a hybrid approach using a neural network to learn a numerical flux function within a Finite Volume framework (e.g., learning a WENO-like stencil) is appropriate. The model should be capable of representing sharp gradients, potentially using adaptive activation functions or distinct sub-networks for smooth regions and discontinuities.

#### Training Strategy

The loss function should combine: (1) an integral conservation loss evaluated over control volumes (finite volume formulation) rather than pointwise residuals; (2) a boundary condition enforcement loss; (3) an initial condition loss; and (4) an entropy inequality penalty to ensure thermodynamic consistency. Sampling must be adaptive, focusing collocation points near high-gradient regions identified by a shock sensor. Optimization should use a robust scheduler (e.g., Adam with L-BFGS refinement) and may require curriculum learning, starting from smooth initial data and progressing to discontinuous states. Soft constraints or artificial viscosity terms may be added initially to stabilize training.

#### Validation Failure Risks

Risks include: (1) Gibbs phenomenon or smearing of shocks if the network acts as a low-pass filter; (2) violation of strict conservation if the architecture does not enforce the integral form; (3) convergence to non-physical weak solutions (entropy violations) without explicit entropy constraints; (4) training instability caused by the stiffness of the source terms or rapid changes in solution topology; (5) poor generalization to unseen Riemann initial states if the training distribution is too narrow. Validation must include checking global conservation error, shock speed accuracy against analytical solutions (e.g., exact Riemann solver), and monitoring entropy production.

### hard_plus_rayleigh_benard_024

#### Problem Formalization

The objective is to solve the unsteady, incompressible Navier-Stokes equations coupled with the energy equation under the Boussinesq approximation in a 2D rectangular domain $\Omega = [0, L_x] 	imes [0, L_y]$. The state variables are velocity $\mathbf{u} = (u, v)$, pressure $p$, and temperature $T$. The domain is heated from below ($T=1$ at $y=0$) and cooled from above ($T=0$ at $y=L_y$). Missing specifications include: the aspect ratio ($L_x/L_y$), side-wall boundary conditions (periodic, no-slip, or adiabatic), Rayleigh number ($Ra$), Prandtl number ($Pr$), and initial conditions. The workflow must assume generic values or treat these as hyperparameters, noting that high $Ra$ implies thin boundary layers requiring high resolution.

#### Physics Constraints

The system must satisfy: 1) Conservation of Momentum: $\partial_t \mathbf{u} + (\mathbf{u} \cdot 
abla)\mathbf{u} = -
abla p + Pr 
abla^2 \mathbf{u} + Ra Pr T \mathbf{e}_y$. 2) Conservation of Mass (Incompressibility): $
abla \cdot \mathbf{u} = 0$. 3) Conservation of Energy: $\partial_t T + (\mathbf{u} \cdot 
abla)T = 
abla^2 T$. Boundary constraints include fixed temperature at horizontal plates and no-slip velocity conditions ($\mathbf{u}=0$) at all walls (assuming rigid boundaries). The solution must respect the Boussinesq approximation where density variations drive buoyancy but are neglected in inertia.

#### Model Choice

A Physics-Informed Neural Network (PINN) with a Fourier Feature embedding layer is selected. The Fourier features are crucial to capture the high-frequency gradients characteristic of thermal and viscous boundary layers at high Rayleigh numbers. The network will take spatiotemporal coordinates $(x, y, t)$ as input and output $(u, v, p, T)$. A shared trunk architecture with separate output heads ensures coupling between fields while allowing distinct feature extraction. This choice fits the PDE-constrained optimization nature of the problem and avoids the need for a structured grid, though it requires careful weighting of loss terms.

#### Training Strategy

The loss function combines PDE residuals ($L_{f}$), boundary condition residuals ($L_{b}$), and initial condition residuals ($L_{i}$): $L = \lambda_f L_f + \lambda_b L_b + \lambda_i L_i$. To resolve boundary layers, a dynamic sampling strategy is employed, allocating a higher density of collocation points near $y=0$ and $y=L_y$. Adaptive loss weighting (e.g., using gradient statistics or soft-Adapt) will balance the competing magnitudes of momentum, continuity, and energy residuals. A curriculum learning approach is recommended: training at a low $Ra$ first to establish a convective roll, then progressively increasing $Ra$ to the target value to stabilize optimization.

#### Validation Failure Risks

Primary risks include the inability to resolve thin boundary layers (leading to inaccurate Nusselt number predictions) and violation of mass conservation ($
abla \cdot \mathbf{u} 
eq 0$) due to optimization stiffness. Validation metrics will include the Nusselt number ($Nu$) at the plates to quantify heat transport and the integrated divergence of velocity over the domain. Failure modes include pressure drift, solution stagnation at local minima, or instability when transitioning to high $Ra$. If the PINN fails to converge, a hybrid approach using sparse CFD data for hard constraint enforcement or operator learning (DeepONet) may be necessary.

### hard_plus_mhd_divergence_025

#### Problem Formalization

The objective is to approximate the solution to the 2D resistive Magnetohydrodynamics (MHD) equations on a spatial domain $\Omega$ and time interval $[0, T]$. The state variables include density $
ho(x,y,t)$, pressure $p(x,y,t)$, velocity field $\mathbf{u}(x,y,t)$, and magnetic field $\mathbf{B}(x,y,t)$. The system is governed by the continuity equation, the Navier-Stokes momentum equation with Lorentz force, and the magnetic induction equation with resistive diffusion. **Missing Information**: Specific boundary conditions (e.g., periodic, perfectly conducting walls), initial conditions, domain geometry, and transport coefficients (viscosity $
u$, resistivity $\eta$). The workflow will assume generic Dirichlet or periodic boundaries and treat coefficients as fixed hyperparameters or learnable scalars if not provided.

#### Physics Constraints

The model must satisfy the following governing equations and constraints:
1. **Momentum Balance**: $
ho (\partial_t \mathbf{u} + \mathbf{u} \cdot 
abla \mathbf{u}) = -
abla p + (
abla 	imes \mathbf{B}) 	imes \mathbf{B} + 
u 
abla^2 \mathbf{u}$.
2. **Magnetic Induction**: $\partial_t \mathbf{B} = 
abla 	imes (\mathbf{u} 	imes \mathbf{B}) + \eta 
abla^2 \mathbf{B}$.
3. **Mass Continuity**: $\partial_t 
ho + 
abla \cdot (
ho \mathbf{u}) = 0$.
4. **Divergence-Free Constraints**: $
abla \cdot \mathbf{u} = 0$ and $
abla \cdot \mathbf{B} = 0$ must be strictly enforced to prevent unphysical mass accumulation or magnetic monopoles.

#### Model Choice

To strictly enforce the divergence-free constraints and avoid unphysical divergence errors inherent in soft penalty methods, the workflow employs a **potential-based neural network architecture**. A deep neural network (e.g., SIREN or Fourier Feature Network) takes inputs $(x, y, t)$ and outputs the stream function $\psi$, magnetic vector potential $A$, density $
ho$, and pressure $p$. The physical fields are derived analytically as:
- $\mathbf{u} = (\partial_y \psi, -\partial_x \psi)$
- $\mathbf{B} = (\partial_y A, -\partial_x A)$
This construction guarantees $
abla \cdot \mathbf{u} = 0$ and $
abla \cdot \mathbf{B} = 0$ identically, removing the need for divergence loss terms.

#### Training Strategy

1. **Loss Function**: Minimize a weighted sum of PDE residuals: $L = \lambda_{mom} \mathcal{L}_{mom} + \lambda_{ind} \mathcal{L}_{ind} + \lambda_{cont} \mathcal{L}_{cont} + \lambda_{bc} \mathcal{L}_{bc}$. Divergence constraints are excluded from the loss as they are satisfied by construction.
2. **Sampling**: Use Latin Hypercube Sampling (LHS) for collocation points in the space-time domain. Implement adaptive sampling to focus points on regions with high residual errors (e.g., current sheets).
3. **Optimization**: Utilize the Adam optimizer for initial convergence, followed by L-BFGS for high-precision minimization of the residuals.
4. **Gradient Computation**: Employ automatic differentiation to compute first and second-order spatial and temporal derivatives required for the PDE residuals.

#### Validation Failure Risks

1. **Boundary Condition Implementation**: Enforcing specific velocity or magnetic field boundary conditions via potentials ($\psi, A$) can be ill-posed (e.g., difficulty mapping Dirichlet BCs on $\mathbf{u}$ to BCs on $\psi$), potentially leading to boundary layer inaccuracies.
2. **Gradient Stiffness**: The Lorentz force and induction terms involve second-order derivatives. Numerical instability or spectral bias in the network may prevent accurate resolution of fine-scale structures like magnetic reconnection layers.
3. **Trivial Solutions**: Without sufficient data or boundary constraints, the optimizer may converge to trivial solutions (e.g., $\mathbf{u}=0, \mathbf{B}=0$) that minimize the PDE residual but do not represent the intended physical dynamics.

### hard_plus_multiscale_darcy_026

#### Problem Formalization

The task involves solving the elliptic boundary value problem for Darcy flow: $-\nabla \cdot (\kappa(\mathbf{x}) \nabla u(\mathbf{x})) = f(\mathbf{x})$ in domain $\Omega$, where $u$ is pressure, $\kappa$ is the heterogeneous permeability field, and $f$ is the source term. The workflow must accommodate two scenarios: solving a single high-contrast instance or learning a mapping across a family of permeability fields. Missing specifications include the exact geometry $\Omega$, the specific types of boundary conditions (Dirichlet, Neumann, or mixed), and the statistical distribution of the permeability fields if learning a family. These gaps require a flexible architecture capable of handling various boundary constraints and input representations.

#### Physics Constraints

The model must enforce the conservation of mass, represented by the divergence of the flux. Darcy's Law defines the constitutive relationship between flux and pressure gradient. Boundary conditions must be strictly satisfied. The permeability field $\kappa(\mathbf{x})$ is strictly positive and may exhibit high contrast (discontinuities or sharp gradients), requiring the solution to respect local ellipticity constraints. The solution $u$ should exhibit continuity, while the flux $\mathbf{q} = -\kappa \nabla u$ may be discontinuous across material interfaces.

#### Model Choice

The choice depends on the specific goal. For learning across a family of coefficient fields to enable fast inference, a **Neural Operator** (e.g., Fourier Neural Operator or DeepONet) is appropriate as it learns the mapping $\kappa \to u$ independent of the mesh. For solving a single, extremely complex instance with multiscale features, **Domain Decomposition** (e.g., XPINN) is preferred to localize the high-contrast effects and reduce the complexity of the optimization landscape. A **Coefficient-aware PINN** (where $\kappa(\mathbf{x})$ is an input coordinate to the network) is suitable for parametric studies where the permeability varies smoothly or is defined by a few physical parameters, offering a balance between interpretability and flexibility.

#### Training Strategy

The loss function combines the PDE residual ($L_{r}$), boundary condition enforcement ($L_{b}$), and potentially data mismatch ($L_{d}$). To handle high-contrast permeability, the input permeability field should be log-transformed ($\ln \kappa$) to normalize the dynamic range. Sampling strategies must prioritize high-gradient regions and interfaces; adaptive residual-based sampling is recommended. For optimization, use a two-stage approach: Adam for initial convergence followed by L-BFGS for precision. If using a Neural Operator, train on a diverse dataset of permeability realizations to ensure generalization; if using PINNs, employ curriculum learning by gradually increasing the contrast ratio of $\kappa$ during training.

#### Validation Failure Risks

Primary risks include spectral bias, where the network fails to capture high-frequency features in the permeability field, leading to inaccurate pressure gradients. Stiffness in the loss function due to high contrast may cause optimization stagnation. For Neural Operators, out-of-distribution generalization is a risk if the test permeability fields have statistical properties (e.g., longer correlation lengths) not seen during training. Additionally, soft enforcement of boundary conditions may lead to leakage errors in flux conservation, particularly at domain corners or interfaces in domain decomposition methods.

## Suggested Next Manual Scoring Subset

Start with the six representative tasks already listed in the pilot plan:

- `easy_heat_1d_dirichlet_001`
- `medium_heat_inverse_alpha_009`
- `medium_wave_sparse_sensors_012`
- `hard_cahn_hilliard_017`
- `hard_helmholtz_high_frequency_020`
- `hard_plus_mhd_divergence_025`

Use this report for reading comfort, but use the normalized JSONL as the source of record for scoring.