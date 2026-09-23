from threat_platform.services.generator import generate_dataset
from threat_platform.services.storage import (
    dataset_path,
    load_dataset,
    save_dataset,
)


def main() -> None:
    # Generate synthetic dataset
    dataset = generate_dataset()

    # Save dataset
    save_dataset(
        dataset,
        dataset_path(),
    )

    # Load dataset to verify it was saved correctly
    dataset = load_dataset(
        dataset_path()
    )

    # Count records in each section
    counts = {
        key: len(value)
        for key, value in dataset.items()
        if isinstance(value, list)
    }

    print("Synthetic dataset ready (data_origin=synthetic)")

    # Display record counts
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")


if __name__ == "__main__":
    main()