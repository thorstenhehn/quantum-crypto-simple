import numpy as np

rng = np.random.default_rng()

def estimate_qber(
    alice_key,
    bob_key,
    max_fraction=0.25,
    batch_size=100,
    target_errors=100,
    confidence=0.99,
    precision=0.05
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

