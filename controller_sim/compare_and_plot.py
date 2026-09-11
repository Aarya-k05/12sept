"""
============================================================
COMPARE PLAINTEXT vs ENCRYPTED CONTROLLER
============================================================

This file runs both controllers and produces:

    results/
        control_data.csv
        execution_trace.csv
        state_response.png
        control_signal.png
        error_vs_step.png
        timing_breakdown.png
        summary.txt

The CSV files are important: the simulation produces actual numerical
data that can be inspected independently of the graphs.
"""

import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from state_space_model import build_plant, design_state_feedback, discretize
from plaintext_sim import simulate_plaintext
from encrypted_sim import simulate_encrypted, make_context


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def save_csv(path, headers, rows):
    """Write a simple CSV file that can be opened in Excel."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def main():
    # ---------------------------------------------------------
    # BUILD PLANT + CONTROLLER
    # ---------------------------------------------------------
    A, B, C, D = build_plant()
    K = design_state_feedback(A, B, desired_poles=(-4.0, -5.0))
    dt = 0.05
    Ad, Bd, Cd, Dd = discretize(A, B, C, D, dt=dt)

    x0 = [1.0, 0.0]
    steps = 100
    t = np.arange(steps + 1) * dt

    print("=" * 72)
    print("STATE-SPACE MODEL")
    print("=" * 72)
    print("Continuous A:\n", A)
    print("Continuous B:\n", B)
    print("Open-loop poles:", np.linalg.eigvals(A))
    print("\nState feedback gain K:", K)
    print("Closed-loop poles (A-BK):", np.linalg.eigvals(A - B @ K))
    print("\nDiscretized Ad:\n", Ad)
    print("Discretized Bd:\n", Bd)

    # ---------------------------------------------------------
    # PLAINTEXT BASELINE
    # ---------------------------------------------------------
    print("\n" + "=" * 72)
    print("1) PLAINTEXT BASELINE")
    print("=" * 72)

    X_plain, U_plain = simulate_plaintext(Ad, Bd, K, x0, steps)

    print(f"Initial state : {X_plain[0]}")
    print(f"Final state   : {X_plain[-1]}")
    print(f"Max |u|       : {np.max(np.abs(U_plain)):.9f}")

    # ---------------------------------------------------------
    # ENCRYPTED RUN
    # ---------------------------------------------------------
    print("\n" + "=" * 72)
    print("2) CKKS ENCRYPTED CONTROLLER")
    print("=" * 72)

    ctx = make_context()
    X_enc, U_enc, timings, trace = simulate_encrypted(
        Ad, Bd, K, x0, steps, ctx=ctx, verbose=True
    )

    # ---------------------------------------------------------
    # ACCURACY
    # ---------------------------------------------------------
    state_error = np.linalg.norm(X_plain - X_enc, axis=1)
    control_error = np.abs(U_plain - U_enc)

    max_state_error = np.max(state_error)
    max_control_error = np.max(control_error)

    print("\n" + "=" * 72)
    print("3) PLAINTEXT vs CKKS ACCURACY")
    print("=" * 72)
    print(f"Final plaintext state  : {X_plain[-1]}")
    print(f"Final encrypted state  : {X_enc[-1]}")
    print(f"Maximum state error    : {max_state_error:.6e}")
    print(f"Maximum control error  : {max_control_error:.6e}")
    print("\nInterpretation:")
    print("CKKS performs approximate arithmetic, so a small numerical")
    print("difference between plaintext and encrypted execution is expected.")

    # ---------------------------------------------------------
    # SAVE ACTUAL NUMERICAL DATA
    # ---------------------------------------------------------
    control_rows = []
    for k in range(steps):
        tr = trace[k]
        control_rows.append([
            k,
            f"{t[k]:.6f}",
            f"{X_plain[k, 0]:.12f}",
            f"{X_plain[k, 1]:.12f}",
            f"{X_enc[k, 0]:.12f}",
            f"{X_enc[k, 1]:.12f}",
            f"{U_plain[k]:.12f}",
            f"{U_enc[k]:.12f}",
            f"{state_error[k]:.12e}",
            f"{control_error[k]:.12e}",
            f"{tr['encrypt_ms']:.6f}",
            f"{tr['he_dot_ms']:.6f}",
            f"{tr['decrypt_ms']:.6f}",
            tr["enc_x_bytes"],
            tr["enc_u_bytes"],
        ])

    save_csv(
        os.path.join(RESULTS_DIR, "control_data.csv"),
        [
            "step", "time_s",
            "position_plain", "velocity_plain",
            "position_encrypted", "velocity_encrypted",
            "u_plain", "u_encrypted",
            "state_error", "control_error",
            "encrypt_ms", "he_dot_ms", "decrypt_ms",
            "enc_x_serialized_bytes", "enc_u_serialized_bytes",
        ],
        control_rows,
    )

    trace_rows = []
    for tr in trace:
        trace_rows.append([
            tr["step"],
            f"{tr['time_s']:.6f}",
            f"{tr['position']:.12f}",
            f"{tr['velocity']:.12f}",
            f"{tr['u_encrypted']:.12f}",
            f"{tr['u_plain_check']:.12f}",
            f"{tr['control_error']:.12e}",
            f"{tr['next_position']:.12f}",
            f"{tr['next_velocity']:.12f}",
            f"{tr['state_change_norm']:.12e}",
            f"{tr['encrypt_ms']:.6f}",
            f"{tr['he_dot_ms']:.6f}",
            f"{tr['decrypt_ms']:.6f}",
            tr["enc_x_bytes"],
            tr["enc_u_bytes"],
        ])

    save_csv(
        os.path.join(RESULTS_DIR, "execution_trace.csv"),
        [
            "step", "time_s", "sensor_position", "sensor_velocity",
            "u_from_encrypted_controller", "u_plain_validation",
            "control_error", "next_position", "next_velocity",
            "state_change_norm", "encrypt_ms", "he_dot_ms",
            "decrypt_ms", "enc_x_serialized_bytes", "enc_u_serialized_bytes",
        ],
        trace_rows,
    )

    # ---------------------------------------------------------
    # PLOTS
    # ---------------------------------------------------------
    fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    axs[0].plot(t, X_plain[:, 0], label="Plaintext controller", lw=2)
    axs[0].plot(t, X_enc[:, 0], "--", label="Encrypted controller (CKKS)", lw=2)
    axs[0].set_ylabel("Position (m)")
    axs[0].legend()
    axs[0].grid(True)
    axs[0].set_title("Closed-Loop State Response")

    axs[1].plot(t, X_plain[:, 1], label="Plaintext controller", lw=2)
    axs[1].plot(t, X_enc[:, 1], "--", label="Encrypted controller (CKKS)", lw=2)
    axs[1].set_ylabel("Velocity (m/s)")
    axs[1].set_xlabel("Time (s)")
    axs[1].legend()
    axs[1].grid(True)

    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "state_response.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t[:-1], U_plain, label="Plaintext u(k)", lw=2)
    ax.plot(t[:-1], U_enc, "--", label="Encrypted u(k)", lw=2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Control input u(k)")
    ax.set_title("Control Signal: Plaintext vs CKKS")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "control_signal.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.semilogy(t, state_error + 1e-16)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("State error (log scale)")
    ax.set_title("CKKS Approximation Error")
    ax.grid(True, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "error_vs_step.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ops = ["encrypt", "he_dot", "decrypt"]
    means = [np.mean(timings[o]) for o in ops]
    ax.bar(ops, means)
    ax.set_ylabel("Average time per control step (ms)")
    ax.set_title("CKKS Controller Timing Breakdown")
    for i, v in enumerate(means):
        ax.text(i, v, f"{v:.3f} ms", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, "timing_breakdown.png"), dpi=150)
    plt.close(fig)

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------
    summary_path = os.path.join(RESULTS_DIR, "summary.txt")

    avg_encrypt = np.mean(timings["encrypt"])
    avg_he = np.mean(timings["he_dot"])
    avg_decrypt = np.mean(timings["decrypt"])

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 72 + "\n")
        f.write("CKKS ENCRYPTED STATE-FEEDBACK CONTROL SYSTEM\n")
        f.write("=" * 72 + "\n\n")

        f.write("1. PLANT\n")
        f.write("Mass-spring-damper: m=1 kg, c=0.5 Ns/m, k=2 N/m\n")
        f.write(f"A =\n{A}\n\nB =\n{B}\n\n")
        f.write(f"Open-loop poles: {np.linalg.eigvals(A)}\n\n")

        f.write("2. CONTROLLER\n")
        f.write("Control law: u(k) = -K x(k)\n")
        f.write(f"K = {K}\n")
        f.write("Desired continuous closed-loop poles: [-4, -5]\n")
        f.write(f"Actual continuous closed-loop poles: {np.linalg.eigvals(A - B @ K)}\n\n")

        f.write("3. DISCRETIZATION\n")
        f.write(f"Sampling time: {dt} s\n")
        f.write(f"Ad =\n{Ad}\n\nBd =\n{Bd}\n\n")

        f.write("4. CKKS CONFIGURATION\n")
        f.write("Polynomial modulus degree: 8192\n")
        f.write("Coefficient modulus bits: [60, 40, 40, 60]\n")
        f.write("Global scale: 2^40\n")
        f.write("Library: TenSEAL (Microsoft SEAL backend)\n\n")

        f.write("5. SIMULATION\n")
        f.write(f"Control cycles: {steps}\n")
        f.write(f"Initial state: {x0}\n")
        f.write(f"Final plaintext state: {X_plain[-1]}\n")
        f.write(f"Final encrypted-controller state: {X_enc[-1]}\n\n")

        f.write("6. ACCURACY\n")
        f.write(f"Maximum state error: {max_state_error:.12e}\n")
        f.write(f"Maximum control error: {max_control_error:.12e}\n\n")

        f.write("7. HE TIMING\n")
        f.write(f"Average encryption: {avg_encrypt:.6f} ms/step\n")
        f.write(f"Average HE dot product: {avg_he:.6f} ms/step\n")
        f.write(f"Average decryption: {avg_decrypt:.6f} ms/step\n")
        f.write(f"Total: {avg_encrypt + avg_he + avg_decrypt:.6f} ms/step\n\n")

        f.write("8. FILES\n")
        f.write("control_data.csv      - combined numerical results\n")
        f.write("execution_trace.csv   - step-by-step execution trace\n")
        f.write("state_response.png    - state comparison\n")
        f.write("control_signal.png    - control comparison\n")
        f.write("error_vs_step.png     - CKKS numerical error\n")
        f.write("timing_breakdown.png  - HE timing\n\n")

        f.write("9. INTERPRETATION\n")
        f.write("The controller computes the state-feedback dot product using\n")
        f.write("a CKKS ciphertext and a plaintext gain vector. Only the resulting\n")
        f.write("control signal is decrypted before it is applied to the simulated\n")
        f.write("plant. The plaintext controller is retained as a baseline so the\n")
        f.write("effect of CKKS approximation can be quantified.\n")

    print("\n" + "=" * 72)
    print("FILES GENERATED")
    print("=" * 72)
    print(f"Results directory: {os.path.abspath(RESULTS_DIR)}")
    print("  control_data.csv")
    print("  execution_trace.csv")
    print("  state_response.png")
    print("  control_signal.png")
    print("  error_vs_step.png")
    print("  timing_breakdown.png")
    print("  summary.txt")


if __name__ == "__main__":
    main()
