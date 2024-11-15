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


def dot_notation_to_dict(
    dot_notation_dict: dict[str, Any], delim="."
) -> dict[str, Any]:
    """Convert a dictionary with keys in dot notation to a nested dictionary.

    Args:
        dot_notation_dict (dict[str, Any]): the dictionary to convert.
        delim (str, optional): the delimiter used in the dot notation keys. Defaults to ".".

    Returns:
        dict[str, Any]: the nested dictionary.
    """
    nested_dict = {}
    for key, value in dot_notation_dict.items():
        parts = key.split(delim)
        d = nested_dict
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value
    return nested_dict


def parse_config_args(unknown_args: list[str]) -> dict[str, Any]:
    """Parse configuration arguments from the unknown arguments."""
    # scan unknown args for those that start with --config.
    # find index of each --config
    from ast import literal_eval

    still_unknown_args = []
    config_args = {}
    config_indices = [i for i, arg in enumerate(unknown_args) if arg.startswith("-")]
    config_indices.append(len(unknown_args))  # need to add the end index
    for i, j in zip(config_indices[:-1], config_indices[1:]):
        if unknown_args[i].startswith("--config"):
            try:
                value = tuple(literal_eval(arg) for arg in unknown_args[i + 1 : j])
            except Exception:
                raise ValueError(
                    f"Error parsing config argument: {unknown_args[i]}, ensure the value(s): {unknown_args[i + 1 : j]} can be interpreted as a python literal. You may need to surround string values with single quotes."
                )
            if len(value) == 1:
                value = value[0]
            config_args[unknown_args[i].replace("--config.", "")] = value
        else:
            still_unknown_args.extend(unknown_args[i:j])
    config_args = dot_notation_to_dict(config_args, delim=".")
    return config_args, still_unknown_args


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
    # ======================================================================== #
    # ========================= Options for examples ========================= #
    # ======================================================================== #
    parser.add_argument(
        "-x",
        "--example",
        required=False,
        help="Name of the example to run - see `matbii.example` or [examples](https://github.com/dicelab-rhul/matbii/tree/main/example) for a full list.",
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
    args = {k.replace("-", "_"): v for k, v in vars(args).items()}
    # create context for configuration from cmd line args, other unknown args are ignored, they may be processed later
    config_args, unknown_args = parse_config_args(unknown_args)
    config_args.setdefault("logging", dict())
    config_args["logging"].setdefault("level", logging_level(args["verbose"]))

    if args.get("example", None) and args.get("script", None):
        raise ValueError("Cannot specify both --example and --script")
    return args, config_args, unknown_args


def run_example(
    name: str, config: str | None = None, config_args: dict[str, Any] | None = None
):
    """Run an example."""
    if config_args is None:
        config_args = dict()

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
    config_args.setdefault("logging", dict())
    config_args["logging"]["path"] = log_dir.as_posix()
    config_args.setdefault("experiment", dict())
    config_args["experiment"]["path"] = example.as_posix()

    # TODO we might search for this instead so that the file name doesnt need to be experiment.json
    if config:
        config_file = example / config
    else:
        config_file = example / "experiment.json"
    if not config_file.exists():
        raise FileNotFoundError(
            f"Example config file: {config_file.as_posix()} not found"
        )
    from matbii.utils import LOGGER

    LOGGER.debug(f"Example path: {example.as_posix()}")
    from matbii.main import main

    main(config_file.as_posix(), **config_args)


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
        raise ValueError(
            f"Unknown arguments: {unknown_args}, see `matbii --help` for options."
        )


def main():
    """Main entry point for the matbii."""
    args, config_args, unknown_args = parse_cmd_args()

    # premeptively set the logging level
    from matbii.utils import LOGGER

    LOGGER.set_level(config_args["logging"].get("level", "WARNING"))

    # 1. Run a script if --script is specified
    if args.get("script", None):
        # unknown arguments are ok, they will be grabbed by the script
        run_script(args.get("script"), **args)
        return

    _unknown_args_error(unknown_args)
    # 2. Run an example if --example is specified
    if args.get("example", None):
        run_example(
            args.get("example"),
            config=args.get("config", None),
            config_args=config_args,
        )
        return

    # 3. Run the main simulation
    if args.get("config", None):
        from matbii.main import main

        main(**args)
    else:
        raise ValueError(
            "No configuration provided, use -c or --config to specify a config file."
        )


if __name__ == "__main__":
    main()
