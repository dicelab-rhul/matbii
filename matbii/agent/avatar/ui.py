from typing import Dict, List, Any
from star_ray import Event


class UIAction(Event):

    xpath: str
    attributes: str | List[Any] | Dict[str, Any]
