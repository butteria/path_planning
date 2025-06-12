#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 12:17:33
# Description:

# load my env
from plan_planning_env import Map, PathPlanningWithLidar, RRT, WaveFront

import numpy as np
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
import pickle
# load obstacles to custom_map

filename = "test.pkl"


if __name__ == "__main__":
    try:
        with open("./obstacles/poly/"+filename, 'rb') as f:
            map_data = pickle.load(f)
    except Exception as e:
        print(f"Error loading map: {e}")
    # print(obstacles)

    vertices = map_data.get("obstacles", [])
    start = map_data.get("start", None)
    end = map_data.get("end", None)
    custom_map = Map(obs_vertices=vertices, start=start, end=end)
    env = PathPlanningWithLidar(custom_map)

    # path solution method
    # rrt = RRT(custom_map)
    wf =WaveFront(custom_map)
    env.path = wf.plan()
    env.render()
    # env.render()
