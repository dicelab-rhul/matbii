"""Module containing configuration classes."""

from pydantic import BaseModel, Field, field_validator
from typing import Any, ClassVar
from pathlib import Path
from star_ray.ui import WindowConfiguration
from icua.extras.eyetracking import EyetrackerBase, EyetrackerIOSensor
from ..utils import LOGGER


class GuidanceConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to guidance that may be provided to a user."""

    enable: bool = Field(
        default=True,
        description="Whether to enable guidance, if this is False then no guidance agent will be created.",
    )
    counter_factual: bool = Field(
        default=False,
        description="Whether to show guidance to the user, if False then guidance agent will be configured NOT to display guidance but will still take actions for logging purposes (if they support this).",
    )
    # guidance_actuator_types: tuple[type] = Field(
    #     default=(
    #         ArrowGuidanceActuator,  # "matbii.guidance.ArrowGuidanceActuator",
    #         BoxGuidanceActuator,  # "matbii.guidance.BoxGuidanceActuator",
    #     ),
    #     description="The type of each actuator that the guidance agent will use. When specifying a type use the full path, for example: `matbii.guidance.ArrowGuidanceActuator`.",
    # )
    # guidance_agent_type: type = Field(
    #     default=DefaultGuidanceAgent,  # "matbii.guidance.DefaultGuidanceAgent",
    #     description="The type of each actuator that the guidance agent will use. When specifying a type use the full path, for example: `matbii.guidance.ArrowGuidanceActuator`.",
    # )
    # guidance_agent_args: dict[str, Any] = Field(
    #     default_factory=dict,
    #     description="Any additional arguments to give to the guidance agent upon instantiation.",
    # )

    # @field_validator(
    #     "guidance_actuator_types",
    #     mode="before",
    # )
    # @classmethod
    # def _validate_guidance_actuator_types(cls, value: Any):
    #     if not isinstance(value, list | tuple):
    #         raise TypeError(f"Invalid type: {value}")
    #     result = []
    #     for f in value:
    #         if isinstance(f, type):
    #             result.append(result)
    #         elif isinstance(f, str):
    #             result.append(get_class_from_fqn(f))
    #         else:
    #             raise TypeError(
    #                 f"Expected `str` or `type` but got: `{type(value)}` for value: {value}"
    #             )
    #     return value

    # @field_validator("guidance_agent_type", mode="before")
    # @classmethod
    # def _validate_guidance_agent_type(cls, value: Any):
    #     if isinstance(value, type):
    #         return value
    #     elif isinstance(value, str):
    #         return get_class_from_fqn(value)
    #     else:
    #         raise TypeError(
    #             f"Expected `str` or `type` but got: `{type(value)}` for value: {value}"
    #         )


class ExperimentConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to the experiment to be run."""

    id: str = Field(default=None, description="The unique ID of this experiment.")
    path: str = Field(
        # default_factory=lambda: Path("./").resolve().as_posix(),
        default="./",
        description="The full path to the directory containing task configuration files. If this is a relative path it is relative to the current working directory.",
    )
    duration: int = Field(
        default=-1,
        description="The duration (in seconds) of this experiment (the simulation will close after this time), a negative value will leave the simulation running forever.",
    )
    enable_video_recording: bool = Field(
        default=False,
        description="Whether to begin a screen recording of the experiment when the simulation starts, the video will be saved to the logging path when the experiment ends.",
    )
    enable_tasks: list[str] = Field(
        default=["system_monitoring", "resource_management", "tracking"],
        description="Which tasks to enable at the start of the simulation.",
    )
    meta: dict = Field(
        default={},
        description="Any additional meta data you wish to associate with this experiment.",
    )

    # @field_validator("path", mode="before")
    # @classmethod
    # def _validate_path(cls, value: str):
    #     experiment_path = Path(value).expanduser().resolve()
    #     if not experiment_path.exists():
    #         raise ValueError(
    #             f"Experiment path: {experiment_path.as_posix()} does not exist."
    #         )
    #     return experiment_path.as_posix()


class ParticipantConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to the participant (or user)."""

    id: str = Field(
        default=None,
        description="The unique ID of the participant that is taking part in the experiment.",
    )
    meta: dict = Field(
        default={},
        description="Any additional meta data you wish to associate with the participant.",
    )


class EyetrackingConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to eyetracking."""

    SUPPORTED_SDKS: ClassVar[tuple[str]] = ("tobii",)

    uri: str | None = Field(
        default=None,
        description="The eye tracker address (example: `'tet-tcp://172.28.195.1'`). If left unspecified `matbii` will attempt to find an eye tracker. For details on setting up eye tracking, consult the [wiki](https://github.com/dicelab-rhul/matbii/wiki/Eyetracking).",
    )
    sdk: str = Field(
        default="tobii",
        description="The eye tracking SDK to use, current options are: `['tobii']`.",
    )
    enabled: bool = Field(default=False, description="Whether eye tracking is enabled.")
    moving_average_n: int = Field(
        default=5,
        description="The window size to used to smooth eye tracking coordinates.",
    )
    velocity_threshold: float = Field(
        default=0.5,
        description="The threshold on gaze velocity which will determine saccades/fixations. This is defined in screen space, where the screen coordinates are normalised in the range [0,1]. **IMPORTANT NOTE:** different monitor sizes may require different values, unfortunately this is difficult to standardise without access to data on the gaze angle (which would be monitor size independent).",
    )

    @field_validator("sdk", mode="before")
    @classmethod
    def _validate_sdk(cls, value: str):
        if value not in EyetrackingConfiguration.SUPPORTED_SDKS:
            raise ValueError(
                f"Eyetracker SDK: {value} is not supported, must be one of {EyetrackingConfiguration.SUPPORTED_SDKS}"
            )
        return value

    def new_eyetracking_sensor(self) -> EyetrackerIOSensor | None:
        """Factory method for an eyetracking sensor.

        Returns:
            EyetrackerIOSensor | None: the sensor, created based on this eyetracking configuration.
        """
        if self.enabled:
            eyetracker = self.new_eyetracker()
            return EyetrackerIOSensor(
                eyetracker, self.velocity_threshold, self.moving_average_n
            )
        return None

    def new_eyetracker(self) -> EyetrackerBase | None:
        """Factory method for an eyetracker.

        Returns:
            EyetrackerBase | None: the eyetracker created based on this eyetracking configuration.
        """
        if self.enabled:
            if self.sdk == "tobii":
                return self._new_tobii_eyetracker()
            else:
                raise ValueError(
                    f"Eyetracker SDK: {self.sdk} is not supported, must be one of {EyetrackingConfiguration.SUPPORTED_SDKS}"
                )
        return None

    def _new_tobii_eyetracker(self) -> EyetrackerBase:
        from icua.extras.eyetracking import tobii  # this may fail!

        return tobii.TobiiEyetracker(uri=self.uri)


class LoggingConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to logging (including event logging)."""

    level: str = Field(
        default="INFO",
        description="The logging level to use: ['DEBUG', 'INFO', 'WARNING', 'ERROR'], this will not affect event logging.",
    )
    path: str = Field(
        default="./logs/",
        description="The path to the directory where log files will be written.",
    )

    @field_validator("level", mode="before")
    @classmethod
    def _validate_level(cls, value: str):
        return value.upper()


class UIConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to rendering and the UI."""

    size: tuple[int, int] = Field(
        default=(800, 600),
        description="The width and height of the canvas used to render the tasks. This should fully encapsulate all task elements. If a task appears to be off screen, try increasing this value.",
    )
    offset: tuple[int, int] = Field(
        default=(0, 0),
        description="The x and y offset used when rendering the root UI element, can be used to pad the top/left of the window.",
    )


class Configuration(BaseModel, validate_assignment=True):
    """Matbii can be configured using a .json file.

    The path of this file is supplied as `-c CONFIG PATH`, for example:

    ```
    python -m matbii -c ./experiment-config.json
    ```

    !!! note "Custom entry points"
        The main configuration outlined here is used in the default entry point (`__main__.py`), but may also be useful for custom entry points.

    The default entry point (main) configuration has sections corresponding to a specific aspect of the simulation. Not all options need to be specified and most have reasonable default values.
    """

    experiment: ExperimentConfiguration = Field(default_factory=ExperimentConfiguration)
    participant: ParticipantConfiguration = Field(
        default_factory=ParticipantConfiguration
    )
    guidance: GuidanceConfiguration = Field(default_factory=GuidanceConfiguration)
    window: WindowConfiguration = Field(default_factory=WindowConfiguration)
    eyetracking: EyetrackingConfiguration = Field(
        default_factory=EyetrackingConfiguration
    )
    logging: LoggingConfiguration = Field(default_factory=LoggingConfiguration)
    ui: UIConfiguration = Field(default_factory=UIConfiguration)

    @staticmethod
    def from_file(
        path: str | Path | None, context: dict[str, Any] | None = None
    ) -> "Configuration":
        """Factory that will build `Configuration` from a .json file.

        Args:
            path (str | Path | None): path to config file.
            context (dict[str, Any] | None, optional): additional context (to override file content). Defaults to None.

        Returns:
            Configuration: resulting configuration.
        """
        context = context if context else {}
        if path:
            path = Path(path).expanduser().resolve().as_posix()
            LOGGER.info(f"Using config file: {path}")
            with open(path) as f:
                return Configuration.model_validate_json(f.read(), context=context)
        else:
            LOGGER.info("No config file was specified, using default configuration.")
            return Configuration()
