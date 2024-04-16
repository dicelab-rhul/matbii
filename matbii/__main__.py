# pylint: disable=E0401, E0611,
from matbii.environment import MatbiiEnvironment

if __name__ == "__main__":
    # potentially get some command line arguments?
    env = MatbiiEnvironment()
    env.run()
