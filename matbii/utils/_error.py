__all__ = ("MatbiiInternalError", "MatbiiScheduleError")


class MatbiiInternalError(Exception):
    pass


class MatbiiScheduleError(MatbiiInternalError):
    pass
