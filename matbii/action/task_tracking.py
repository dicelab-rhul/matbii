""" Action definitions for the tracking task. """

from typing import Tuple

from star_ray.event import Action
from star_ray.plugin.xml import QueryXMLTemplated, QueryXPath


class TargetMoveAction(Action):
    direction: Tuple[float, float]
    speed: float

    @staticmethod
    def new(direction: Tuple[float, float], speed: float) -> "TargetMoveAction":
        return TargetMoveAction(direction=direction, speed=speed)


# @ActiveActuator.attempt
# def move_target(self, direction: Tuple[float, float], speed: float):
#     # normalise the direction
#     d = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
#     direction = (direction[0] / d, direction[1] / d)
#     # return QueryXMLTemplated.new(
#     #     self.id,
#     #     target,
#     #     {
#     #         "data-state": "%s" % state,
#     #         "fill": "{{data_colors[%s]}}" % state,
#     #     },
#     # )
