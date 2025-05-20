# Task Introduction
A Task in Habitat defines:

- What the agent is supposed to do

- How it is evaluated

- What actions it can take

- What sensors it uses to perceive the environment

- How rewards, success, and termination are defined

For example: `habitat/task/pointnav.yaml`
```yaml
defaults:
  - task_config_base
  - actions:
    - stop
    - move_forward
    - turn_left
    - turn_right
  - measurements:
    - distance_to_goal
    - success
    - spl
    - distance_to_goal_reward
  - lab_sensors:
    - pointgoal_with_gps_compass_sensor
  - _self_

type: Nav-v0
end_on_success: True
reward_measure: "distance_to_goal_reward"
success_measure: "spl"
goal_sensor_uuid: pointgoal_with_gps_compass
```

## How to use Task
### Self-Defined Task
Task is like action and datsets, you can first register them:
```python
@registry.register_task(name="Nav-v0")
class NavigationTask(EmbodiedTask):
    ...
```
Then use it in yaml to override the default config:
```yaml
defaults:
  - task_config_base
type: Nav-v0
```
or create a config:
```python
from habitat.config import Config
from dataclasses import dataclass
from habitat.config.default_structured_configs import TaskConfig 
@dataclass
class MyTaskConfig(TaskConfig):
    type: str = "Nav-v0"
    success_measure: str = "spl"
    reward_measure: str = "distance_to_goal_reward"
    end_on_success: bool = True
    measurements: list = None
    actions: list = None
from hydra.core.config_store import ConfigStore
cs = ConfigStore.instance()
cs.store(group="habitat/task/", name="mytask", node=MyTaskConfig)
```
The detailed way to define a task can ref [here](https://github.com/facebookresearch/habitat-lab/blob/5e0d63838cf3f6c7008c9eed00610d556c46c1e3/habitat-lab/habitat/tasks/nav/nav.py#L4).

### Pre-Defined Task
Habitat already defined many tasks [here](https://github.com/facebookresearch/habitat-lab/tree/main/habitat-lab/habitat/tasks). Just check their information(especailly type), and use them in yaml:
```yaml
defaults:
  - task_config_base
  - actions:
    - stop
    - move_forward
    - turn_left
    - turn_right
  - measurements:
    - distance_to_goal
    - success
    - spl
    - distance_to_goal_reward
  - lab_sensors:
    - pointgoal_with_gps_compass_sensor
  - _self_

type: Nav-v0
end_on_success: True
reward_measure: "distance_to_goal_reward"
success_measure: "spl"
goal_sensor_uuid: pointgoal_with_gps_compass
```
Task `Nav-v0` will get actions, measurements, lab_sensors, etc from the config.

## Key Attributes for Navigation
- `end_on_success`: If True: once the success condition is satisfied (e.g., the agent reaches the goal), the episode automatically ends. If False: the episode continues until max steps are reached — even after success.
- `distance_to_goal_reward`: Reward is given when the agent gets closer to the goal. 
- `spl`: Success weighted by Path Length.

These are all handled in task definition(Nav-v0 here).

