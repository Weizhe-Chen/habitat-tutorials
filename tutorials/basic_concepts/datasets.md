# Datasets Introduction

Datasets is the key part in Habitat Lab. It defines the scene, starting pose of robot and goals. It consists of scene datasets and episode datasets.

## Datasets Download

Habitat currently uses [these datasets](https://github.com/facebookresearch/habitat-lab/blob/main/DATASETS.md). Most of them can be downloaded directly from the link, but some may need additional application(MatterPort3D for example).

To make datasets loaded properly and easily found, you should follow the particular folder structure or use symlink. You can use habitat-sim download script for downloading [these datasets](https://github.com/facebookresearch/habitat-sim/blob/dfb388e29e5e1f25da4b576305e85bdc0be140b8/src_python/habitat_sim/utils/datasets_download.py#L341):
```sh
python -m habitat_sim.utils.datasets_download --uids habitat_test_scenes --data-path data/
```

## Scene Data

Scene files are the 3D environments (e.g., scanned apartments or synthetic rooms). e.g.
```sh
data/scene_datasets/mp3d/17DRP5sb8fy/17DRP5sb8fy.glb
data/scene_datasets/habitat-test-scenes/van-gogh-room.glb
```

These files can be shared across multiple datasets and tasks (e.g., PointNav, ObjectNav). Typically they are included in the episode files.

`.glb` files can be viewed using some 3D viewer software, you can also use online viewer for some small files.

## Episode Data

Episode data contain task-specific definitions, like where the agent starts and where the goal is, etc. They are stored in `.json.gz` files, e.g.
```sh
data/datasets/pointnav/mp3d/v1/train/17DRP5sb8fy.json.gz
data/datasets/pointnav/habitat-test-scenes/v1/train/van-gogh-room.json.gz
```
You can use python script to read the contents:
```python
import gzip
import json
import os, git
import pprint

repo = git.Repo(".", search_parent_directories=True)
dir_path = repo.working_tree_dir
data_path = os.path.join(dir_path, "data")
file_path=os.path.join(
            data_path,
            "datasets/pointnav/habitat-test-scenes/v1/train/train.json.gz",
        )
# Open and load the JSON data
with gzip.open(file_path, 'rt', encoding='utf-8') as f:
    data = json.load(f)

# Access the first episode
first_episode = data['episodes'][0]

# Pretty-print it
pprint.pprint(first_episode)
```
Here is an example for one episode:
```sh
    {
      "episode_id": "4999",
      "scene_id": "data/scene_datasets/habitat-test-scenes/van-gogh-room.glb",
      "start_position": [
        2.706711769104004,
        0.17669875919818878,
        -1.0063905715942383
      ],
      "start_rotation": [
        0,
        0.9819991318353665,
        0,
        -0.18888542843371092
      ],
      "info": {
        "geodesic_distance": 1.2928786277770996,
        "difficulty": "easy"
      },
      "goals": [
        {
          "position": [
            2.119081497192383,
            0.17669875919818878,
            0.006348460912704468
          ],
          "radius": null
        }
      ],
      "shortest_paths": null,
      "start_room": null
    }
```
where `geodesic_distance` is the shortest traversable distance from start to goal, constrained by the scene’s geometry, and `difficulty` is episode difficulty level (based on geodesic vs. Euclidean ratio). "easy" means it's fairly direct.

## Use Dataset 

Like actions and agents, a registered dataset can be refered to directly in config file.
```yaml
defaults:
  - /habitat/dataset: dataset_config_schema
  - _self_

type: PointNav-v1
split: train
data_path: data/datasets/pointnav/habitat-test-scenes/v1/{split}/{split}.json.gz
```
The field `type` here must match the type name when the dataset is registerd. You can find these registration in `habitat-lab/habitat-lab/habitat/datasets`, like `habitat-lab/habitat-lab/habitat/datasets/pointnav/pointnav_datasets.py`:
```py
@registry.register_dataset(name="PointNav-v1")
class PointNavDatasetV1(Dataset):
    r"""Class inherited from Dataset that loads Point Navigation dataset."""
    ...
```

## TODO: Make a new dataset