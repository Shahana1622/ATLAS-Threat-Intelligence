from backend.threat_platform.services.generator import generate_dataset
from backend.threat_platform.services.storage import dataset_path, load_dataset, save_dataset


def main() -> None:
    save_dataset(generate_dataset(), dataset_path())
    dataset = load_dataset(dataset_path())
    counts = {key: len(value) for key, value in dataset.items() if isinstance(value, list)}
    print("Synthetic dataset ready (data_origin=synthetic)")
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")


if __name__ == "__main__":
    main()

