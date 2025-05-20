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
