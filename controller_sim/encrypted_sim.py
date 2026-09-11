"""
============================================================
ENCRYPTED CLOSED-LOOP SIMULATION
CKKS homomorphic state-feedback controller
============================================================

This file is the actual execution/demo of the encrypted controller.

At every control step:

    1. The simulated plant has a real state x(k).
    2. The sensor side encrypts x(k) using CKKS.
    3. The controller evaluates Enc(x(k)) . (-K).
       The controller-side operation is performed on ciphertext.
    4. Only the resulting control signal is decrypted.
    5. The plaintext plant is updated using that control signal.
    6. The process repeats.

The terminal output deliberately shows the execution pipeline so that
the simulation is observable instead of being only a final graph.

Important:
    This is a software proof-of-concept. The plant itself is simulated
    in plaintext. The state-feedback calculation is the part evaluated
    homomorphically. A real deployment would separate the sensor/
    encryption side, encrypted controller, and decryption/actuator side.
"""

import os
import time
import numpy as np
import tenseal as ts

from state_space_model import build_plant, design_state_feedback, discretize


def make_context(poly_modulus_degree=8192, coeff_mod_bit_sizes=(60, 40, 40, 60)):
    """Create the CKKS context used by the simulation."""
    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=poly_modulus_degree,
        coeff_mod_bit_sizes=list(coeff_mod_bit_sizes),
    )
    ctx.global_scale = 2 ** 40
    ctx.generate_galois_keys()
    return ctx


def _fmt_vector(values, digits=6):
    values = np.asarray(values, dtype=float).reshape(-1)
    return "[" + ", ".join(f"{v:.{digits}f}" for v in values) + "]"


