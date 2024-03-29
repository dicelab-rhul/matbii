import random
import time
from star_ray.agent import Agent, ActiveActuator
from star_ray.plugin.xml import QueryXMLTemplated
from star_ray.event import ErrorResponse
from pyfuncschedule import ScheduleParser

import logging
from ..utils import DEFAULT_SCHEDULE_PATH

_LOGGER = logging.getLogger("matbii")

DEFAULT_SCHEDULE_FILE = DEFAULT_SCHEDULE_PATH / "default_schedule.sch"


class MatbiiActuator(ActiveActuator):

    @ActiveActuator.attempt
    def set_light(self, target: int, state: int):
        # typically there are only two lights TODO but the agent should discover this...
        assert target in [1, 2]
        assert state in [0, 1]
        target = f"light-{target}-button"
        return QueryXMLTemplated.new(
            self.id,
            target,
            {
                "data-state": "%s" % state,
                "fill": "{{data_colors[%s]}}" % state,
            },
        )

    @ActiveActuator.attempt
    def light_failure(self, target: int):
        # typically there are only two lights TODO but the agent should discover this...
        assert target in [1, 2]
        target = f"light-{target}-button"
        failure_state = 1
        return QueryXMLTemplated.new(
            self.id,
            target,
            {
                "data-state": "%s" % failure_state,
                "fill": "{{data_colors[%s]}}" % failure_state,
            },
        )

    @ActiveActuator.attempt
    def toggle_light(self, target: int):
        # typically there are only two lights TODO but the agent should discover this...
        assert target in [1, 2]
        target = f"light-{target}-button"
        return QueryXMLTemplated.new(
            self.id,
            target,
            {
                "data-state": "{{1-data_state}}",
                "fill": "{{data_colors[1-data_state]}}",
            },
        )

    @ActiveActuator.attempt
    def toggle_slider(self, target: int):
        # typically there are only 4 lights TODO but the agent should discover this...
        assert target in [1, 2, 3, 4]
        state = 2 * random.randint(0, 1) - 1  # randomly perturb the state
        target = f"slider-{target}-button"
        state_template = "min(max(data_statemin, data_state+%s), data_statemax)" % state
        return QueryXMLTemplated.new(
            self.id,
            target,
            {
                "data-state": "{{%s}}" % state_template,
                "y": "{{data_padding + %s * data_height}}" % state_template,
            },
        )

    def get_attempt_methods(self):
        def _get_attempt_methods(cls):
            decorated_methods = []
            for attr_name in dir(cls):
                attr = getattr(cls, attr_name)
                if callable(attr) and hasattr(attr, "is_attempt"):
                    decorated_methods.append(attr)
            return decorated_methods

        methods = _get_attempt_methods(self.__class__)
        return [method.__get__(self, self.__class__) for method in methods]


# import unittest
# from pathlib import Path
# from star_ray.agent import ActiveActuator


class MatbiiScheduleError(Exception):
    pass


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
        for obs in self.actuators[0].get_observations():
            if isinstance(obs, ErrorResponse):
                _LOGGER.error(
                    "ErrorResponse caught for scheduled action. TODO See error logs for details."
                )

    def _load_schedule(self, actuator, schedule_file=None):
        if schedule_file is None:
            schedule_file = DEFAULT_SCHEDULE_FILE
        parser = ScheduleParser()
        for fun in actuator.get_attempt_methods():
            _LOGGER.debug("Registered attempts in schedule: %s", fun.__name__)
            parser.register_action(fun)

        from random import uniform, randint

        parser.register_function(uniform)
        parser.register_function(randint)
        parser.register_function(min)
        parser.register_function(max)

        _LOGGER.debug("Reading schedule file: %s", schedule_file)
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
