import unittest
from pathlib import Path
from pyfuncschedule import ScheduleParser
from star_ray.agent import Actuator


class MyActuator(Actuator):

    @Actuator.attempt
    def foo(self, arg):
        return f"foo-{arg}"

    @Actuator.attempt
    def bar(self, *args):
        return "bar-1"


def _get_attempt_methods(cls):
    decorated_methods = []
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and hasattr(attr, "is_attempt"):
            decorated_methods.append(attr)
    return decorated_methods


def get_attempt_methods(instance):
    def _get_attempt_methods(cls):
        decorated_methods = []
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and hasattr(attr, "is_attempt"):
                decorated_methods.append(attr)
        return decorated_methods

    methods = _get_attempt_methods(instance.__class__)
    return [method.__get__(instance, instance.__class__) for method in methods]


class TestActuatorSchedule(unittest.TestCase):

    def test(self):
        parser = ScheduleParser()
        actuator = MyActuator()
        for fun in get_attempt_methods(actuator):
            parser.register_action(fun)

        schedule_path = (Path(__file__) / ".." / "actuator_schedule.sch").resolve()
        with open(schedule_path, "r", encoding="UTF-8") as f:
            schedule_str = f.read()
        schedule = parser.parse(schedule_str)
        print(schedule)
        schedule = parser.resolve(schedule)
        print(schedule)


if __name__ == "__main__":
    unittest.main()
