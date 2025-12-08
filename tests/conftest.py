import os
import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Enable pytest live logging (`log_cli`) only when ENABLE_LOGS env var is truthy.

    This keeps default runs quiet, and allows toggling logs by setting
    `ENABLE_LOGS=1` (or `true`, `yes`) in the environment.
    """
    enable = os.getenv("ENABLE_LOGS", "0").lower() in ("1", "true", "yes")
    if enable:
        # Turn on live logging and set the level/format
        config.option.log_cli = True
        config.option.log_cli_level = "INFO"
        # Optional: set format if not already configured
        try:
            # some pytest versions accept these attributes
            config.option.log_cli_format = "%(asctime)s %(levelname)s %(message)s"
            config.option.log_cli_date_format = "%Y-%m-%d %H:%M:%S"
        except Exception:
            # ignore if options unavailable
            pass
