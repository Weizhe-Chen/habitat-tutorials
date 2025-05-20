# Visualization Introduction

This tutorial mainly introduces visualization for navigation tasks, including topdown map, agent, birdview.

## Top Down Map

Visualization for top down map, bird view and agent is implemented in `Map` defined [here](https://github.com/facebookresearch/habitat-lab/tree/main/habitat-lab/habitat/utils/visualizations).

To plot top down map:
1. import `map` class
   ```python
   from habitat.utils.visualizations import maps
   ```
2. Get top down map
   ```python
    topdown_map = maps.get_topdown_map_from_sim(env.sim, map_resolution=512)
    topdown_map_color = maps.colorize_topdown_map(topdown_map)
   ```
3. Plot
   ```python
   cv2.imshow("top_down_map", topdown_map_color)
   ```

If you want to plot agent on the top down map, you should calculate the yaw of the agent, you should pay attention to coordinate transform:
1. Get agent pose
   ```python
    agent_pos = env.sim.get_agent_state().position  # (x, y, z)
    agent_rot = env.sim.get_agent_state().rotation  # quat
   ```
2. Calculate yaw
   ```python
    q = agent_rot  
    yaw = quat_to_yaw(q)
   ```
3. Calculate agent position in grid map
   ```python
    map_resolution = topdown_map.shape[0:2]
    grid_x, grid_y = maps.to_grid(agent_pos[2], agent_pos[0], grid_resolution=map_resolution, sim=env.sim) # Pay attention to axis here
   ```
4. Add agent to top down map:
   ```python
   topdown_with_agent = maps.draw_agent(
            topdown_map_color.copy(),
            (grid_x, grid_y),  # Attention to the x,y order
            agent_rotation=yaw,
            agent_radius_px=10,
        )
   ```
5. Plot
   ```python
   cv2.imshow("Top-Down Map with Agent", topdown_with_agent)
   ```

## Bird View

Bird view can also be plotted direclty using `pointnav_draw_target_birdseye_view()` method in `Map`, however, you should pay attention to transformation. Also, you should get the target position. 
```python
birdseye_view = maps.pointnav_draw_target_birdseye_view(
            agent_position=agent_pos,
            agent_heading=yaw,
            goal_position=goal_position,
        )
```

Here is the full code for plotting top down map and bird view:
```python
import habitat
import cv2
import os
from habitat.utils.visualizations import maps
import math
import numpy as np

FORWARD_KEY="w"
LEFT_KEY="a"
RIGHT_KEY="d"
FINISH="f"
END='q'

def transform_rgb_bgr(image):
    return image[:, :, [2, 1, 0]]

def quat_to_yaw(q):
    # Extract yaw angle around Y axis
    siny_cosp = 2.0 * (q.w * q.y - q.z * q.x)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.x * q.x)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    # Normalize yaw to [-pi, pi]
    if yaw < -math.pi:
        yaw += 2 * math.pi
    if yaw > math.pi:
        yaw -= 2 * math.pi
    
    # Map image: positive yaw should rotate clockwise, flip sign
    # yaw = -yaw
    yaw  -= math.pi 

    return yaw

def compute_goal_position(agent_pos, agent_yaw, distance, theta):
    x_goal = agent_pos[2] + distance * math.cos(agent_yaw + theta)
    z_goal = agent_pos[0] + distance * math.sin(agent_yaw + theta)
    y_goal = agent_pos[1]  # 高度保持不变
    return np.array([z_goal, y_goal, x_goal])

def example():
    env = habitat.Env(
        config=habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
    )
    
    print("Environment creation successful")
    observations = env.reset()
    print("Destination, distance: {:3f}, theta(radians): {:.2f}".format(
        observations["pointgoal_with_gps_compass"][0],
        observations["pointgoal_with_gps_compass"][1]))
    cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))

    print("Agent stepping around inside environment.")
    agent_inil_pos = env.sim.get_agent_state().position
    distance = observations["pointgoal_with_gps_compass"][0]
    theta = observations["pointgoal_with_gps_compass"][1]
    yaw = quat_to_yaw(env.sim.get_agent_state().rotation)
    goal_position = compute_goal_position(agent_inil_pos, yaw, distance, theta)
    print(f"goal position:{goal_position}")


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

        print(f"action:{action}")
        observations = env.step(action)
        count_steps += 1

        print("Destination, distance: {:3f}, theta(radians): {:.2f}".format(
            observations["pointgoal_with_gps_compass"][0],
            observations["pointgoal_with_gps_compass"][1]))
        
        topdown_map = maps.get_topdown_map_from_sim(env.sim, map_resolution=512)
        topdown_map_color = maps.colorize_topdown_map(topdown_map)
        
        agent_pos = env.sim.get_agent_state().position  # (x, y, z)
        agent_rot = env.sim.get_agent_state().rotation  # quat
        
        print(f"agent_pos:{agent_pos}")
        print(f"goal position:{goal_position}")
        q = agent_rot  
        yaw = quat_to_yaw(q)
        print(f"yaw:{yaw}")
        # Convert real world x z to image axis
        map_resolution = topdown_map.shape[0:2]
        grid_x, grid_y = maps.to_grid(agent_pos[2], agent_pos[0], grid_resolution=map_resolution, sim=env.sim)
        topdown_with_agent = maps.draw_agent(
            topdown_map_color.copy(),
            (grid_x, grid_y),  # Attention to the x,y order
            agent_rotation=yaw,
            agent_radius_px=10,
        )

        birdseye_view = maps.pointnav_draw_target_birdseye_view(
            agent_position=agent_pos,
            agent_heading=yaw,
            goal_position=goal_position,
        )

        cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))
        cv2.imshow("Top-Down Map with Agent", topdown_with_agent)
        cv2.imshow("PointNav Birdseye View", birdseye_view)

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
```
## Plot top down map using measurements

A more simple way to plot top down map is to use meansurements. By default, habitat has registered `TopDownMapMeasurementConfig` as a meansurement, as long as  `CollisionsMeasurementConfig`, `FogOfWarConfig`, we can add them to existing config under key `measurement` to directly get the measurements.

1. Add these default structured config to existing config:
   ```python
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
   ```
2. Create `env` use the new config:
   ```python
    env = habitat.Env(config=config)
   ```
3. Get measurements:
   ```python
   # Get metrics
    info = env.get_metrics()
   ```
4. plot the measurements(here we plot the top down map together with observations):
   ```python
   frame = observations_to_image(observations, info)
   ```
5. Add the other information in measurements to frame
   ```python
   # Remove top_down_map from metrics
    info.pop("top_down_map")
    # Overlay numeric metrics onto frame
    frame = overlay_frame(frame, info)
   ```
6. Plot the frame
   ```python
    frame = transform_rgb_bgr(frame)
    cv2.imshow("RGB with TopDown Map", frame)
   ```

Below is the full code:
```python
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
```