from pathlib import Path
import yaml

from uav_mpe.models import Config


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config.model_validate(data)


def main() -> None:
    config = load_config("configs/example_fixed_wing.yaml")
    print("Config loaded successfully.")
    print(config)


if __name__ == "__main__":
    main()