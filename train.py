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

if __name__ == "__main__":
    # path datasets
    trains_path = './dataset/trains'
    pkls = [ f.path for f in os.scandir(trains_path) if f.name.endswith('.pkl') ]

    
    for pkl in pkls:
        try:
            with open(pkl, 'rb') as f:
                data = pickle.load(f)
                obstacles = data.get("obstacles")
                runs = data.get("runs")
                
                # define MAP
                custom_map = Map(obstacles, start, end)
                for run in runs:
                    start = run.get("start")
                    end = run.get("end")
                    env = PathPlanningWithLidar(custom_map)
                    env.path = run.get("path")
                
                    done = False
                    while not done:
                        done, obs = env.step()
                        env.render()
                    env.close()
        except Exception as e:
            print(f"load {pkl} error: {e}")