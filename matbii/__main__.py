"""Entry point of a `matbii` simulation.

`matbii` may be run with `python -m matbii -c <CONFIG_FILE>` after installing with pip, where <CONFIG_FILE> is a path to a json configuration file, see the [wiki](https://github.com/dicelab-rhul/matbii/wiki) for details on configuring `matbii`.
"""

if __name__ == "__main__":
    from functools import partial

    # imports for creating the environment
    from matbii.environment import MultiTaskEnvironment

    # imports for creating guidance agents
    from matbii.guidance import (
        DefaultGuidanceAgent,
        ArrowGuidanceActuator,
        BoxGuidanceActuator,
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
    import argparse
    import os

    from star_ray.utils import _LOGGER

    # silence debugging from star_ray logger
    _LOGGER.setLevel("WARNING")

    # avoid a pygame issue on linux...
    os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"

    # load configuration file
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path to configuration file.",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--participant",
        required=False,
        help="ID of the participant.",
        default=None,
    )
    parser.add_argument(
        "-e", "--experiment", required=False, help="ID of the experiment.", default=None
    )

    args = parser.parse_args()
    # args from command line can be used in config
    context = dict(
        experiment=dict(id=args.experiment),
        participant=dict(id=args.participant),
    )
    config = Configuration.from_file(args.config, context=context)

    # Create the avatar:
    # - required sensors are added by default
    # - task related actuators are added when their corresponding task is enabled
    avatar = Avatar(
        [],
        [AvatarActuator()],
        window_config=config.window,
    )

    # if eyetracking is enabled, add a sensor to the avatar
    eyetracking_sensor = config.eyetracking.new_eyetracking_sensor()
    if eyetracking_sensor:
        avatar.add_component(eyetracking_sensor)

    agents = []  # will be given to the environment

    if config.guidance.enable:
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
                # shows arrow pointing at a task as guidance
                ArrowGuidanceActuator(
                    # TODO should be a config option?
                    arrow_mode="gaze" if config.eyetracking.enabled else "mouse",
                    arrow_scale=1.0,  # TODO should be a config option?
                    arrow_fill_color="none",  # TODO should be a config option?
                    arrow_stroke_color="#ff0000",  # TODO should be a config option?
                    arrow_stroke_width=4.0,  # TODO should be a config option?
                    arrow_offset=(80, 80),  # TODO should be a config option?
                ),
                # shows a box around a task as guidance
                BoxGuidanceActuator(
                    box_stroke_color="#ff0000",  # TODO should be a config option?
                    box_stroke_width=4.0,  # TODO should be a config option?
                ),
            ],
            break_ties="random",  # TODO should be a config option?
            grace_period=2.0,  # TODO configuration options
            counter_factual=config.guidance.counter_factual,
        )
        agents.append(guidance_agent)

    env = MultiTaskEnvironment(
        avatar=avatar,
        agents=agents,
        svg_size=config.ui.size,
        svg_position=config.ui.offset,
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
                target_speed=50.0,  # TODO a config option for this?
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
