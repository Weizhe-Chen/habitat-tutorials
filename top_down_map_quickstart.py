import habitat
import cv2
import os
from habitat.utils.visualizations import maps
import math

FORWARD_KEY="w"
LEFT_KEY="a"
RIGHT_KEY="d"
FINISH="f"


def transform_rgb_bgr(image):
    return image[:, :, [2, 1, 0]]

def quat_to_yaw(q):
    # Extract yaw angle around Y axis
    siny_cosp = 2.0 * (q.w * q.y - q.z * q.x)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.x * q.x)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    # Habitat forward = -Y axis, so zero yaw should correspond to facing -Y.
    # atan2 result zero is +X axis in math coord, so rotate yaw by -pi/2
    # yaw -= math.pi 
    
    # Normalize yaw to [-pi, pi]
    if yaw < -math.pi:
        yaw += 2 * math.pi
    if yaw > math.pi:
        yaw -= 2 * math.pi
    
    # Map image: positive yaw should rotate clockwise, flip sign
    # yaw = -yaw
    
    return yaw

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
        print(f"agent_rot:{agent_rot}")
        q = agent_rot  
        yaw = quat_to_yaw(q)
        print(f"yaw:{yaw}")
        # Convert real world x z to image axis
        map_resolution = topdown_map.shape[0:2]
        grid_x, grid_y = maps.to_grid(agent_pos[2], agent_pos[0], grid_resolution=map_resolution, sim=env.sim)
        print(f"Map origin: {env.sim.pathfinder.get_bounds()}")
        print(f"gird x:{grid_x}, grid_y:{grid_y}")
        topdown_with_agent = maps.draw_agent(
            topdown_map_color.copy(),
            (grid_x, grid_y),  # Attention to the x,y order
            agent_rotation=yaw,
            agent_radius_px=10,
        )

        print(f"shape of observation:{len(observations['pointgoal_with_gps_compass'])}")
        birdseye_view = maps.pointnav_draw_target_birdseye_view(
            agent_position=agent_pos,
            agent_heading=yaw,
            goal_position=observations['pointgoal_with_gps_compass'][0:3],
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
