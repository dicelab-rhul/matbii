"""Module containing configuration classes."""

import json
from deepmerge import always_merger
from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    # NonNegativeInt,
    PositiveInt,
    PositiveFloat,
    model_validator,
)
from typing import Any, ClassVar, Literal
from pathlib import Path
from icua.agent.actuator_guidance import ArrowGuidanceActuator, BoxGuidanceActuator
from star_ray.ui import WindowConfiguration
from icua.extras.eyetracking import EyetrackerBase, EyetrackerIOSensor
from ..utils import LOGGER


class GuidanceArrowConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to the arrow guidance."""

    enable: bool = Field(
        default=True,
        description="Whether to enable arrow guidance.",
    )
    mode: Literal["gaze", "mouse", "fixed"] = Field(
        default="gaze",
        description="The mode to use for the arrow guidance, `gaze` will use the current gaze position, `mouse` will use the current mouse position, `fixed` will use the fixed offset specified in `arrow_offset`.",
    )
    scale: float = Field(default=1.0, description="The scale of the arrow.")
    fill_color: str = Field(default="none", description="The fill colour of the arrow.")
    stroke_color: str = Field(
        default="#ff0000", description="The line colour of the arrow outline."
    )
    stroke_width: float = Field(
        default=4.0, description="The line width of the arrow outline."
    )
    offset: tuple[float, float] = Field(
        default=(80, 80),
        description='The offset of the arrow from its set position, this is the position of the arrow if in "fixed" mode.',
    )

    def validate_from_context(self, context: "Configuration"):  # noqa
        if not context.eyetracking.enable and self.mode == "gaze":
            raise ValueError(
                '`guidance.arrow.mode`: "gaze" is not supported when eyetracking is disabled.'
            )

    def to_actuator(self) -> ArrowGuidanceActuator:
        """Factory method for a guidance arrow actuator."""
        return ArrowGuidanceActuator(
            arrow_mode=self.mode,
            arrow_scale=self.scale,
            arrow_fill_color=self.fill_color,
            arrow_stroke_color=self.stroke_color,
            arrow_stroke_width=self.stroke_width,
            arrow_offset=self.offset,
        )


class GuidanceBoxConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to the guidance box."""

    enable: bool = Field(
        default=True, description="Whether to enable the guidance box."
    )
    stroke_color: str = Field(
        default="#ff0000", description="The line colour of the box outline."
    )
    stroke_width: float = Field(
        default=4.0, description="The line width of the box outline."
    )

    def validate_from_context(self, context: "Configuration"):  # noqa
        pass

    def to_actuator(self) -> BoxGuidanceActuator:
        """Factory method for a guidance box actuator."""
        return BoxGuidanceActuator(
            box_stroke_color=self.stroke_color,
            box_stroke_width=self.stroke_width,
        )


_TYPE_BREAK_TIES = Literal["random", "longest"]
_TYPE_GRACE_MODE = Literal["guidance_task", "guidance_any", "failure", "attention"]
_TYPE_ATTENTION_MODE = Literal["fixation", "gaze", "mouse"]


class GuidanceConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to guidance that may be provided to a user."""

    enable: bool = Field(
        default=True,
        description="Whether to enable guidance, if this is False then no guidance agent will be created. Only set this False if you do not plan to use AT ALL in your experiments, otherwise set `counter_factual` to True.",
    )
    counter_factual: bool = Field(
        default=False,
        description="Whether to show guidance to the user, if False then guidance agent will be configured NOT to display guidance but will still take actions for logging purposes (if they support this).",
    )
    break_ties: _TYPE_BREAK_TIES = Field(
        default="random",
        description="How to break ties if guidance may be shown on multiple tasks simultaneously.",
    )
    grace_mode: _TYPE_GRACE_MODE = Field(
        default="attention",
        description="Condition for which the `grace_period` is waiting. Options: `'guidance_task'` - time from last guidance a task, `'guidance_any'` - time from last guidance on _any_ task, `'failure'` - time from last failure a task, `'attention'` - time from when the user last attended to a task (according to `attention_mode`).",
    )
    attention_mode: _TYPE_ATTENTION_MODE = Field(
        default="fixation",
        description="Method used to track the attention of the user. Options: `'fixation'` - use eyetracking fixations, `'gaze'` - use eyetracking (fixation & saccade), `'mouse'` - use the mouse position.",
    )
    grace_period: float = Field(
        default=3.0,
        description="The grace period to use (seconds) - how long to wait before guidance is shown to the user, see also `grace_mode`.",
    )
    arrow: GuidanceArrowConfiguration = Field(
        default_factory=GuidanceArrowConfiguration,
        description="Configuration for displaying arrow guidance.",
    )
    box: GuidanceBoxConfiguration = Field(
        default_factory=GuidanceBoxConfiguration,
        description="Configuration for displaying box guidance.",
    )

    @field_validator("break_ties", mode="before")
    @classmethod
    def _validate_break_ties(cls, value: _TYPE_BREAK_TIES):
        if value.lower() not in ["random", "longest"]:
            raise ValueError(
                f"`guidance.break_ties` must be one of: {_TYPE_BREAK_TIES.__args__}"
            )
        return value.lower()

    @field_validator("attention_mode", mode="before")
    @classmethod
    def _validate_attention_mode(cls, value: _TYPE_ATTENTION_MODE):
        if value.lower() not in _TYPE_ATTENTION_MODE.__args__:
            raise ValueError(
                f"`guidance.attention_mode` must be one of: {_TYPE_ATTENTION_MODE.__args__}"
            )
        return value.lower()

    @field_validator("grace_mode", mode="before")
    @classmethod
    def _validate_grace_mode(cls, value: _TYPE_GRACE_MODE):
        if value.lower() not in _TYPE_GRACE_MODE.__args__:
            raise ValueError(
                f"`guidance.grace_mode` must be one of: {_TYPE_GRACE_MODE.__args__}"
            )
        return value.lower()

    @model_validator(mode="before")
    @classmethod
    def _validate(cls, data: dict[str, Any]):
        if data.get("counter_factual", False) and not data.get("enable", True):
            raise ValueError(
                "`guidance.counter_factual` cannot be True when `guidance.enable` is False. `guidance.enabled = False` should only be used when guidance is not going to be AT ALL in your experiments or analysis as it will completely disable this feature, otherwise, use `guidance.counter_factual = True`."
            )
        return data

    def validate_from_context(self, context: "Configuration"):  # noqa
        if self.enable:
            self.box.validate_from_context(context)
            self.arrow.validate_from_context(context)
            if (
                self.attention_mode in ["gaze", "fixation"]
                and not context.eyetracking.enable
            ):
                raise ValueError(
                    f'`guidance.attention_mode`: "{self.attention_mode}" is not supported when eyetracking is disabled.'
                )


class ExperimentConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to the experiment to be run."""

    id: str | None = Field(
        default=None, description="The unique ID of this experiment."
    )
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

    @field_validator("id", mode="before")
    @classmethod
    def _validate_id(cls, value: str | None):
        if value is None:
            LOGGER.warning("Configuration option: `experiment.id` was set to None")
        return value

    @field_validator("path", mode="before")
    @classmethod
    def _validate_path(cls, value: str):
        # we don't want to set it here, it should remain relative, just check that it exists!
        experiment_path = Path(value).expanduser().resolve()
        if not experiment_path.exists():
            raise ValueError(
                f"Configuration option `experiment.path` is not valid: `{experiment_path.as_posix()}` does not exist."
            )
        return value

    def validate_from_context(self, context: "Configuration"):  # noqa
        pass


class ParticipantConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to the participant (or user)."""

    id: str | None = Field(
        default=None,
        description="The unique ID of the participant that is taking part in the experiment.",
    )
    meta: dict = Field(
        default={},
        description="Any additional meta data you wish to associate with the participant.",
    )

    def validate_from_context(self, context: "Configuration"):  # noqa
        pass


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
    enable: bool = Field(default=False, description="Whether eye tracking is enabled.")
    moving_average_n: PositiveInt = Field(
        default=5,
        description="The window size to used to smooth eye tracking coordinates.",
    )
    velocity_threshold: PositiveFloat = Field(
        default=0.5,
        description="The threshold on gaze velocity which will determine saccades/fixations. This is defined in screen space, where the screen coordinates are normalised in the range [0,1]. **IMPORTANT NOTE:** different monitor sizes may require different values, unfortunately this is difficult to standardise without access to data on the gaze angle (which would be monitor size independent).",
    )

    def validate_from_context(self, context: "Configuration"):  # noqa
        pass

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, data: dict[str, Any]):
        if "enabled" in data:
            LOGGER.warning(
                "Configuration option: `eyetracking.enabled` is deprecated and will be removed in the future, please use `eyetracking.enable` instead."
            )
            data["enable"] = data["enabled"]
            del data["enabled"]
        return data

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
        if self.enable:
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
        if self.enable:
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
        _value = value.upper()
        if _value not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(
                f"Configuration option `logging.level` is invalid: `{value}` must be one of: ['DEBUG', 'INFO', 'WARNING', 'ERROR']"
            )
        return _value


class UIConfiguration(BaseModel, validate_assignment=True):
    """Configuration relating to rendering and the UI."""

    width: PositiveInt = Field(
        default=810,
        description="The width of the canvas used to render the tasks.",
    )
    height: PositiveInt = Field(
        default=680,
        description="The height of the canvas used to render the tasks.",
    )
    # size: tuple[PositiveInt, PositiveInt] = Field(
    #     default=(810, 680),
    #     description="The width and height of the canvas used to render the tasks. This should fully encapsulate all task elements. If a task appears to be off screen, try increasing this value.",
    # )
    # offset: tuple[NonNegativeInt, NonNegativeInt] = Field(
    #     default=(0, 0),
    #     description="The x and y offset used when rendering the root UI element, can be used to pad the top/left of the window.",
    # )

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, data: dict[str, Any]):
        if "size" in data:
            LOGGER.warning(
                "Configuration option: `ui.size` is deprecated and will be removed in the future, please use `ui.width` and `ui.height` instead."
            )
            data["width"] = data["size"][0]
            data["height"] = data["size"][1]
            del data["size"]
        if "offset" in data:
            LOGGER.warning(
                "Configuration option: `ui.offset` is deprecated and has been removed as an option, please instead modify the coordinates of each task to reflect the desired offset."
            )
            del data["offset"]
        return data


def _default_window_configuration_factory():
    window_config = WindowConfiguration()
    window_config.width = 810
    window_config.height = 680
    window_config.title = "icua matbii"
    return window_config


class Configuration(BaseModel, validate_assignment=True):
    """Main configuration class for the default entry point."""

    experiment: ExperimentConfiguration = Field(default_factory=ExperimentConfiguration)
    participant: ParticipantConfiguration = Field(
        default_factory=ParticipantConfiguration
    )
    guidance: GuidanceConfiguration = Field(default_factory=GuidanceConfiguration)
    window: WindowConfiguration = Field(
        default_factory=_default_window_configuration_factory
    )
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
                data = json.load(f)
                data = always_merger.merge(data, context)
                result = Configuration.model_validate(data)
                result.validate_from_context()  # check consistency of nested fields
                return result
        else:
            LOGGER.info("No config file was specified, using default configuration.")
            return Configuration()

    @staticmethod
    def initialise_logging(config: "Configuration") -> "Configuration":
        """Initialises logging for the given run. This will set logging options and set the config logging path which should be used throughout `matbii` to log information that may be relevant for experiment post-analysis. The configuration passed here will also be logged to the `configuration.json` file in the logging path.

        The logging path will be derived: `<config.experiment.id>/<config.participant.id>` if these values are present, otherwise a timestamp will be used to make the logging path unique. If the two ids are given then they are assumed to be unique (they represent a single trial for a participant).

        Args:
            config (Configuration): configuration

        Raises:
            FileExistsError: if the derived logging path already exists.

        Returns:
            Configuration: the configuration (with updated path variables - modified in place)
        """
        # set logging level
        LOGGER.set_level(config.logging.level)

        # set the logger path
        path = Path(config.logging.path).expanduser().resolve()

        # create the full path
        full_path = path
        if config.experiment.id:
            full_path = full_path / config.experiment.id
        if config.participant.id:
            full_path = full_path / config.participant.id

        if path == full_path:
            full_path = full_path / datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

        if full_path.exists():
            raise FileExistsError(
                f"Logging path: {path} already exists, perhaps you have miss-specified `experiment.id` or `participant.id`?\n    See <TODO LINK> for details."
            )

        full_path.mkdir(parents=True)
        LOGGER.debug(f"Logging to: {full_path.as_posix()}")

        # log the configuration that is in use
        with open(full_path / "configuration.json", "w") as f:
            f.write(config.model_dump_json(indent=2))

        config.logging.path = full_path.as_posix()
        return config

    def validate_from_context(self):  # noqa
        self.guidance.validate_from_context(self)
        self.eyetracking.validate_from_context(self)
