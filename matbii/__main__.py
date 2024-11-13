"""Entry point for the matbii simulation."""

import importlib.resources
from pathlib import Path
from typing import Any
from collections import defaultdict
import os
import argparse
import importlib
import inspect


from star_ray.utils import _LOGGER

# avoid a pygame issue on linux. TODO this should be moved somewhere more suitable...
os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"

# silence logs from star_ray logger
_LOGGER.setLevel("WARNING")


def logging_level(verbosity: int) -> str:
    """Convert a verbosity level to a logging level."""
    return defaultdict(lambda: "DEBUG", {0: "WARNING", 1: "INFO", 2: "DEBUG"})[
        verbosity
    ]


def parse_cmd_args() -> dict[str, Any]:
    """Parse command line arguments."""
    # load configuration file
    parser = argparse.ArgumentParser()

    # ======================================================================== #
    # =============================== Options ================================ #
    # ======================================================================== #
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (use -v, -vv, -vvv for more verbosity)",
    )
    # ======================================================================== #
    # =========================== Options for main =========================== #
    # ======================================================================== #
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path to configuration file.",
    )
    parser.add_argument(
        "-p",
        "--participant",
        required=False,
        help="ID of the participant.",
    )
    parser.add_argument(
        "-e", "--experiment", required=False, help="ID of the experiment.", default=None
    )
    # ======================================================================== #
    # ========================= Options for examples ========================= #
    # ======================================================================== #
    parser.add_argument(
        "-x",
        "--example",
        required=False,
        help="Name of the example to run - see `https://github.com/dicelab-rhul/matbii/tree/main/example`",
    )
    # ======================================================================== #
    # ========================= Options for scripts ========================== #
    # ======================================================================== #
    parser.add_argument(
        "-s",
        "--script",
        required=False,
        help="Name of the script to run - see `matbii.extras.scripts`",
    )
    args, unknown_args = parser.parse_known_intermixed_args()
    kwargs = {k.replace("-", "_"): v for k, v in vars(args).items()}
    # create context for configuration from cmd line args
    kwargs["logging"] = dict(level=logging_level(args.verbose))
    if kwargs.get("experiment", None):
        kwargs["experiment"] = dict(id=kwargs["experiment"])
    else:
        kwargs["experiment"] = dict()
    if kwargs.get("participant", None):
        kwargs["participant"] = dict(id=kwargs["participant"])
    else:
        kwargs["participant"] = dict()

    if kwargs.get("example", None) and kwargs.get("script", None):
        raise ValueError("Cannot specify both --example and --script")
    return kwargs, unknown_args


def run_example(name: str, **kwargs: dict[str, Any]):
    """Run an example."""
    # navigate to the example directory
    example_dir = Path(importlib.resources.path("matbii", "example"))
    if not example_dir.exists():
        # try again, there are some issues with editable installs
        example_dir = example_dir.parent / "matbii" / example_dir.name
        if not example_dir.exists():
            raise ImportError(f"Example path: {example_dir.as_posix()} not found.")
    example = example_dir / name
    # from matbii.utils import LOGGER
    # LOGGER.debug(f"Using example path: {example.as_posix()}")
    if not example.is_dir():
        avaliable_examples = "\n- ".join(
            [p.name for p in example_dir.iterdir() if p.is_dir()]
        )
        raise ValueError(
            f"Example: `{name}` not found at path: `{example.as_posix()}`. Avaliable examples:\n- {avaliable_examples}"
        )
    # record the current working directory, this will be used to store the log files
    log_dir = Path.cwd() / f"{name}-logs"
    kwargs["logging"]["path"] = log_dir.as_posix()
    kwargs["experiment"]["path"] = example.as_posix()

    # TODO we might search for this instead so that the file name doesnt need to be experiment.json
    if kwargs.get("config", None):
        config_file = example / kwargs["config"]
    else:
        config_file = example / "experiment.json"
    if not config_file.exists():
        raise FileNotFoundError(
            f"Example config file: {config_file.as_posix()} not found"
        )
    del kwargs["config"]

    from matbii.utils import LOGGER

    LOGGER.debug(f"Example path: {example.as_posix()}")
    from matbii.main import main

    main(config_file.as_posix(), **kwargs)


def run_script(name: str, **kwargs: dict[str, Any]):
    """Run a script."""
    from matbii.extras import scripts

    avaliable_scripts = {
        func[0]: func[1]
        for func in inspect.getmembers(scripts, inspect.isfunction)
        if not func[0].startswith("_")  # Filter out private functions
    }
    if name not in avaliable_scripts:
        script_names = "\n- ".join(avaliable_scripts.keys())
        raise ValueError(
            f"Script: `{name}` not found, avaliable scripts:\n- {script_names}"
        )
    avaliable_scripts[name](**kwargs)


def _unknown_args_error(unknown_args: Any):
    if unknown_args:
        raise ValueError(f"Unknown arguments: {unknown_args} - see `matbii --help`")


def main():
    """Main entry point for the matbii."""
    kwargs, unknown_args = parse_cmd_args()

    # premeptively set the logging level
    from matbii.utils import LOGGER

    LOGGER.set_level(kwargs["logging"].get("level", "WARNING"))

    # 1. Run a script if --script is specified
    if kwargs.get("script", None):
        # unknown arguments are ok, they will be grabbed by the script
        run_script(kwargs.get("script"), **kwargs)
        return

    _unknown_args_error(unknown_args)
    # 2. Run an example if --example is specified
    if kwargs.get("example", None):
        run_example(kwargs.get("example"), **kwargs)
        return

    # 1. Run the main simulation
    if kwargs.get("config", None):
        from matbii.main import main

        main(**kwargs)
    else:
        raise ValueError(
            "No configuration provided, use -c or --config to specify a config file."
        )


if __name__ == "__main__":
    main()