def simulate_encrypted(
    Ad,
    Bd,
    K,
    x0,
    steps,
    ctx=None,
    verbose=True,
    demo_steps=8,
    print_every=10,
):
    """
    Run the CKKS encrypted-controller simulation.

    The optional terminal demonstration prints the first `demo_steps`
    control cycles and then every `print_every` steps. The complete
    numerical trajectory is returned to the caller.

    Returns:
        X         : plant state trajectory
        U         : control signal trajectory
        timings   : encryption/HE/decryption timing lists
        trace     : per-step execution metadata for CSV/reporting
    """
    if ctx is None:
        ctx = make_context()

    neg_K = (-K).flatten().tolist()
    n = Ad.shape[0]
    x = np.array(x0, dtype=float).reshape(n, 1)

    X = np.zeros((steps + 1, n))
    U = np.zeros(steps)
    X[0] = x.flatten()

    timings = {"encrypt": [], "he_dot": [], "decrypt": []}
    trace = []

    if verbose:
        print("\n" + "=" * 72)
        print("CKKS ENCRYPTED STATE-FEEDBACK EXECUTION")
        print("=" * 72)
        print("Controller operation: Enc(u) = Enc(x) · (-K)")
        print("The plaintext state is NOT used in the controller operation.")
        print("The terminal is an experiment observer; the simulated")
        print("sensor/plant values are shown here for demonstration.")
        print("-" * 72)

    for k in range(steps):
        time_s = k * 0.05

        # ------------------------------------------------------
        # SENSOR -> ENCRYPTION
        # ------------------------------------------------------
        x_before = x.flatten().copy()

        t0 = time.perf_counter()
        enc_x = ts.ckks_vector(ctx, x_before.tolist())
        t1 = time.perf_counter()

        # A serialized ciphertext size gives us concrete evidence that
        # a ciphertext object was created without printing secret data.
        try:
            enc_x_bytes = len(enc_x.serialize())
        except Exception:
            enc_x_bytes = -1

        # ------------------------------------------------------
        # ENCRYPTED CONTROLLER
        # ------------------------------------------------------
        t2 = time.perf_counter()
        enc_u = enc_x.dot(neg_K)
        t3 = time.perf_counter()

        try:
            enc_u_bytes = len(enc_u.serialize())
        except Exception:
            enc_u_bytes = -1

        # ------------------------------------------------------
        # DECRYPT ONLY THE CONTROL ACTION
        # ------------------------------------------------------
        u_val = float(enc_u.decrypt()[0])
        t4 = time.perf_counter()

        encrypt_ms = (t1 - t0) * 1e3
        he_ms = (t3 - t2) * 1e3
        decrypt_ms = (t4 - t3) * 1e3

        timings["encrypt"].append(encrypt_ms)
        timings["he_dot"].append(he_ms)
        timings["decrypt"].append(decrypt_ms)

        # Plaintext value is calculated ONLY for validation/measurement.
        # It is not used to produce u_val.
        u_plain_check = float((-K @ x)[0, 0])
        control_error = abs(u_plain_check - u_val)

        # ------------------------------------------------------
        # PHYSICAL PLANT UPDATE
        # ------------------------------------------------------
        x = Ad @ x + Bd * u_val
        X[k + 1] = x.flatten()
        U[k] = u_val

        state_change = float(np.linalg.norm(X[k + 1] - X[k]))

        trace.append(
            {
                "step": k,
                "time_s": time_s,
                "position": float(x_before[0]),
                "velocity": float(x_before[1]),
                "u_encrypted": u_val,
                "u_plain_check": u_plain_check,
                "control_error": control_error,
                "next_position": float(x[0, 0]),
                "next_velocity": float(x[1, 0]),
                "state_change_norm": state_change,
                "encrypt_ms": encrypt_ms,
                "he_dot_ms": he_ms,
                "decrypt_ms": decrypt_ms,
                "enc_x_bytes": enc_x_bytes,
                "enc_u_bytes": enc_u_bytes,
            }
        )

        # ------------------------------------------------------
        # TERMINAL DEMONSTRATION
        # ------------------------------------------------------
        show = verbose and (k < demo_steps or (k + 1) % print_every == 0 or k == steps - 1)

        if show:
            print(f"\nSTEP {k:03d}   t = {time_s:5.2f} s")
            print(f"  Sensor state x(k)       = {_fmt_vector(x_before)}")
            print("  -> Encrypting x(k) with CKKS")
            print(f"  -> Ciphertext created    ({enc_x_bytes} bytes)" if enc_x_bytes >= 0
                  else "  -> Ciphertext created")
            print("  -> Controller: Enc(x) · (-K)")
            print(f"  -> Encrypted result      ({enc_u_bytes} bytes)" if enc_u_bytes >= 0
                  else "  -> Encrypted result created")
            print(f"  -> Decrypting control u  = {u_val:.9f}")
            print(f"  -> Plant update x(k+1)   = {_fmt_vector(x.flatten())}")
            print(
                f"  -> timing: encrypt={encrypt_ms:.3f} ms, "
                f"HE={he_ms:.3f} ms, decrypt={decrypt_ms:.3f} ms"
            )

    if verbose:
        avg_encrypt = np.mean(timings["encrypt"])
        avg_he = np.mean(timings["he_dot"])
        avg_decrypt = np.mean(timings["decrypt"])

        print("\n" + "=" * 72)
        print("EXECUTION COMPLETE")
        print("=" * 72)
        print(f"Control cycles completed : {steps}")
        print(f"Final state              : {_fmt_vector(X[-1])}")
        print(f"Maximum |u|              : {np.max(np.abs(U)):.9f}")
        print("\nAverage timing per control cycle:")
        print(f"  Encryption             : {avg_encrypt:.4f} ms")
        print(f"  Homomorphic dot product: {avg_he:.4f} ms")
        print(f"  Decryption             : {avg_decrypt:.4f} ms")
        print(
            f"  TOTAL                  : "
            f"{avg_encrypt + avg_he + avg_decrypt:.4f} ms"
        )

    return X, U, timings, trace


if __name__ == "__main__":
    A, B, C, D = build_plant()
    K = design_state_feedback(A, B)
    Ad, Bd, Cd, Dd = discretize(A, B, C, D, dt=0.05)

    x0 = [1.0, 0.0]

    print("=" * 72)
    print("MASS-SPRING-DAMPER + CKKS CONTROLLER")
    print("=" * 72)
    print(f"Initial state x(0) = {_fmt_vector(x0)}")
    print(f"State-feedback gain K = {_fmt_vector(K)}")
    print(f"Sampling time = 0.05 s")
    print("Building CKKS context...")

    ctx = make_context()

    X, U, timings, trace = simulate_encrypted(
        Ad, Bd, K, x0, steps=100, ctx=ctx, verbose=True
    )

    print("\nThis run demonstrates:")
    print("  plaintext state -> CKKS ciphertext -> HE control -> decrypted u")
    print("  -> plant update -> next state")
