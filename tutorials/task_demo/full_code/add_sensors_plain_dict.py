import habitat
import cv2
import os
from habitat.utils.visualizations import maps
import math
import numpy as np
from habitat.config.default_structured_configs import (
    CollisionsMeasurementConfig,
    FogOfWarConfig,
    TopDownMapMeasurementConfig,
)
from habitat.config.default_structured_configs import HabitatSimRGBSensorConfig
from habitat.utils.visualizations.utils import (
    images_to_video,
    observations_to_image,
    overlay_frame,
)
import git 
from omegaconf import OmegaConf
FORWARD_KEY="w"
LEFT_KEY="a"
RIGHT_KEY="d"
FINISH="f"
END='q'

repo = git.Repo(".", search_parent_directories=True)
dir_path = repo.working_tree_dir
data_path = os.path.join(dir_path, "data")

def transform_rgb_bgr(image):
    return image[:, :, [2, 1, 0]]

def example():
    # Create habitat config
    config = habitat.get_config(
        config_path=os.path.join(
            dir_path,
            "./config/benchmark/nav/pointnav/pointnav_habitat_test.yaml",
        )
    )
    print(type(config))
    print(OmegaConf.is_readonly(config.habitat.simulator.agents.main_agent.sim_sensors))
    print(OmegaConf.is_struct(config.habitat.simulator.agents.main_agent.sim_sensors))
    # Add habitat.tasks.nav.nav.TopDownMap and habitat.tasks.nav.nav.Collisions measures
    with habitat.config.read_write(config):
        config.habitat.simulator.agents.main_agent.sim_sensors.top_rgb_sensor = {
        "type": "HabitatSimRGBSensor",
        "width": 256,
        "height": 256,
        "position": [0.0, 1.7, 0.0],
        "sensor_subtype": "PINHOLE",
        "uuid": "new_rgb",
    }          

    env = habitat.Env(
        config=config
    )
    
    print("Environment creation successful")
    observations = env.reset()
    print("Destination, distance: {:3f}, theta(radians): {:.2f}".format(
        observations["pointgoal_with_gps_compass"][0],
        observations["pointgoal_with_gps_compass"][1]))
    print(f"Observation space{env.observation_space}")
    print("Agent stepping around inside environment.")

    cv2.imshow("New-RGB", transform_rgb_bgr(observations["new_rgb"]))
    cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))


    count_steps = 0
    while not env.episode_over:
        keystroke = cv2.waitKey(0)

        if keystroke == ord(FORWARD_KEY):
            action = "move_forward"
        elif keystroke == ord(LEFT_KEY):
            action = "turn_left"
        elif keystroke == ord(RIGHT_KEY):
            action = 'turn_right'
        elif keystroke == ord(FINISH):
            action = 'stop'
        elif keystroke == ord(END):
            break
        else:
            print("INVALID KEY")
            continue

        observations = env.step(action)
        cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))

        cv2.imshow("New-RGB", transform_rgb_bgr(observations["new_rgb"]))
     


    print("Episode finished after {} steps.".format(count_steps))

    if (
        action == "stop"
        and observations["pointgoal_with_gps_compass"][0] < 0.2
    ):
        print("you successfully navigated to destination point")
    else:
        print("your navigation was unsuccessful")


if __name__ == "__main__":
    example()
