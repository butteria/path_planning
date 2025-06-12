#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 12:17:33
# Description:

# load my env
from plan_planning_env import Map, PathPlanningWithLidar, RRT, WaveFront

import numpy as np
import os
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
import pickle
# load obstacles to custom_map

filename = "test.pkl"


if __name__ == "__main__":
    # path datasets
    path_path = './dataset/path'
    poly_path = './obstacles/poly'
    path_files = [f.path for f in os.scandir(path_path) if f.name.endswith('.path') and f.is_file()]
    pkl_files = [f.path for f in os.scandir(poly_path) if f.name.endswith('.pkl') and f.is_file()]

    for pkl_file, path_file in zip(pkl_files, path_files):
        try:
            with open(pkl_file, 'rb') as f:
                map_data = pickle.load(f)
        except Exception as e:
            print(f"Error loading map: {e}")
        try:
            with open(path_file, 'rb') as f:
                path_data = pickle.load(f)
        except Exception as e:
            print(f"Error loading path: {e}")


        vertices = map_data.get("obstacles", [])
        start = map_data.get("start", None)
        end = map_data.get("end", None)
        custom_map = Map(obs_vertices=vertices, start=start, end=end)
        env = PathPlanningWithLidar(custom_map)
        env.path = path_data.get("path", None)
        done = False
        while not done:
            done, obs = env.step()
            env.render()
        

        env.close()
        break