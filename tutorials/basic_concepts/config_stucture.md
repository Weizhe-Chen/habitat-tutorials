# Habitat Config Introduction

Habitat V0.3.3 uses Hydra as the config framework. For official config system introduction, see [here](https://github.com/facebookresearch/habitat-lab/tree/main/habitat-lab/habitat/config).

## Key Concepts
- **Input Config**: Input config is the config that direcly read by our scripts, say, `config/benchmark/nav/pointnav/pointnav_habitat_test.yaml`.
- **Output Config**: After the input config read by our scripts, the subconfig composited in the input config, and new configs given at running time will be merged by Hydra. Finally we will get an output config, where only basic types(int, str, etc) exists.
- **Structured Config**: Structured Config provides a way to explicitly define some key-value pairs with the type. e.g.
    ```python
    @dataclass
    class MyConfig:
        learning_rate: float = 0.001
        batch_size: int = 32
        use_gpu: bool = True
    ```
    you can find basic structured config used in habitat [here](https://github.com/facebookresearch/habitat-lab/blob/main/habitat-lab/habitat/config/default_structured_configs.py).
- **Config Group**: Config Group is a folder-like structure which allows you to put the config with the same function into a group. The config lives in the same config group and be easily changed modularly.
- **ConfigStore**: ConfigStore is a singleton which allows you to register you structured config and use them in other yamls and scripts. By using ConfigStore, you can split the defintion and use of a config.
- **Config Search Path**: If you don't use ConfigStore to register the config(Put a yaml directly there like our `config` folder), Hydra uses config search path to recognize their groups, name and nodes. e.g. in our `config` folder:
    ```sh
    .
    ├── benchmark
    │   ├── ...
    └── habitat
        ├── dataset
        │   ├── eqa
        │   ├── imagenav
        │   ├── instance_imagenav
        │   ├── objectnav
        │   ├── pointnav
        │   ├── ...
    ```
    A yaml file can still refer other configs like this(path from the root as group, filename as name):
    ```yaml
    defaults:
        - pointnav_base
        - /habitat/dataset/pointnav: habitat_test
        - _self_
    ```
    > Habitat adds `habitat/config` to Config Search Path using [`HabitatConfigPlugin`](https://github.com/facebookresearch/habitat-lab/blob/main/habitat-lab/habitat/config/default_structured_configs.py).
- **Config Merge**: All config files or structured config referred to in the input config will be merged into one output config. The basic merging rule can be found below.
- **Config Injection**: Config injection is used when you want to add a config to a node in current config rather than directly override it. e.g.
    ```yaml
    /habitat/simulator/sensor_setups@habitat.simulator.agents.main_agent: rgbds_agent
    ```
    This means:
    ```yaml
    habitat:
        simulator:
            agents:
                main_agent:
                    Contents from rgbds_agent
    ```
    This will create the node `main_agent` if there is none, and add new contents if some contents already under agents. 


## Config Creation Pipeline
1. Define a sturctured config in script:
    ```python
    from dataclasses import dataclass
    @dataclass
    class MyConfig:
        learning_rate: float = 0.001
        batch_size: int = 32
        use_gpu: bool = True
    ```
2. Register it in ConfigStore
    ```python
    from hydra.core.config_store import ConfigStore
    cs = ConfigStore.instance()
    cs.store(group="basic_config", name="my_config", node=MyConfig)
    ```
3. Refer this in other yaml
    ```yaml
    # config.yaml
    defaults:
        - basic_config: my_config
    ```
    > You use name rather than node to refer.
4. Use this yaml in your script
    ```python
        import hydra
        from omegaconf import OmegaConf

        @hydra.main(version_base=None, config_name="config")
        def main(cfg: MyConfig):
            print(OmegaConf.to_yaml(cfg))

        if __name__ == "__main__":
            main()
    ```
    > Here we use a Hydra way to use this yaml(Decorate the main function), in habitat you typically needn't do this since habitat uses ComposeAPI instead of decorator and you only need to call Habitat API `get_config`.

## Habitat Config Structure

### Benchmark

In Habitat, the `config/benchmark/` directory contains predefined task configurations used for running standardized evaluations or benchmarking models on common datasets and tasks. The config file is typically named by task+dataset(say `pointnav_mp3d.yaml`)

### Habitat

There are 3 subfolders in habitat: `dataset`, `simulator`, `task`.

- `dataset`: Each yaml in `dataset` folder will by default use 
    ```yaml
    defaults:
    - /habitat/dataset: dataset_config_schema
    - _self_
    ```
    which is registered in [default_strucutured_config](https://github.com/facebookresearch/habitat-lab/blob/main/habitat-lab/habitat/config/CONFIG_KEYS.md)
    and then override `type`, `split`, `data_path`, etc.

- `simulator`: This folder mainly config the agent using default structured config, we can use Config Injection to add sensors and agents.
- `task`: yaml in `task` folder load `task_config_base` by default, which is a complicated config(see [TaskConfig](https://github.com/facebookresearch/habitat-lab/blob/main/habitat-lab/habitat/config/default_structured_configs.py#L1373)). The important nodes to override are `lab_sensors`, `actions` and `measures`.
    > `lab_sensors` is different from agent sensors, they provide task level perception, like `habitat.task.lab_sensors.compass_sensor` for angle difference in radians between the current rotation of the robot and the start rotation of the robot along the vertical axis, for more details, see [here](https://github.com/facebookresearch/habitat-lab/blob/main/habitat-lab/habitat/config/CONFIG_KEYS.md).

## Config Merging Rule
Habitat use tree structure to manage configs. They are merged following the rules below:
1. If there is a `@package` in yaml file, it will be merged to the target defined by `@package`, no matter where the yaml file is and which group it belongs to.
e.g.(`habitat_test.yaml`)
    ```yaml
    # @package habitat.dataset
    defaults:
    - /habitat/dataset: dataset_config_schema
    - _self_

    type: PointNav-v1
    split: train
    data_path: data/datasets/pointnav/habitat-test-scenes/v1/{split}/{split}.json.gz
    ```
    > A special case is `@package _global_`, which means merge all contents to the root level.
2. If there is no `@package`, the yaml will be merged to the key defined by its group, like the 
    ```yaml
    - /habitat/dataset: dataset_config_schema
    ```
    in above `habitat_test.yaml`. It will be merged to
    ```yaml
    habitat:
        dataset:
    ```
3. If there is no `@package`, and no group is given, the yaml will be merged to the called level. e.g.
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
    ```

## Modify Config in script

1. Get the config file
    ```python
    config = habitat.get_config(
            config_path=os.path.join(
                dir_path,
                "./config/benchmark/nav/pointnav/pointnav_habitat_test.yaml",
            )
        )
    ```
2. By default, this config is frozen, and you can not modify it, you can check this:
    ```python
    print(OmegaConf.is_readonly(config.habitat.simulator)) # Or any other key you want
    ```
3. To defrost the config file for modifying, you should use:
    ```python
    with habitat.config.read_write(config):
        print(OmegaConf.is_readonly(config.habitat.simulator)) # Now it will be False
    ```
4. Modify the config
    ```python
    # The first way is to use update() method to update
    with config.habitat.simulator.agents.main_agent.sim_sensors.update(
        {
                    "new_rgb": # Contents you want to set
        }
    )
    # The second way is to modify the config directly
    top_rgb_cfg = # Contents you want to set
    config.habitat.simulator.agents.main_agent.sim_sensors.top_rgb_sensor = top_rgb_cfg # Pay attention you need the new key name here
    ```

The contents you want to set can also be set via two ways: structured config or not. When you use structured config, you will enjoy the type checking, autocompletion, etc. The shortcome is that you may not always find a suitable defined structured config and you may want to define one.(e.g. if you use `HabitatSimRGBSensor` to create sensor, you will fail due to the lack of `uuid` key in this structured config).
```python
# We use HeadRGBSensorConfig so that uuid can be set
config.habitat.simulator.agents.main_agent.sim_sensors.update(
            {
                "new_rgb": HeadRGBSensorConfig(
                width=256,
                height=256,
                position=[0.0, 1.7, 0.0],
                sensor_subtype="PINHOLE",
                uuid="new_rgb",
                type="HabitatSimRGBSensor"  # REQUIRED!
                )
            }
```

The other way is to use plain dict, this can be done if your plain dict contains all information needed:
```python
with habitat.config.read_write(config):
        config.habitat.simulator.agents.main_agent.sim_sensors.top_rgb_sensor = {
        "type": "HabitatSimRGBSensor",
        "width": 256,
        "height": 256,
        "position": [0.0, 1.7, 0.0],
        "sensor_subtype": "PINHOLE",
        "uuid": "new_rgb",
    }          
```

You can check the full code in `add_sensor_update.py`, `add_sensor_plain_dict.py` and `add_sensor_structured.py` respectively.