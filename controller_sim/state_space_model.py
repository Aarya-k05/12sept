"""
============================================================
STATE-SPACE MODEL + STATE FEEDBACK CONTROLLER DESIGN
============================================================
This is the "dummy example of a control system" Prof. Mulla asked
the group to define. It follows exactly the generic model used in
the project slides:

    Error:            e(k) = r(k) - y(k)
    Controller:        u(k) = K e(k)              (state feedback: u = -Kx)
    State update:     x(k+1) = A x(k) + B u(k)
    Output:            y(k) = C x(k) + D u(k)

Plant chosen: a mass-spring-damper (2nd order mechanical system).
    m*x'' + c*x' + k*x = u
with m=1 kg, c=0.5 Ns/m, k=2 N/m.

State vector: x = [position, velocity]^T
This is a standard "textbook" example used to demonstrate state
feedback design -- simple, physically intuitive, and easy to explain
live in a viva (mass on a spring with friction, pushed by a force u).
============================================================
"""

import numpy as np
from scipy import signal
from scipy.signal import place_poles


def build_plant(m=1.0, c=0.5, k=2.0):
    """Continuous-time state-space model of the mass-spring-damper plant."""
    A = np.array([[0.0, 1.0],
                  [-k / m, -c / m]])
    B = np.array([[0.0],
                  [1.0 / m]])
    C = np.array([[1.0, 0.0]])   # we measure position
    D = np.array([[0.0]])
    return A, B, C, D


def design_state_feedback(A, B, desired_poles=(-4.0, -5.0)):
    """
    Design the state feedback gain K such that u(k) = -K x(k) places
    the closed-loop poles at `desired_poles` (faster, better-damped
    response than the open-loop plant).
    """
    result = place_poles(A, B, np.array(desired_poles))
    K = result.gain_matrix  # shape (1, n)
    return K


def discretize(A, B, C, D, dt=0.05):
    """Zero-order-hold discretization, matching x(k+1)=A_d x(k)+B_d u(k)."""
    sysd = signal.cont2discrete((A, B, C, D), dt, method='zoh')
    Ad, Bd, Cd, Dd, _ = sysd
    return Ad, Bd, Cd, Dd


if __name__ == "__main__":
    A, B, C, D = build_plant()
    K = design_state_feedback(A, B)
    Ad, Bd, Cd, Dd = discretize(A, B, C, D)

    print("Open-loop A:\n", A)
    print("Open-loop eigenvalues (poles):", np.linalg.eigvals(A))
    print("\nState feedback gain K:", K)
    print("Closed-loop eigenvalues (A-BK):",
          np.linalg.eigvals(A - B @ K))
    print("\nDiscretized (dt=0.05s):")
    print("Ad =\n", Ad)
    print("Bd =\n", Bd)
