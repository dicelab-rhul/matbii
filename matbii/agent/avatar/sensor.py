from typing import List
from collections import defaultdict
from star_ray.agent import ActiveSensor, OnAwake
from star_ray.event import Observation, Event
from star_ray.plugin.xml import QueryXML, QueryXMLHistory
from .ui import UIAction

from ...utils import _LOGGER

__all__ = ("SVGSensor", "SVGChangeSensor")


# TODO this should probably be a passive sensor. We dont want to constantly be polling for new updates
# TODO implement passive sensing in star_ray using pubsub
class SVGChangeSensor(ActiveSensor):

    def __sense__(self) -> List["QueryXMLHistory"]:
        # this will get all of the changes to the matbii SVG since the end of the last cycle
        return [QueryXMLHistory(index=...)]

    def __transduce__(self, events: List[Observation]):
        try:
            events = list(self._group_events(events))
        except Exception:
            _LOGGER.exception("Failed to group change event attributes.")
            # falling back to ungrouped version. It is ok if this happens once in a while.
            # might need to rethink the grouping operation if this happens regularly, but it shouldn't in the usual running of matbii
            events = list(self._from_events_iter(events))
        return [UIAction(**event) for event in events]

    def _group_events(self, events: List[Observation]):
        # group the changes, we should send only the most recent, and group them together as these are the only that matter for the UI
        changes = sorted(self._from_events_iter(events), key=lambda x: x["timestamp"])
        results = dict()
        # NOTE IMPORTANT: this grouping done for efficiency reasons, but if a query changes the XML tree then grouping like this could break things.
        for change in changes:
            xpath = change["xpath"]
            attrs = change["attributes"]
            if xpath in results:
                results[xpath]["timestamp"] = change["timestamp"]
                if isinstance(attrs, dict):
                    results[xpath]["attributes"].update(attrs)
                else:
                    raise ValueError(
                        f"Failed to group change events, multiple modifications to XML tree structure in the same cycle at xpath {xpath}"
                    )
            else:
                results[xpath] = dict(
                    xpath=xpath, timestamp=change["timestamp"], attributes=attrs
                )

        for result in sorted(results.values(), key=lambda x: x["timestamp"]):
            yield result

    def _from_events_iter(self, events: List[Observation]):
        for event in events:
            for value in event.values:
                yield value


@OnAwake  # this will ensure the sensor only runs once (when the avatar is first created/on its first cycle)
class SVGSensor(ActiveSensor):
    """This sensor observes an entire svg element ONCE (on its first cycle). It can be used again be calling `activate()`."""

    def __init__(self, sv_element_id="root", *args, **kwargs):
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
