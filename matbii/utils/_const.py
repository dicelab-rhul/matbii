from pathlib import Path
from icua.utils import LOGGER

# constants defining the task ids
TASK_ID_TRACKING = "tracking"
TASK_ID_SYSTEM_MONITORING = "system_monitoring"
TASK_ID_RESOURCE_MANAGEMENT = "resource_management"

# path of the tasks (in this package)
PACKAGE_PATH = Path(__file__).resolve().parent.parent  # root of the package
LOGGER.debug(f"`matbii` package path: {PACKAGE_PATH.as_posix()}")
TASKS_PATH = PACKAGE_PATH / "tasks"

# tasks ids, add to this when/if more tasks are implemented
TASKS = [TASK_ID_TRACKING, TASK_ID_SYSTEM_MONITORING, TASK_ID_RESOURCE_MANAGEMENT]
# paths of each task (within this package), ensure that the task id matches the folder name in `matbii.tasks`
TASK_PATHS = {t: (TASKS_PATH / t).as_posix() for t in TASKS}
for task, path in TASK_PATHS.items():
    LOGGER.debug(f"Checking {task} path: {path}")
    if not Path(path).exists():
        raise FileNotFoundError(f"Failed to find task: {task} at path: {path}")

# enable these tasks by default
DEFAULT_ENABLED_TASKS = [
    TASK_ID_TRACKING,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_RESOURCE_MANAGEMENT,
]

DEFAULT_KEY_BINDING = {
    "arrowright": "right",
    "arrowleft": "left",
    "arrowup": "up",
    "arrowdown": "down",
    "right": "right",
    "left": "left",
    "up": "up",
    "down": "down",
}

ALTERNATE_KEY_BINDING = {
    "d": "right",
    "a": "left",
    "w": "up",
    "s": "down",
}


# PYGAME_CONST = dict(
#     DEFAULT_KEY_BINDING={
#         "right": "right",
#         "left": "left",
#         "up": "up",
#         "down": "down",
#     },
#     ALTERNATE_KEY_BINDING={
#         "d": "right",
#         "a": "left",
#         "w": "up",
#         "s": "down",
#     },
# )


###### constant IDs for tasks, these are defined in the task svgs, but it is useful to have access. ######


def tank_id(tank: str):
    assert tank in ("a", "b")
    return f"tank-{tank}"


def tank_level_id(tank: str):
    assert tank in ("a", "b")
    return f"tank-{tank}-level"


def slider_id(slider: int):
    assert slider in (1, 2, 3, 4)
    return f"slider-{slider}-button-container"


def slider_incs_id(slider: int):
    assert slider in (1, 2, 3, 4)
    return f"slider-{slider}-incs"


def light_id(light: int):
    assert light in (1, 2)
    return f"light-{light}-button"


def tracking_box_id():
    return "tracking_box"


def tracking_target_id():
    return "tracking_target"
