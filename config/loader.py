import os
import tomllib

# Directory the configs are read from. Defaults to this package directory
# (the generic, geography-neutral configs). Set the RISK_MODEL_CONFIG_DIR
# environment variable to point at an alternative config set — e.g. to run the
# bundled India reference example:
#
#   RISK_MODEL_CONFIG_DIR=contrib/india/example/config python scripts/hazard.py
#
# The directory must contain base_config.toml plus the per-script config files.
_DEFAULT_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))


def _config_dir() -> str:
    override = os.environ.get("RISK_MODEL_CONFIG_DIR")
    if override:
        return os.path.abspath(override)
    return _DEFAULT_CONFIG_DIR


def load_config(name: str) -> dict:
    """Load a script-specific TOML config merged on top of base_config.toml.

    Sections present in base_config.toml are shallow-merged with those from
    the named config, so script configs only need to declare their own sections.

    The config directory is the package directory by default, or the path in
    the RISK_MODEL_CONFIG_DIR environment variable when set.
    """
    config_dir = _config_dir()
    with open(os.path.join(config_dir, "base_config.toml"), "rb") as f:
        config = tomllib.load(f)

    with open(os.path.join(config_dir, f"{name}.toml"), "rb") as f:
        specific = tomllib.load(f)

    for key, value in specific.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            config[key].update(value)
        else:
            config[key] = value

    return config
