""" Action definitions for the resource management task. """

from typing import Tuple
from dataclasses import dataclass, astuple

from star_ray.plugin.xml import QueryXMLTemplated, QueryXPath

from ..utils import MatbiiInternalError
