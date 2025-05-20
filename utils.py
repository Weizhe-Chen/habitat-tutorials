import git
import os
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
from habitat_sim.utils.common import d3_40_colors_rgb


os.environ["MAGNUM_LOG"] = "quiet"
os.environ["HABITAT_SIM_LOG"] = "error"
os.environ["GLOG_minloglevel"] = "2"

def get_data_path():
    repo = git.Repo(".", search_parent_directories=True)
    git_root = repo.working_tree_dir
    data_path = os.path.join(git_root, "data")
    return data_path

def get_output_path():
    repo = git.Repo(".", search_parent_directories=True)
    git_root = repo.working_tree_dir
    output_path = os.path.join(git_root, "output")
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    return output_path

def display_sample(rgb_obs, semantic_obs=np.array([]), depth_obs=np.array([]), figsize=(24, 8)):
    rgb_img = Image.fromarray(rgb_obs, mode="RGBA")
    arr = [rgb_img]
    titles = ["rgb"]
    if semantic_obs.size != 0:
        semantic_img = Image.new("P", (semantic_obs.shape[1], semantic_obs.shape[0]))
        semantic_img.putpalette(d3_40_colors_rgb.flatten())
        semantic_img.putdata((semantic_obs.flatten() % 40).astype(np.uint8))
        semantic_img = semantic_img.convert("RGBA")
        arr.append(semantic_img)
        titles.append("semantic")

    if depth_obs.size != 0:
        depth_img = Image.fromarray((depth_obs / 10 * 255).astype(np.uint8), mode="L")
        arr.append(depth_img)
        titles.append("depth")

    plt.figure(figsize=figsize)
    for i, data in enumerate(arr):
        ax = plt.subplot(1, len(arr), i + 1)
        ax.axis("off")
        ax.set_title(titles[i])
        plt.imshow(data)
    plt.show()

def display_map(topdown_map, key_points=None):
    plt.figure(figsize=(12, 8))
    ax = plt.subplot(1, 1, 1)
    ax.axis("off")
    plt.imshow(topdown_map)
    # plot points on map
    if key_points is not None:
        for point in key_points:
            plt.plot(point[0], point[1], marker="o", markersize=10, alpha=0.8)
    plt.show()

def convert_points_to_topdown(pathfinder, points, meters_per_pixel):
    points_topdown = []
    bounds = pathfinder.get_bounds()
    for point in points:
        # convert 3D x,z to topdown x,y
        px = (point[0] - bounds[0][0]) / meters_per_pixel
        py = (point[2] - bounds[0][2]) / meters_per_pixel
        points_topdown.append(np.array([px, py]))
    return points_topdown
