from importlib.resources import files

DEFAULT_STATIC_PATH = files(__package__).parent.parent / "static"
DEFAULT_TASK_PATH = DEFAULT_STATIC_PATH / "task"
DEFAULT_SCHEDULE_PATH = DEFAULT_STATIC_PATH / "schedule"
DEFAULT_SVG_INDEX_FILE = DEFAULT_STATIC_PATH / "index.svg.jinja"


# TODO add other tasks...
DEFAULT_ENABLED_TASKS = ["task_system_monitoring", "task_tracking"]
# DEFAULT_ENABLED_TASKS = ["task_system_monitoring"]
# DEFAULT_ENABLED_TASKS = ["task_tracking"]
