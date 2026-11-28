import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

from qkd_postproc import estimate_qber, sift_key

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

    for bit, a_basis, b_basis in zip(alice_bits, alice_bases, bob_bases):
        qc = QuantumCircuit(1, 1)

        prepare_qubit(qc, bit, a_basis)
        phase_noise(qc, p)
        bit_flip_noise(qc, p)
        measure_qubit(qc, b_basis)

        circuits.append(qc)

    sampler = StatevectorSampler()
    result = sampler.run(circuits, shots=1).result()

    bob_bits = np.array(
        [int(result[i].data.c.get_bitstrings()[0]) for i in range(len(circuits))]
    )

    return bob_bits


def phase_noise(qc, p):
    """Apply a phase flip with probability p."""

    if rng.random() < p:
        qc.z(0)


def bit_flip_noise(qc, p):
    """Apply a bit flip with probability p."""

    if rng.random() < p:
        qc.x(0)


def main():

    N = 10000
    p = 0.19

    # Alice generates random bits and bases
    alice_bits = rng.integers(0, 2, N)
    alice_bases = rng.integers(0, 2, N)

    # Bob generates random bases
    bob_bases = rng.integers(0, 2, N)

    # Quantum transmission
    bob_bits = simulate_channel(alice_bits, alice_bases, bob_bases, p)

    # Key sifting
    alice_key, bob_key = sift_key(alice_bits, alice_bases, bob_bits, bob_bases)

    # QBER estimation
    estimation = estimate_qber(
        alice_key,
        bob_key,
        max_fraction=0.20,
        batch_size=100,
        target_errors=100,
        confidence=0.99,
        precision=0.03,
        max_qber=0.11,
    )

    # Results
    print("\n--- Parameter estimation ---")
    print("Status:", estimation["status"])
    print("Estimated QBER:", f"{estimation['qber']:.2%}")
    print("Errors:", estimation["errors"])
    print("Bits revealed:", estimation["sampled"])
    print("Confidence interval:", estimation["confidence_interval"])

    # Remaining key material
    alice_final = estimation["alice_key"]
    bob_final = estimation["bob_key"]

    print("\n--- Remaining key ---")
    print("Alice's key length:", len(alice_final))
    print("Bob's key length:", len(bob_final))
    print("Keys identical:", np.array_equal(alice_final, bob_final))


if __name__ == "__main__":
    main()
