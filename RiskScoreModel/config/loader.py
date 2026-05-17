import tomllib
import os

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config(name: str) -> dict:
    """Load a script-specific TOML config merged on top of base_config.toml.

    Sections present in base_config.toml are shallow-merged with those from
    the named config, so script configs only need to declare their own sections.
    """
    with open(os.path.join(_CONFIG_DIR, "base_config.toml"), "rb") as f:
        config = tomllib.load(f)

    with open(os.path.join(_CONFIG_DIR, f"{name}.toml"), "rb") as f:
        specific = tomllib.load(f)

    for key, value in specific.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            config[key].update(value)
        else:
            config[key] = value

    return config
