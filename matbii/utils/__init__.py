"""Package defining various utilities."""

from ._const import (
    TASK_PATHS,
    TASK_ID_TRACKING,
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
)

from icua.utils import LOGGER
import importlib

__all__ = (
    "LOGGER",
    "get_class_from_fqn",
    "TASK_PATHS",
    "TASK_ID_TRACKING",
    "TASK_ID_RESOURCE_MANAGEMENT",
    "TASK_ID_SYSTEM_MONITORING",
)


def get_class_from_fqn(name: str) -> type:
    """Gets a class from its fully qualified name.

    Returns:
        str : fully qualified name of the class.
    """
    module_path, _, class_name = name.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
