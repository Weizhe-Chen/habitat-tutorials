# Habitat Action Introduction

Action is the abstraction that agent can execute in the environment — such as moving forward, turning left, or stopping. In Habitat-Lab, an action is a command you give the agent during `env.step(action_name)`. The action is created, registered, and refered to in a config file(typically in `task/xxx.yaml`)
> Unlike traditional robotics config, `action` in habitat is connected to the task, not directly to the agent. This is because different tasks may require different action spaces, action semantics, and goal conditions, even for the same agent and scene

## Action Creation and Use Pipeline

1. Implement Action: An action used in navigation is a class inherited from `SimulatorTaskAction`, which must implement `step()` method. Typically we call simulator to set the pose of the robot:
    ```python
    def _strafe_body(
        sim,
        move_amount: float,
        strafe_angle_deg: float,
        noise_amount: float,
    ):
        # Get the state of the agent
        agent_state = sim.get_agent_state()
        # Convert from np.quaternion (quaternion.quaternion) to mn.Quaternion
        normalized_quaternion = agent_state.rotation
        agent_mn_quat = mn.Quaternion(
            normalized_quaternion.imag, normalized_quaternion.real
        )
        forward = agent_mn_quat.transform_vector(-mn.Vector3.z_axis())
        strafe_angle = np.random.uniform(
            (1 - noise_amount) * strafe_angle_deg,
            (1 + noise_amount) * strafe_angle_deg,
        )
        strafe_angle = mn.Deg(strafe_angle)
        rotation = mn.Quaternion.rotation(strafe_angle, mn.Vector3.y_axis())
        move_amount = np.random.uniform(
            (1 - noise_amount) * move_amount, (1 + noise_amount) * move_amount
        )
        delta_position = rotation.transform_vector(forward) * move_amount
        final_position = sim.pathfinder.try_step(  # type: ignore
            agent_state.position, agent_state.position + delta_position
        )
        sim.set_agent_state(
            final_position,
            [*rotation.vector, rotation.scalar],
            reset_sensors=False,
        )
    @habitat.registry.register_task_action
    class StrafeLeft(SimulatorTaskAction):
        def __init__(self, *args, config, sim, **kwargs):
            super().__init__(*args, config=config, sim=sim, **kwargs)
            self._sim = sim
            self._move_amount = config.move_amount
            self._noise_amount = config.noise_amount

        def _get_uuid(self, *args, **kwargs) -> str:
            return "strafe_left"

        def step(self, *args, **kwargs):
            print(
                f"Calling {self._get_uuid()} d={self._move_amount}m noise={self._noise_amount}"
            )
            # This is where the code for the new action goes. Here we use a
            # helper method but you could directly modify the simulation here.
            _strafe_body(self._sim, self._move_amount, 90, self._noise_amount)
    ```
    The decorator register the action we defined so that it can be found by thb config.

2. Create a structured config pointing to our action
    ```python
    from habitat.config.default_structured_configs import ActionConfig
    @dataclass
    class StrafeActionConfig(ActionConfig):
        type: str = "StrafeLeft"  # MUST match the registered action
        move_amount: float = 0.25
        noise_amount: float = 0.0
    ```
3. Store it to ConfigStore
    ```python
    from hydra.core.config_store import ConfigStore

    cs = ConfigStore.instance()
    cs.store(group="habitat/task/actions", name="strafe_action", node=StrafeActionConfig)
    ```
    > You can also use it directly in code, just like any other config.
4. Refer it in yaml
    ```yaml
    defaults:
    - habitat/task/actions@STRAFE_LEFT: strafe_action
    ```
5. Use it to step:
    ```python
    # First Load the yaml
    obs = env.step("STRAFE_LEFT")
    ```

## Default Actions for Navigation

There are 4 default actions defined in Habitat Sim and they are registered and stored in Habitat Lab, you can directly use them in your yaml and code:
```yaml
defaults:
  - task_config_base
  - actions:
    - stop
    - move_forward
    - turn_left
    - turn_right
```
```python
env.step('stop')
```