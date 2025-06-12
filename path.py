#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import glob
import pickle
import time
from plan_planning_env import Map, WaveFront

if __name__ == "__main__":
   trains_path = './dataset/trains'
   pkl_files = [f.path for f in os.scandir(trains_path) if f.name.endswith('.pkl') and f.is_file()]
   for pkl_file in pkl_files:
        with open(pkl_file, 'rb') as f:
            trains = pickle.load(f)
        obstacles = trains.get("obstacles", [])
        runs = trains.get("runs", None)


        # loop through each start-end pair
        for i, run in enumerate(runs):
            if run.get("path") is None:
                start = run.get("start", None)
                end = run.get("end", None)
                custom_map = Map(obs_vertices=obstacles, start=start, end=end)
                
                wf = WaveFront(custom_map)
                start_time = time.time()
                print(f"Planning path for start: {start}, end: {end}")
                path = wf.plan()
                print(path)
                end_time = time.time()

                if path:
                    trains["runs"][i]["path"] = path
                    trains["runs"][i]["time"] = end_time - start_time

        with open(pkl_file, 'wb') as f:
            pickle.dump(trains, f)