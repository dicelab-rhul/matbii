# def table_of_attempt_signatures(actuator_fully_qualified_paths: list[str]):
#     get_attempts()


# if __name__ == "__main__":
#     from matbii.tasks import (
#         TrackingActuator,
#         SystemMonitoringActuator,
#         ResourceManagementActuator,
#     )
#     import griffe

#     fqcn = f"{TrackingActuator.__module__}.{TrackingActuator.__name__}"
#     fqcn = f"{SystemMonitoringActuator.__module__}.{SystemMonitoringActuator.__name__}"

#     fqcn = (
#         f"{ResourceManagementActuator.__module__}.{ResourceManagementActuator.__name__}"
#     )
#     # fqcn = "matbii.tasks.ResourceManagementActuator"
#     for a in get_attempts(fqcn):
#         print(a)
