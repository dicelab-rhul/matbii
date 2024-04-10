from typing import List
from star_ray.agent import ActiveSensor, OnAwake
from star_ray.event import Observation, Event
from star_ray.plugin.xml import QueryXML, QueryXMLHistory
from .ui import UIAction


__all__ = ("SVGSensor", "SVGChangeSensor")


# TODO this should probably be a passive sensor. We dont want to constantly be polling for new updates
# TODO implement passive sensing in star_ray using pubsub
class SVGChangeSensor(ActiveSensor):

    def __sense__(self) -> List["QueryXMLHistory"]:
        # this will get all of the changes to the matbii SVG since the end of the last cycle
        return [QueryXMLHistory(index=...)]

    def __transduce__(self, events: List[Observation]):
        # each the values contained in each event are the updates that have been performed on the matbii svg
        return list(self._from_events(events))

    def _from_events(self, events: List[Observation]):
        for event in events:
            for value in event.values:
                # value contains xpath, attributes and timestamp
                yield UIAction(source=event.source, **value)


@OnAwake  # this will ensure the sensor only runs once (when the avatar is first created/on its first cycle)
class SVGSensor(ActiveSensor):
    """This sensor observes an entire svg element ONCE (on its first cycle). It can be used again be calling `activate()`."""

    def __init__(self, sv_element_id="root", active=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._svg_element_id = sv_element_id

    def __sense__(self):
        return [QueryXML(self._svg_element_id, [])]

    def __transduce__(self, events: List[Observation]) -> List[Event]:
        event = events[0]  # we should only receive a single event...
        # we need the xpath of the element to enable an update in the UI
        xpath = QueryXML(element_id=self._svg_element_id, attributes=[]).xpath
        # this is the form that the UI is expecting.
        ui_event = UIAction(
            timestamp=event.timestamp,
            source=event.source,
            xpath=xpath,
            attributes=event.values,
        )
        return [ui_event]
