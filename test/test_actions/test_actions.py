import unittest

from star_ray import Event
from matbii.ambient import MatbiiAmbient
from matbii.action import (
    SetLightAction,
    ToggleLightAction,
    SetSliderAction,
)
from star_ray.plugin.xml import QueryXPath, QueryXML


class TestActions(unittest.TestCase):

    ambient = MatbiiAmbient([])

    def test_SetSliderAction(self):
        INC = 2
        action = SetSliderAction(target=1, state=INC, relative=True)
        but_target = f"slider-{action.target}-button"
        xpath_parent = f"//*[@id='{but_target}']/parent::node()"
        response1 = TestActions.ambient.__select__(
            QueryXPath(xpath=xpath_parent, attributes=["data-state", "y"])
        )
        response2 = TestActions.ambient.__update__(action)
        response3 = TestActions.ambient.__select__(
            QueryXPath(xpath=xpath_parent, attributes=["data-state", "y"])
        )
        self.assertEqual(
            response1.values[0]["data-state"] + INC, response3.values[0]["data-state"]
        )

    def test_SetLightAction(self):
        action = SetLightAction(target=1, state=1)
        but_target = f"light-{action.target}-button"
        response1 = TestActions.ambient.__select__(
            QueryXML(but_target, ["data-state", "y"])
        )
        response2 = TestActions.ambient.__update__(action)
        response3 = TestActions.ambient.__select__(
            QueryXML(but_target, ["data-state", "y"])
        )
        self.assertEqual(
            abs(response1.values["data-state"] - response3.values["data-state"]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
