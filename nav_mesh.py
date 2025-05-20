
import math
import habitat_sim
import magnum as mn
import numpy as np
from habitat_sim.utils import common as utils
from habitat.utils.visualizations import maps
from matplotlib import pyplot as plt
from depth_semantic_sensors import *
from utils import *

meters_per_pixel = 0.1

print("NavMesh Area = " + str(sim.pathfinder.navigable_area))
print("NavMesh Bounds = " + str(sim.pathfinder.get_bounds()))

# Make sure the pathfinder is loaded
assert sim.pathfinder.is_loaded, "Pathfinder not initialized, aborting."

# Method 1: Get the topdown map from Habitat-Sim
height = sim.pathfinder.get_bounds()[0][1]
sim_topdown_map = sim.pathfinder.get_topdown_view(meters_per_pixel, height)

# Method 2: Get the topdown map from Habitat-Lab
hablab_topdown_map = maps.get_topdown_map(sim.pathfinder, height, meters_per_pixel=meters_per_pixel)
recolor_map = np.array([[255, 255, 255], [128, 128, 128], [0, 0, 0]], dtype=np.uint8)
hablab_topdown_map = recolor_map[hablab_topdown_map]
display_map(sim_topdown_map)
display_map(hablab_topdown_map)

# A random point on the NavMesh can be queried with *get_random_navigable_point*.
sim.pathfinder.seed(1)
nav_point = sim.pathfinder.get_random_navigable_point()
print("Random navigable point : " + str(nav_point))
print("Is point navigable? " + str(sim.pathfinder.is_navigable(nav_point)))

# Island radius is the radius of the minimum containing circle (with vertex centroid origin) for the isolated navigable island of a point.
print("Nav island radius : " + str(sim.pathfinder.island_radius(nav_point)))

# Find the closest obstacle within a radius
max_search_radius = 2.0
print("Distance to obstacle: " + str(sim.pathfinder.distance_to_closest_obstacle(nav_point, max_search_radius)))
hit_record = sim.pathfinder.closest_obstacle_surface_point(nav_point, max_search_radius)
print("Closest obstacle HitRecord:")
print(" point: " + str(hit_record.hit_pos))
print(" normal: " + str(hit_record.hit_normal))
print(" distance: " + str(hit_record.hit_dist))

vis_points = [nav_point]
# HitRecord will have infinite distance if no valid point was found:
if math.isinf(hit_record.hit_dist):
    print("No obstacle found within search radius.")
else:
    # Points near the boundary or above the NavMesh can be snapped onto it.
    perturbed_point = hit_record.hit_pos - hit_record.hit_normal * 0.2
    print("Perturbed point : " + str(perturbed_point))
    print("Is point navigable? " + str(sim.pathfinder.is_navigable(perturbed_point)))
    snapped_point = sim.pathfinder.snap_point(perturbed_point)
    print("Snapped point : " + str(snapped_point))
    print("Is point navigable? " + str(sim.pathfinder.is_navigable(snapped_point)))
    vis_points.append(snapped_point)

# Generates a topdown visualization of the NavMesh with sampled points overlaid.
xy_vis_points = convert_points_to_topdown(sim.pathfinder, vis_points, meters_per_pixel)
# use the y coordinate of the sampled nav_point for the map height slice
top_down_map = maps.get_topdown_map(sim.pathfinder, height=nav_point[1], meters_per_pixel=meters_per_pixel)
recolor_map = np.array([[255, 255, 255], [128, 128, 128], [0, 0, 0]], dtype=np.uint8)
top_down_map = recolor_map[top_down_map]
print("Display the map with key_point overlay:")
display_map(top_down_map, key_points=xy_vis_points)

# Sample valid points on the NavMesh for agent spawn location and pathfinding goal
sim.pathfinder.seed(4)
sample1 = sim.pathfinder.get_random_navigable_point()
sample2 = sim.pathfinder.get_random_navigable_point()
# Use ShortestPath module to compute path between samples.
path = habitat_sim.ShortestPath()
path.requested_start = sample1
path.requested_end = sample2
found_path = sim.pathfinder.find_path(path)
geodesic_distance = path.geodesic_distance
path_points = path.points
print("found_path : " + str(found_path))
print("geodesic_distance : " + str(geodesic_distance))
print("path_points : " + str(path_points))

# Display trajectory on a topdown map of ground floor
if not found_path:
    print("No path found!")

meters_per_pixel = 0.025
height = sim.scene_aabb.y().min
top_down_map = recolor_map[maps.get_topdown_map(sim.pathfinder, height, meters_per_pixel=meters_per_pixel)]
grid_dimensions = (top_down_map.shape[0], top_down_map.shape[1])
# convert world trajectory points to maps module grid points
trajectory = [
    maps.to_grid(
        path_point[2],
        path_point[0],
        grid_dimensions,
        pathfinder=sim.pathfinder,
    )
    for path_point in path_points
]
grid_tangent = mn.Vector2(trajectory[1][1] - trajectory[0][1], trajectory[1][0] - trajectory[0][0])
path_initial_tangent = grid_tangent / grid_tangent.length()
initial_angle = math.atan2(path_initial_tangent[0], path_initial_tangent[1])
# draw the agent and trajectory on the map
maps.draw_path(top_down_map, trajectory)
maps.draw_agent(top_down_map, trajectory[0], initial_angle, agent_radius_px=8)
print("Display the map with agent and path overlay:")
display_map(top_down_map)

# Place agent and render images at trajectory points (if found).
print("Rendering observations at path points:")
tangent = path_points[1] - path_points[0]
agent_state = habitat_sim.AgentState()
for i, point in enumerate(path_points):
    if i == len(path_points) - 1:
        break
    tangent = path_points[i + 1] - point
    agent_state.position = point
    tangent_orientation_matrix = mn.Matrix4.look_at(point, point + tangent, np.array([0, 1.0, 0]))
    tangent_orientation_q = mn.Quaternion.from_matrix(tangent_orientation_matrix.rotation())
    agent_state.rotation = utils.quat_from_magnum(tangent_orientation_q)
    agent.set_state(agent_state)

    observations = sim.get_sensor_observations()
    rgb = observations["color_sensor"]
    semantic = observations["semantic_sensor"]
    depth = observations["depth_sensor"]
    print(f"Rendering observation at point {point}")
    display_sample(rgb, semantic, depth)