# Encrypted State-Feedback Control Simulation

This completes the task assigned by Prof. Ameer Mulla:
1. Model a dummy control system using state-space realization
2. Design a state feedback controller
3. Simulate it with homomorphic encryption applied on the controller side

It is a **Python** implementation (no compiling, no SEAL build needed —
runs on any laptop in ~2 minutes of setup) that sits alongside your
existing `HE_Project/` (BFV, C++) work in the repo.

## Folder structure
```
project/
├── README.md                    <- this file
├── VIVA_CHEAT_SHEET.md          <- what to SAY tomorrow, plain English
├── controller_sim/
│   ├── state_space_model.py     <- plant + state feedback (K) design
│   ├── plaintext_sim.py         <- normal (unencrypted) closed-loop sim
│   ├── encrypted_sim.py         <- HE closed-loop sim (TenSEAL / CKKS)
│   └── compare_and_plot.py      <- RUN THIS. Produces all plots + report
└── results/                     <- generated output (already included)
    ├── state_response.png
    ├── control_signal.png
    ├── error_vs_step.png
    ├── timing_breakdown.png
    └── summary.txt
```

The `results/` folder already has everything generated and ready to
screenshot into slides — you do NOT have to run anything if you're
short on time. But if you want to reproduce/tweak it:

## How to run

```bash
# one-time setup (~1-2 min)
pip install tenseal scipy matplotlib numpy

# run everything
cd project/controller_sim
python3 compare_and_plot.py
```

That's it. It will print the state-space model, controller gain,
accuracy comparison, and regenerate all plots + `summary.txt` into
`../results/`.

## What this demonstrates (map to your project objectives slide)

| Objective (from slides)      | Where it's done |
|---|---|
| 1. Homomorphic Encryption study | `encrypted_sim.py` — CKKS via TenSEAL/Microsoft SEAL |
| 2. Understand FPGA/system architecture | existing `HE_Project/` (BFV, C++) |
| 3. Identify bottleneck | `timing_breakdown.png` — encrypt/HE-op/decrypt cost per control step |
| 4. Optimize performance | Discussion point: this Python sim validates correctness; FPGA/NTT optimization (literature survey) is the next stage |

## Why CKKS instead of BFV here

Your existing `HE_Project` uses **BFV**, which only supports encrypted
**integer** arithmetic (hence the `10, 20` example). A real state
feedback controller needs **real-valued** states and gains (e.g.
`K = [18.0, 8.5]`), so this simulation uses **CKKS**, the homomorphic
scheme designed for approximate real-number arithmetic — same
underlying Microsoft SEAL library, different scheme, chosen because
it matches the actual math of `u(k) = K·x(k)`.

## Key result

The encrypted controller reproduces the plaintext controller's
closed-loop response to within `~1.3e-7` — i.e. the plant is
controlled correctly even though the controller never sees the
plaintext state, only encrypted ciphertexts. See
`results/state_response.png`.
