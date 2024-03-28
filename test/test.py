from matbii import MATBIIEnvironment, QueryLight
import time
import ray

import star_ray.plugin.xml as xml

# from star_ray_example_matbii import MATBIIEnvironment

if __name__ == "__main__":
    try:

        ray.init()

        env = MATBIIEnvironment()
        running = True
        while running:
            time.sleep(0.1)
            # start_time = time.time()
            running = env.step()
            # end_time = time.time()
            # elapsed_time = end_time - start_time
            # print(f"The function took {elapsed_time} seconds to complete.")
            env._ambient.__update__.remote(QueryLight.new_toggle("test", 0))
    except Exception as e:
        raise e
    finally:
        print("SHUTTING DOWN")
        env.close()
