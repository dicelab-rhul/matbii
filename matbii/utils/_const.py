from importlib.resources import files

# directories
DEFAULT_STATIC_PATH = files(__package__).parent.parent / "static"
DEFAULT_TASK_PATH = DEFAULT_STATIC_PATH / "task"
DEFAULT_CONFIG_PATH = DEFAULT_STATIC_PATH / "config"
DEFAULT_SCHEDULE_PATH = DEFAULT_STATIC_PATH / "schedule"
# files
DEFAULT_SVG_INDEX_FILE = DEFAULT_STATIC_PATH / "index.svg.jinja"
DEFAULT_SERVER_CONFIG_FILE = DEFAULT_CONFIG_PATH / "default_server_config.json"
DEFAULT_SCHEDULE_FILE = DEFAULT_SCHEDULE_PATH / "default_schedule.sch"

TASK_ID_TRACKING = "task_tracking"
TASK_ID_SYSTEM_MONITORING = "task_system_monitoring"
TASK_ID_RESOURCE_MANAGEMENT = "task_resource_management"

# TODO add other tasks...?
DEFAULT_ENABLED_TASKS = [
    TASK_ID_TRACKING,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_RESOURCE_MANAGEMENT,
]

# DEFAULT_ENABLED_TASKS = ["task_system_monitoring"]
# DEFAULT_ENABLED_TASKS = ["task_tracking"]

DEFAULT_KEY_BINDING = {
    "ArrowRight": "right",
    "ArrowLeft": "left",
    "ArrowUp": "up",
    "ArrowDown": "down",
}
ALTERNATE_KEY_BINDING = {
    "d": "right",
    "a": "left",
    "w": "up",
    "s": "down",
}
