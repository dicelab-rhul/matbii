import random
import time
import math
from typing import Tuple
from types import MethodType
from star_ray.agent import Agent, ActiveActuator, attempt
from star_ray.event import ErrorActiveObservation
from pyfuncschedule import ScheduleParser


from ..action import (
    SetLightAction,
    ToggleLightAction,
    SetSliderAction,
    TargetMoveAction,
    BurnFuelAction,
    PumpFuelAction,
)

from ..utils import _LOGGER, DEFAULT_SCHEDULE_FILE, MatbiiScheduleError


class MatbiiActuator(ActiveActuator):

    @attempt
    def burn_fuel(self, target: int | str, burn: float):
        return BurnFuelAction(target=target, burn=burn)

    @attempt
    def fail_light(self, target: int):
        return SetLightAction(target=target, state=0)

    @attempt
    def toggle_light(self, target: int):
        return ToggleLightAction(target=target)

    @attempt
    def perturb_slider(self, target: int):
        state = 2 * random.randint(0, 1) - 1  # randomly perturb +/- 1
        return SetSliderAction(target=target, state=state, relative=True)

    @attempt
    def move_target(self, direction: Tuple[float, float] | int | float, speed: float):
        # an angle was provided (in degrees), convert it to a direction vector
        if isinstance(direction, (int, float)):
            angle = math.radians(direction)
            direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)

    @attempt
    def perturb_target(self, speed: float):
        angle = (random.random() * 2 - 1) * math.pi
        direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)


class ScheduleRunner:

    def __init__(self, schedule, current_time):
        self._schedule = schedule
        self._schedule_iter = iter(schedule)
        self._wait, _ = next(self._schedule_iter)
        self._time = current_time

    def step(self, current_time):
        if self.is_completed:
            raise MatbiiScheduleError(
                "Attempting to run completed schedule:", str(self._schedule)
            )
        if self._wait <= (current_time - self._time):
            # its time to attempt the next action, this will be handled by the ActionSchedule via direct calls to the MatbiiActuator.
            self._wait, _ = next(self._schedule_iter)
            # wait will be None on the final execution of the schedule action
            if self.is_completed:
                _LOGGER.debug("Schedule %s completed.", str(self._schedule))
            self._time = current_time
        return self.is_completed

    @property
    def is_completed(self):
        return self._wait is None


class MatbiiAgent(Agent):

    def __init__(self, schedule_path: str = None):
        schedules, actuator = self._load_schedule(MatbiiActuator(), schedule_path)
        super().__init__([], [actuator])
        current_time = time.time()
        self._schedule_runners = [
            ScheduleRunner(schedule, current_time) for schedule in schedules
        ]

    def _step_runners(self):
        current_time = time.time()
        for runner in self._schedule_runners:
            if not runner.step(current_time):
                yield runner

    def __cycle__(self):
        self._schedule_runners = list(self._step_runners())
        # check observation results for errors
        actuator = next(iter(self.actuators))
        for obs in actuator.get_observations():
            if isinstance(obs, ErrorActiveObservation):
                _LOGGER.error("Observation error for scheduled action: %s", repr(obs))

    @staticmethod
    def get_attempt_methods(actuator):
        for fun in actuator.__class__.__attemptmethods__:
            yield MethodType(fun, actuator)

    def _load_schedule(self, actuator, schedule_file=None):
        if schedule_file is None:
            schedule_file = DEFAULT_SCHEDULE_FILE
        parser = ScheduleParser()
        for fun in MatbiiAgent.get_attempt_methods(actuator):
            _LOGGER.debug("Registered attempts in schedule: %s", fun.__name__)
            parser.register_action(fun)

        from random import uniform, randint

        parser.register_function(uniform)
        parser.register_function(randint)
        parser.register_function(min)
        parser.register_function(max)

        _LOGGER.debug("Reading schedule file: `%s`", schedule_file)
        with open(schedule_file, "r", encoding="UTF-8") as f:
            schedule_str = f.read()
        schedule = parser.parse(schedule_str)
        schedule = parser.resolve(schedule)
        _LOGGER.debug(
            "Successfully loaded schedule:\n    %s",
            "\n    ".join(str(sch) for sch in schedule),
        )
        _LOGGER.debug("")
        return schedule, actuator
