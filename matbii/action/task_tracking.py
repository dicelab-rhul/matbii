""" Action definitions for the tracking task. """

import math
from typing import Tuple, List
from pydantic import validator
from star_ray.event import Action
from star_ray.plugin.xml import QueryXMLTemplated, QueryXML, XMLState, QueryXPath
from ..utils import TASK_ID_TRACKING, _LOGGER

TARGET_ID = "tracking_target"
TRACKING_MODES = ["MANUAL", "AUTO"]


# TODO
class TrackingModeAction(Action):

    manual: bool

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        pass


class TargetMoveAction(Action):
    direction: Tuple[float, float]
    speed: float

    @validator("direction", pre=True, always=True)
    @classmethod
    def _validate_direction(cls, value):
        if isinstance(value, tuple):
            if len(value) == 2:
                # normalise the direction
                d = math.sqrt(value[0] ** 2 + value[1] ** 2)
                if d == 0:
                    return (0.0, 0.0)
                return (float(value[0]) / d, float(value[1]) / d)
        raise ValueError(f"Invalid direction {value}, must be Tuple[float,float].")

    @validator("speed", pre=True, always=True)
    @classmethod
    def _validate_speed(cls, value):
        return float(value)

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        if self.direction == (0.0, 0.0):
            _LOGGER.warning(
                "Attempted %s with direction (0,0)", TargetMoveAction.__name__
            )
            return []  # going no where...
        d1 = self.direction[0] * self.speed
        d2 = self.direction[1] * self.speed
        # get properties of the tracking task
        query = QueryXML(element_id=TASK_ID_TRACKING, attributes=["width", "height"])
        values = state.__select__(query).values
        # task bounds should limit the new position
        x1, y1 = (0, 0)
        x2, y2 = x1 + values["width"], y1 + values["height"]

        new_x = f"max(min(x + {d1}, {x2} - width), {x1})"
        new_y = f"max(min(y + {d2}, {y2} - height), {y1})"

        return [
            QueryXMLTemplated(
                TARGET_ID,
                {"x": "{{%s}}" % new_x, "y": "{{%s}}" % new_y},
            )
        ]
