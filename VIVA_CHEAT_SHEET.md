# Viva Cheat Sheet — say this, in this order

You don't need to know control theory deeply. Just be able to say these
sentences in order and point at the right file/plot when asked.

## 1. "What is a state-space system?" (30 sec answer)

> "Instead of describing a system with one big differential equation, we
> describe it using a *state vector* — the minimum set of numbers that
> tells you everything about the system right now. For our example, a
> mass on a spring with a damper, the state is just **position** and
> **velocity**. Once you know those two numbers, you can predict the
> future of the system if you know the force applied to it."

Equations (already in the slides, slide "Mathematical Model"):
- `x(k+1) = A x(k) + B u(k)`  → how the state evolves
- `y(k) = C x(k)`             → what we can measure
- `e(k) = r(k) - y(k)`        → error between target and measured
- `u(k) = K e(k)`             → controller decides the force to apply

## 2. "What is state feedback control?" (30 sec answer)

> "Left alone, our spring-mass system oscillates slowly and takes a long
> time to settle — that's the 'open-loop' behavior. State feedback means:
> measure the current state x(k), multiply it by a gain matrix K, and
> feed `u(k) = -K x(k)` back as the force. Choosing K correctly lets us
> *place the poles* — i.e. directly choose how fast and how smoothly the
> system settles."

In our code (`state_space_model.py`):
- Open-loop poles: complex, slow, oscillatory (`-0.25 ± 1.39j`)
- We chose desired closed-loop poles at `-4` and `-5` (fast, no
  oscillation)
- `scipy.signal.place_poles` computed the exact `K = [18.0, 8.5]` needed

## 3. "What is the dummy example?" 

> "A mass-spring-damper: mass = 1 kg, damping = 0.5, spring constant = 2.
> We start it displaced by 1 meter and let the controller bring it back
> to zero."

## 4. "Where's the encryption?" — THE MAIN POINT OF THE PROJECT

> "The controller doesn't get to see the real state. Every step:
> 1. The plant's state x(k) is **encrypted** (CKKS homomorphic encryption,
>    via Microsoft SEAL, same library as our earlier BFV demo)
> 2. The controller computes `u(k) = -K · x(k)` **directly on the
>    ciphertext** — it never decrypts x(k)
> 3. Only the final scalar control output u(k) is decrypted and sent
>    back to the plant."

> "We already built a BFV demo earlier (10×20=200) which only supports
> encrypted integers. A real controller needs real numbers, so here we
> switched to **CKKS**, the homomorphic scheme designed for approximate
> real-number arithmetic. That's a deliberate scheme choice, not a
> random swap."

## 5. "Does it actually work?" — show `results/state_response.png`

> "Yes — the orange dashed line (encrypted controller) sits exactly on
> top of the blue line (plaintext controller). Max error is about
> `1e-7`, which is just the expected approximation error of CKKS, not a
> bug."

## 6. "What's the performance cost?" — show `results/timing_breakdown.png`

> "Per control step: ~4.3 ms to encrypt the state, ~3.2 ms for the
> homomorphic dot product, ~0.7 ms to decrypt — about 8 ms total per
> step. That's the overhead of doing control *securely*. This directly
> connects to what we found in the literature survey — homomorphic
> multiplication is the main recurring bottleneck (see our BFV timing
> slide: 3042 µs for multiply vs 21 µs for add) — and it's the natural
> next step for our FPGA acceleration work."

## 7. If asked "why not do this on the FPGA yet?"

> "This Python/TenSEAL simulation validates the *control-theory and
> algorithm correctness* first — same approach the professor described:
> simulate in Python/MATLAB/C++ before hardware. The FPGA acceleration
> (from our literature survey — NTT, pipelining, RNS) is the next stage
> once the algorithm is validated, matching our project's stated
> objective #3 and #4 (identify bottleneck → optimize performance)."

## Quick numbers to remember
- Plant: `A = [[0,1],[-2,-0.5]]`, `B = [[0],[1]]`
- Open-loop poles: `-0.25 ± 1.39j` (slow, oscillatory)
- Desired closed-loop poles: `-4, -5`
- Computed gain: `K = [18.0, 8.5]`
- Max error, encrypted vs plaintext: `~1.3e-7`
- HE overhead per control step: `~8.2 ms` (encrypt 4.3 + dot 3.2 + decrypt 0.7)
