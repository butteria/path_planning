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
import random
# load obstacles to custom_map

filename = "test.pkl"


if __name__ == "__main__":
    # path datasets
    trains_path = './dataset/trains'
    pkl_files = [f.path for f in os.scandir(trains_path) if f.name.endswith('.pkl') and f.is_file()]

    for pkl_file in pkl_files:
        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)
        

        obstacles = data.get("obstacles", [])
        runs = data.get("runs", None)
        run = random.choice(runs) if runs else None

        start = run.get("start", None)
        end = run.get("end", None)
        custom_map = Map(obs_vertices=obstacles, start=start, end=end)
        env = PathPlanningWithLidar(custom_map)
        env.path = run.get("path", None)
        print(env.path)
        done = False
        while not done:
            done, obs = env.step()
            env.render()
        

        env.close()