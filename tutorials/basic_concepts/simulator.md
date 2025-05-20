# Simulator Introduction

Simulator in Habitat-Lab defines how the `Habitat-Sim` engine behaves. In config file, its main children nodes are agent definitions and sensor definitions. 

## Config

A minial config is like this:
```yaml
habitat:
  simulator:
    agents:
      main_agent:
        sim_sensors:
          rgb_sensor:
            width: 256
            height: 256
          depth_sensor:
            width: 256
            height: 256
```
Only agents need to be overridden since the basic config such as simulator_type, seed in defined in default `SimulatorConfig` which is contained in `habitat_config_base`.