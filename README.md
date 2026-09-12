# Encrypted State-Feedback Control Simulation

Software simulation of a state-feedback controller executing on homomorphic encrypted data.

## Overview

This project demonstrates encrypted state-feedback control using CKKS (Cheon-Kim-Kim-Song) homomorphic encryption. The core operation is the control law `u = -Kx`, where the state vector `x` is encrypted before the computation.

The simulation includes:

- A simple state-space plant model (2-state system)
- State-feedback gain calculation
- Plaintext controller (reference)
- Encrypted controller using TenSEAL
- Correctness and timing analysis
- Comparison plots

## Prerequisites

- Python 3.7+
- `pip` or equivalent package manager

## Installation

```bash
pip install tenseal scipy matplotlib numpy
```

## Running

From the project root:

```bash
cd controller_sim
python compare_and_plot.py
```

or with `python3`:

```bash
python3 compare_and_plot.py
```

This runs both plaintext and encrypted simulations and generates results in `results/`.

## Project structure

```
controller_sim/
├── state_space_model.py    # Plant model and controller gain
├── plaintext_sim.py        # Baseline (unencrypted) controller
├── encrypted_sim.py        # CKKS encrypted controller
└── compare_and_plot.py     # Run both and generate plots

results/
├── state_response.png      # State trajectory comparison
├── control_signal.png      # Control input over time
├── error_vs_step.png       # Encryption error magnitude
├── timing_breakdown.png    # Operation timing
└── summary.txt             # Numerical results
```

## How it works

Each control step follows this flow:

```
Plaintext state x
    ↓
Encrypt (CKKS)
    ↓
Homomorphic computation: Enc(x) · (-K)
    ↓
Decrypt
    ↓
Apply control u to plant
    ↓
Measure next state
```

The encrypted and plaintext versions run in parallel for comparison.

## Understanding the results

**state_response.png** — Overlay of plaintext and encrypted state trajectories. Should be nearly identical.

**control_signal.png** — Control input magnitude over time. Starts high (state far from equilibrium), decays toward zero.

**error_vs_step.png** — Pointwise difference between encrypted and plaintext control. Represents CKKS approximation error; should be small.

**timing_breakdown.png** — Duration of encrypt, compute, and decrypt operations per step.

**summary.txt** — Final state values, control error magnitude, mean operation times.

## Why CKKS?

CKKS supports approximate arithmetic on real and complex numbers, making it suitable for continuous-valued state and control signals. Unlike BFV (which handles integers), CKKS naturally handles floating-point gain matrices and state vectors.

## Notes

- Each control step encrypts the current state independently; the simulation does not accumulate noise across steps.
- CKKS approximation error is expected and typically in the range of 1e-5 to 1e-6 for this problem.
- The plant dynamics are simulated in plaintext; only the controller computation is encrypted.
- Runtime depends on CKKS parameter choice; larger polynomial degrees and coefficient moduli increase security but reduce speed.