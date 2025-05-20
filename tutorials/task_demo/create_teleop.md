# Create Env and Teleop

This tutorial aims to provide a basic framework for navigation using keyboard input.

## Create Environment

Habitat Lab use a high level abstraction like gym. You can use a config file to create an environment. Bascially this config file should contain `dataset`, `task`, and `simulator`.

```python
import habitat
env = habitat.Env(
        config=habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
    )
```

This `env` object contains all information needed for simulation.
- Full config: `env._config` is the resolved config
- Action and Observation Space: `env.action_space` and `env.observation_space`

## Step
Using `env.action_space` you can see all the actions used in this sim, directly use the name to move the robot:
```python
observations = env.step('move_forward')
```

## Get Observation

You can find all default observation types [here](https://github.com/facebookresearch/habitat-lab/blob/5e0d63838cf3f6c7008c9eed00610d556c46c1e3/habitat-lab/habitat/sims/habitat_simulator/habitat_simulator.py#L107), just check the keys in `env.observation_space`.

## Full Code:
```python
import habitat
import cv2
from omegaconf import OmegaConf
import os

FORWARD_KEY="w"
LEFT_KEY="a"
RIGHT_KEY="d"
FINISH="f"


def transform_rgb_bgr(image):
    return image[:, :, [2, 1, 0]]


def example():
    output_path = "./output/resolve_conf.yaml"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    env = habitat.Env(
        config=habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
    )
    
    print("Environment creation successful")
    print(f"Env Action Space:{env.action_space}")
    print(f"Env Observation Space:{env.observation_space}")

    # Save the resolved config
    with open(output_path, "w") as f:
        OmegaConf.save(config=env._config, f=f)
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
        cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))

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