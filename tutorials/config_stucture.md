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
