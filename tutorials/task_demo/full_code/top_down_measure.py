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
from habitat.utils.visualizations.utils import (
    images_to_video,
    observations_to_image,
    overlay_frame,
)
import git 

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
    
    # Add habitat.tasks.nav.nav.TopDownMap and habitat.tasks.nav.nav.Collisions measures
    with habitat.config.read_write(config):
        config.habitat.task.measurements.update(
            {
                "top_down_map": TopDownMapMeasurementConfig(
                    map_padding=3,
                    map_resolution=1024,
                    draw_source=True,
                    draw_border=True,
                    draw_shortest_path=True,
                    draw_view_points=True,
                    draw_goal_positions=True,
                    draw_goal_aabbs=True,
                    fog_of_war=FogOfWarConfig(
                        draw=True,
                        visibility_dist=5.0,
                        fov=90,
                    ),
                ),
                "collisions": CollisionsMeasurementConfig(),
            }
        )

    env = habitat.Env(
        config=config
    )
    
    print("Environment creation successful")
    observations = env.reset()
    print("Destination, distance: {:3f}, theta(radians): {:.2f}".format(
        observations["pointgoal_with_gps_compass"][0],
        observations["pointgoal_with_gps_compass"][1]))

    print("Agent stepping around inside environment.")
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
        # Get metrics
        info = env.get_metrics()
        # Concatenate RGB-D observation and topdowm map into one image
        frame = observations_to_image(observations, info)

        # Remove top_down_map from metrics
        info.pop("top_down_map")
        # Overlay numeric metrics onto frame
        frame = overlay_frame(frame, info)
        # Add fame to vis_frames
        frame = transform_rgb_bgr(frame)
        cv2.imshow("RGB with TopDown Map", frame)
     


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
