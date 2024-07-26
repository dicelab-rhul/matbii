from matbii.guidance import (
    DefaultGuidanceAgent,
    ArrowGuidanceActuator, 
    BoxGuidanceActuator,
    SystemMonitoringTaskAcceptabilitySensor,
    TrackingTaskAcceptabilitySensor,
    ResourceManagementTaskAcceptabilitySensor,
)
from matbii.tasks import (
    TrackingActuator,
    SystemMonitoringActuator,
    ResourceManagementActuator,
    AvatarTrackingActuator,
    AvatarSystemMonitoringActuator,
    AvatarResourceManagementActuator,
)
from matbii import (
    TASK_PATHS,
    TASK_ID_TRACKING,
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    CONFIG_PATH,
)
from icua.agent import Avatar, AvatarActuator
from icua.environment import MultiTaskEnvironment
from icua.utils import LOGGER
from icua.extras.eyetracking import EyetrackerIOSensor, tobii
from star_ray.ui import WindowConfiguration
from star_ray.utils import ValidatedEnvironment
from pathlib import Path
import argparse
import os
from pprint import pformat

from star_ray.utils import _LOGGER
_LOGGER.setLevel("INFO")
#LOGGER.set_level("INFO")

# avoid a pygame issue on linux...
os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--config",
    required=False,
    help="Path to the matbii configuration file.",
    default=None,
)
args = parser.parse_args()
config = ValidatedEnvironment.load_and_validate_context(str(CONFIG_PATH), args.config)


if args.config:
    LOGGER.debug(f"Using config file: {str(args.config)}")
else:
    LOGGER.debug("No config file was specified, using default configuration.")



window_config = WindowConfiguration(
    x=config["window_x"],
    y=config["window_y"],
    width=config["window_width"],
    height=config["window_height"],
    title=config["window_title"],
    resizable=config["window_resizable"],
    fullscreen=config["window_fullscreen"],
    background_color=config["window_background_color"],
)

eyetracking_config = dict(
    enabled=config["eyetracking_enabled"],
    calibration_check=config["eyetracking_calibration_check"],
    moving_average_n=config["eyetracking_moving_average_n"],
    velocity_threshold=config["eyetracking_velocity_threshold"],
    throttle_events=config["eyetracking_throttle"],
)

experiment_config = config["experiment_info"]
experiment_id = experiment_config["id"]
experiment_duration = experiment_config["duration"]

experiment_path = Path(experiment_config["path"]).expanduser().resolve()
if not experiment_path.exists():
    raise ValueError(f"Experiment path: {experiment_path.as_posix()} does not exist.")
experiment_path = experiment_path.as_posix()

participant_config = config["participant_info"]
participant_id = participant_config["id"]

# LOGGER.info(
#     "------------------------------------------------------------------------------------------"
# )
# LOGGER.info("%25s %s", "Experiment :", experiment_id)
# LOGGER.info("%25s %s", "Experiment path :", experiment_path)
# LOGGER.info("%25s %s", "Participant :", participant_id)
# LOGGER.info("%25s %s", "Eyetracking enabled :", eyetracking_config["enabled"])
# LOGGER.info("%25s %s", "Tasks enabled :", config["enable_tasks"])
# LOGGER.info(
#     "------------------------------------------------------------------------------------------"
# )

eyetracker = tobii.TobiiEyetracker(uri="tet-tcp://172.28.195.1")
window_config = WindowConfiguration(width=1200, height=800)
eyetracker_sensor = EyetrackerIOSensor(eyetracker)

avatar = Avatar(
    [eyetracker_sensor],  # relevant sensors are added by default
    [AvatarActuator()],  # task actuators are added when the corresponding task is enabled
    window_config=window_config,
)

guidance_agent = DefaultGuidanceAgent(
    [
        SystemMonitoringTaskAcceptabilitySensor(),
        ResourceManagementTaskAcceptabilitySensor(),
        TrackingTaskAcceptabilitySensor(),
    ],
    # change actuators for different guidance to be shown (must inherit from GuidanceActuator)
    [ArrowGuidanceActuator(arrow_mode="gaze"), BoxGuidanceActuator()],
)

env = MultiTaskEnvironment(
    avatar=avatar,
    agents=[guidance_agent],
    wait=0.3,
    svg_size=config["canvas_size"],
    svg_position=config["canvas_offset"],
    logging_path=config["logging_path"],
)

# NOTE: if you have more tasks to add, add them here! dynamic loading is not enabled by default, if you want to load actuators dynamically, enable it in the ambient.
env.add_task(
    name=TASK_ID_TRACKING,
    path=[experiment_path, TASK_PATHS[TASK_ID_TRACKING]],
    agent_actuators=[TrackingActuator],
    avatar_actuators=[AvatarTrackingActuator],
    enable=TASK_ID_TRACKING in config["enable_tasks"],
)

env.add_task(
    name=TASK_ID_SYSTEM_MONITORING,
    path=[experiment_path, TASK_PATHS[TASK_ID_SYSTEM_MONITORING]],
    agent_actuators=[SystemMonitoringActuator],
    avatar_actuators=[AvatarSystemMonitoringActuator],
    enable=TASK_ID_SYSTEM_MONITORING in config["enable_tasks"],
)

env.add_task(
    name=TASK_ID_RESOURCE_MANAGEMENT,
    path=[experiment_path, TASK_PATHS[TASK_ID_RESOURCE_MANAGEMENT]],
    agent_actuators=[ResourceManagementActuator],
    avatar_actuators=[AvatarResourceManagementActuator],
    enable=TASK_ID_RESOURCE_MANAGEMENT in config["enable_tasks"],
)
env.run()
