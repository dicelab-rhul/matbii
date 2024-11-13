"""Entry point of the `matbii` simulation.

`matbii` may be run with `python -m matbii -c <CONFIG_FILE>` after installing with pip, where <CONFIG_FILE> is a path to a json configuration file, see [documentation](https://dicelab-rhul.github.io/matbii/latest/) for details on configuring `matbii`.
"""

from functools import partial
from typing import Any


# imports for creating the environment
from matbii.environment import MultiTaskEnvironment

# imports for creating guidance agents
from matbii.guidance import (
    DefaultGuidanceAgent,
    SystemMonitoringTaskAcceptabilitySensor,
    TrackingTaskAcceptabilitySensor,
    ResourceManagementTaskAcceptabilitySensor,
)
from matbii.agent import (
    TrackingActuator,
    SystemMonitoringActuator,
    ResourceManagementActuator,
)
from matbii.avatar import (
    Avatar,
    AvatarActuator,
    ExitActuator,
    AvatarTrackingActuator,
    AvatarSystemMonitoringActuator,
    AvatarResourceManagementActuator,
)
from matbii.config import Configuration
from matbii.utils import (
    TASK_PATHS,
    TASK_ID_TRACKING,
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
)


def main(
    config: str | None = None,
    **context: dict[str, Any],
):
    """Run the `matbii` simulation."""
    # args from command line can be used in config
    # context = dict(
    #     experiment=dict(id=experiment) if experiment else dict(),
    #     participant=dict(id=participant) if participant else dict(),
    #     **kwargs,
    # )

    # load configuration from the config file
    config = Configuration.from_file(config, context=context)
    # initialise logging
    config = Configuration.initialise_logging(config)

    # Create the avatar:
    # - required sensors are added by default
    # - task related actuators are added when their corresponding task is enabled
    avatar = Avatar(
        [],
        [AvatarActuator(), ExitActuator()],  # will log user events by default
        window_config=config.window,
    )

    # if eyetracking is enabled, add a sensor to the avatar
    eyetracking_sensor = config.eyetracking.new_eyetracking_sensor()
    if eyetracking_sensor:
        avatar.add_component(eyetracking_sensor)

    agents = []  # will be given to the environment

    # create the guidance agent
    # - sensors will determine the acceptability of each task - if the task is enabled.
    # - change actuators for different guidance to be shown (must inherit from GuidanceActuator)
    guidance_agent = DefaultGuidanceAgent(
        [
            # add more if there are more tasks!
            SystemMonitoringTaskAcceptabilitySensor(),
            ResourceManagementTaskAcceptabilitySensor(),
            TrackingTaskAcceptabilitySensor(),
        ],
        [
            # used to log this agents beliefs for post experiment analysis
            # LogActuator(path=Path(config.logging.path) / "guidance_logs.log"),
            # shows arrow pointing at a task as guidance
            config.guidance.arrow.to_actuator(),
            # shows a box around a task as guidance
            config.guidance.box.to_actuator(),
        ],
        break_ties=config.guidance.break_ties,
        grace_period=config.guidance.grace_period,
        grace_mode=config.guidance.grace_mode,
        attention_mode=config.guidance.attention_mode,
        counter_factual=config.guidance.counter_factual,
    )
    agents.append(guidance_agent)

    env = MultiTaskEnvironment(
        wait=0.01,  # this can be zero as long as it doesnt matter that the env scheduler hogs asyncio: TODO test this with IO devices (eyetracker particularly)
        avatar=avatar,
        agents=agents,
        svg_size=(config.ui.width, config.ui.height),
        logging_path=config.logging.path,
        terminate_after=config.experiment.duration,
    )

    # NOTE: if you have more tasks to add, add them here!
    env.add_task(
        name=TASK_ID_TRACKING,
        path=[config.experiment.path, TASK_PATHS[TASK_ID_TRACKING]],
        agent_actuators=[TrackingActuator],
        avatar_actuators=[
            partial(
                AvatarTrackingActuator,
                # Negative values will invert the direction of movement
                target_speed=-50.0,  # TODO a config option for this?
            )
        ],
        enable=TASK_ID_TRACKING in config.experiment.enable_tasks,
    )

    env.add_task(
        name=TASK_ID_SYSTEM_MONITORING,
        path=[config.experiment.path, TASK_PATHS[TASK_ID_SYSTEM_MONITORING]],
        agent_actuators=[SystemMonitoringActuator],
        avatar_actuators=[AvatarSystemMonitoringActuator],
        enable=TASK_ID_SYSTEM_MONITORING in config.experiment.enable_tasks,
    )

    env.add_task(
        name=TASK_ID_RESOURCE_MANAGEMENT,
        path=[config.experiment.path, TASK_PATHS[TASK_ID_RESOURCE_MANAGEMENT]],
        agent_actuators=[ResourceManagementActuator],
        avatar_actuators=[AvatarResourceManagementActuator],
        enable=TASK_ID_RESOURCE_MANAGEMENT in config.experiment.enable_tasks,
    )
    env.run()
