"""Module contains the base class for task acceptability sensors `TaskAcceptabilitySensor`, it is an extension of the base class that is part of `icua` which includes functionality for determining if a task is active based on whether the task element is present in the environment state."""

from typing import Any
from star_ray.event import Event, Observation, ActiveObservation, ErrorObservation
from star_ray_xml import XPathElementsNotFound, Select
from icua.agent import TaskAcceptabilitySensor as _TaskAcceptabilitySensor


class TaskAcceptabilitySensor(_TaskAcceptabilitySensor):
    """This `Sensor` can be used by an agent to track the acceptability of a task."""

    def __init__(self, task_name: str, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            task_name (str): task to track.
            args (list[Any]): Additional optional arguments.
            kwargs (dict[str,Any]): Additional optionals keyword arguments.
        """
        super().__init__(task_name, *args, **kwargs)
        self._is_active = True  # unless it cannot be found...
        # the id of the action that is used to check whether the task is active
        self._is_active_action_id = None

    def is_active(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        return self._is_active  # this is not done by subclass

    def __transduce__(self, observations: list[Observation]) -> list[Observation]:  # noqa
        # fetch the observation that is the result of the is_active action and update _is_active
        # this must happen before beliefs are updated since some updates may depend on whether the task is active
        self._update_is_active(observations)
        return super().__transduce__(observations)

    def on_error_observation(self, observation: ErrorObservation):  # noqa
        if self._is_active:
            return super().on_error_observation(observation)
        # if the task is inactive then some observations may result in XPathElementsNotFound
        if issubclass(observation.resolve_exception_type(), XPathElementsNotFound):
            pass  # ignore these
        else:
            # these may still be relevant
            return super().on_error_observation(observation)

    def _update_is_active(self, observations: list[Observation]) -> bool:
        """Checks whether the task is currently active based on the observation resulting from the `is_active` action."""
        is_active_observation = list(
            filter(
                lambda x: isinstance(x, ActiveObservation)
                and x.action_id == self._is_active_action_id,
                observations,
            )
        )
        if len(is_active_observation) == 0:
            # the is_active observation was not part of these observations
            # this can happen if the sensor is receiving observations via subscription
            return
        # the is_active observation was part of the observations, check it
        is_active_observation = is_active_observation[0]
        if self._is_active:
            if isinstance(is_active_observation, ErrorObservation):
                self._is_active = False  # the task is now inactive!
            else:
                self._is_active = True  # the task is active and remains active
        else:
            if not isinstance(is_active_observation, ErrorObservation):
                self._is_active = True  # the task is inactive and may now be active
            else:
                self._is_active = False  # the task is inactive and remains inactive

    def __sense__(self) -> list[Event]:  # noqa
        if self._is_active:
            actions = self.sense()
            if not isinstance(actions, list | tuple):
                raise TypeError(
                    f"`sense()` must return a `list` of events, received: {type(actions)}"
                )
        else:
            actions = []
        # always check if the task is active
        is_active = Select(xpath=f"//*[@id='{self.task_name}']", attrs=["id"])
        self._is_active_action_id = is_active.id
        actions.insert(0, is_active)
        return actions
