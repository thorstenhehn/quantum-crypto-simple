import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

rng = np.random.default_rng()


def prepare_qubit(qc, bit, basis):

    if bit == 1:
        qc.x(0)

    # Apply hadamard to signal in |+>, |-> basis
    if basis == 1:
        qc.h(0)


def measure_qubit(qc, basis):

    # Apply hadamard to measure in |+>, |-> basis
    if basis == 1:
        qc.h(0)

    qc.measure(0, 0)


def simulate_channel(alice_bits, alice_bases, bob_bases, p):

    circuits = []

    for bit, a_basis, b_basis in zip(
        alice_bits, alice_bases, bob_bases
    ):
        qc = QuantumCircuit(1, 1)

        prepare_qubit(qc, bit, a_basis)
        phase_noise(qc, p)
        bit_flip_noise(qc, p)
        measure_qubit(qc, b_basis)

        circuits.append(qc)

    sampler = StatevectorSampler()
    result = sampler.run(circuits, shots=1).result()

    bob_bits = np.array([
        int(result[i].data.c.get_bitstrings()[0])
        for i in range(len(circuits))
    ])

    return bob_bits


def phase_noise(qc, p):
    """Apply a phase flip with probability p."""

    if rng.random() < p:
        qc.z(0)


def bit_flip_noise(qc, p):
    """Apply a bit flip with probability p."""

    if rng.random() < p:
        qc.x(0)


def sift_key(alice_bits, alice_bases, bob_bits, bob_bases):

    matching = alice_bases == bob_bases

    return alice_bits[matching], bob_bits[matching]



def estimate_qber(
    alice_key,
    bob_key,
    max_fraction=0.20,
    batch_size=100,
    target_errors=100,
    confidence=0.99,
    precision=0.03
):
    """Adaptive QBER estimation using random batches."""

    n = len(alice_key)
    max_samples = int(n * max_fraction)

    if max_samples == 0:
        raise ValueError("Sampling budget is zero")

    if not 0 < confidence < 1:
        raise ValueError("Invalid confidence level")

    # Random permutation ensures uniform sampling
    # without replacement across batches.
    positions = rng.permutation(n)

    sampled = 0
    errors = 0
    batch_count = 0

    while sampled < max_samples:

        # Draw next batch
        size = min(batch_size, max_samples - sampled)
        batch = positions[sampled:sampled + size]

        batch_errors = np.sum(
            alice_key[batch] != bob_key[batch]
        )

        sampled += size
        errors += batch_errors
        batch_count += 1

        qber = errors / sampled

        # Conservative confidence bound
        alpha = (1 - confidence) / batch_count

        margin = np.sqrt(
            np.log(2 / alpha) / (2 * sampled)
        )

        lower = max(0.0, qber - margin)
        upper = min(1.0, qber + margin)

        print(
            f"Sampled: {sampled:5d} | "
            f"Errors: {errors:4d} | "
            f"QBER: {qber:.2%} | "
            f"CI: [{lower:.2%}, {upper:.2%}]"
        )

        # Stop if EITHER target is reached
        if errors >= target_errors or 2 * margin <= precision:
            status = (
                "TARGET ERRORS REACHED"
                if errors >= target_errors
                else "CI PRECISION REACHED"
            )
            break

    else:
        status = "SAMPLING BUDGET EXHAUSTED"

    # Remove all publicly revealed positions
    remaining = positions[sampled:]

    return {
        "qber": errors / sampled,
        "errors": errors,
        "sampled": sampled,
        "confidence_interval": (lower, upper),
        "status": status,
        "alice_key": alice_key[remaining],
        "bob_key": bob_key[remaining]
    }


def main():

    N = 1000
    p = 0.2
    
    # Alice generates random bits and bases
    alice_bits = rng.integers(0, 2, N)
    alice_bases = rng.integers(0, 2, N)

    # Bob generates random bases
    bob_bases = rng.integers(0, 2, N)

    # Quantum transmission
    bob_bits = simulate_channel(
        alice_bits, alice_bases, bob_bases, p
    )

    # Key sifting
    alice_key, bob_key = sift_key(
        alice_bits, alice_bases,
        bob_bits, bob_bases
    )


    # QBER estimation
    estimation = estimate_qber(
        alice_key,
        bob_key,
        max_fraction=0.20,
        batch_size=100,
        target_errors=100,
        confidence=0.99,
        precision=0.03
    )

    # Results
    print("\n--- Parameter estimation ---")
    print("Status:", estimation["status"])
    print("Estimated QBER:", f"{estimation['qber']:.2%}")
    print("Errors:", estimation["errors"])
    print("Bits revealed:", estimation["sampled"])
    print("Confidence interval:",
          estimation["confidence_interval"])

    # Remaining key material
    alice_final = estimation["alice_key"]
    bob_final = estimation["bob_key"]

    print("\n--- Remaining key ---")
    print("Alice's key length:", len(alice_final))
    print("Bob's key length:", len(bob_final))
    print("Keys identical:",
          np.array_equal(alice_final, bob_final))

    
if __name__ == "__main__":
    main()
