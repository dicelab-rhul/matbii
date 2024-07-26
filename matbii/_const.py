from importlib.resources import files
import os

_TASK_PATH = files(__package__) / "tasks"
TASK_ID_TRACKING = "tracking"
TASK_ID_SYSTEM_MONITORING = "system_monitoring"
TASK_ID_RESOURCE_MANAGEMENT = "resource_management"
CONFIG_PATH = _TASK_PATH / "config.schema.json"
assert os.path.exists(str(CONFIG_PATH))

TASKS = [TASK_ID_TRACKING, TASK_ID_SYSTEM_MONITORING, TASK_ID_RESOURCE_MANAGEMENT]
TASK_PATHS = {t: str(_TASK_PATH / t) for t in TASKS}
for task, path in TASK_PATHS.items():
    assert os.path.exists(str(path))

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


PYGAME_CONST = dict(
    DEFAULT_KEY_BINDING={
        "right": "right",
        "left": "left",
        "up": "up",
        "down": "down",
    },
    ALTERNATE_KEY_BINDING={
        "d": "right",
        "a": "left",
        "w": "up",
        "s": "down",
    },
)


###### constant IDs for tasks ######


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
