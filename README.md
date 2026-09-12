# Encrypted State-Feedback Control Simulation

Software simulation of a state-feedback controller executing on homomorphically encrypted data.

## Overview

This project demonstrates encrypted state-feedback control using CKKS (Cheon-Kim-Kim-Song) homomorphic encryption.

The basic control law is:

    u = -Kx

where `x` is the system state and `K` is the state-feedback gain.

In the encrypted version, the state is encrypted before the controller computation:

    Enc(x) · (-K) = Enc(u)

The simulation includes:

- A simple state-space plant model (2-state system)
- State-feedback gain calculation
- Plaintext controller as a reference
- Encrypted controller using TenSEAL / CKKS
- Correctness and timing analysis
- Comparison plots

## Prerequisites

- Python 3.7+
- `pip` or equivalent package manager

## Installation

Install the required packages:

```bash
pip install tenseal scipy matplotlib numpy
```

If `pip` is not recognized:

```bash
python -m pip install tenseal scipy matplotlib numpy
```

## Running

From the project root:

```bash
cd controller_sim
```

### Run the complete simulation

```bash
python compare_and_plot.py
```

or:

```bash
python3 compare_and_plot.py
```

This runs the plaintext and encrypted simulations, compares their results, and generates the plots and numerical summary in `results/`.

### Run only the encrypted controller

To directly see the CKKS encrypted controller execution:

```bash
python encrypted_sim.py
```

or:

```bash
python3 encrypted_sim.py
```

This prints the execution of each control step, including:

- State being encrypted
- CKKS encryption
- Homomorphic computation `Enc(x) · (-K)`
- Encrypted control result
- Decryption
- Control value applied to the plant
- Encryption / HE / decryption timing

The plaintext `u = -Kx` calculation is also performed internally as a correctness check, but it is not used to generate the encrypted result or update the plant.

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
├── error_vs_step.png       # HE approximation error
├── timing_breakdown.png    # Operation timing
└── summary.txt             # Numerical results
```

## How it works

Each control step follows this flow:

```
Simulated state x
    ↓
CKKS encryption
    ↓
Encrypted state Enc(x)
    ↓
Homomorphic computation
Enc(x) · (-K)
    ↓
Encrypted control Enc(u)
    ↓
Decrypt
    ↓
Control u
    ↓
Update plant
    ↓
Next state
```

The plaintext controller is used separately as a reference so that the decrypted HE result can be checked for correctness.

The actual control signal used to update the encrypted simulation comes from the decrypted homomorphic result.

## Understanding the results

**state_response.png** — Overlay of plaintext and encrypted state trajectories. The two responses should be nearly identical.

**control_signal.png** — Control input over time. It starts relatively high because the initial state is away from equilibrium, then approaches zero as the feedback controller stabilizes the system.

**error_vs_step.png** — Difference between the decrypted HE control result and the independent plaintext reference. This represents the numerical approximation error introduced by CKKS.

**timing_breakdown.png** — Time spent on encryption, the homomorphic computation, and decryption for each control step.

**summary.txt** — Contains the final state, control error, and average operation timings.

## Why CKKS?

BFV is designed for exact modular integer arithmetic, while CKKS supports approximate arithmetic on real and complex values.

The state-feedback controller uses real-valued states and gains, for example:

```
K = [18.0, 8.5]
```

Therefore, CKKS is more suitable for this simulation.

TenSEAL provides the Python interface used here, with Microsoft SEAL as the underlying homomorphic encryption library.

## Notes

- Each control step encrypts the current state independently.
- The simulation does not repeatedly operate on the same ciphertext across control steps, so the 100 control steps should not be interpreted as cumulative noise growth in a single ciphertext.
- CKKS performs approximate arithmetic, so a small difference between the decrypted HE result and the plaintext reference is expected.
- The approximation error is measured directly from the simulation rather than assuming a fixed error range.
- The plant dynamics are simulated in plaintext; the state-feedback controller computation is the part performed homomorphically.
- Runtime depends on the CKKS parameters. Larger polynomial degrees and coefficient moduli can increase computational cost.

## Current scope

This is a software proof-of-concept for the encrypted controller.

The current implementation demonstrates:

- State-space modelling
- State-feedback control
- CKKS encryption
- Homomorphic controller computation
- Decryption of the control signal
- Correctness comparison
- Timing analysis

FPGA implementation and hardware-level optimizations such as NTT acceleration, pipelining, parallelism, and resource optimization are outside the scope of this simulation.