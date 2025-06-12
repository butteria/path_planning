#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import glob
import pickle
import time
from plan_planning_env import Map, WaveFront

if __name__ == "__main__":
    
    poly_path = './obstacles/poly'
    path_path = './dataset/path'
    if not os.path.exists(path_path):
        os.makedirs(path_path)

    if not os.path.exists(poly_path):
        print("no obstacles folder found, creating one...")
        exit -1
    pkl_files = [f.path for f in os.scandir(poly_path) if f.name.endswith('.pkl') and f.is_file()]
    
    if not pkl_files:
        print("no pkl files found in the obstacles folder.")
        exit -1

    for pkl_file in pkl_files:
        try:
            with open(pkl_file, 'rb') as f:
                map_data = pickle.load(f)
        except Exception as e:
            print(f"Error loading map: {e}")
        
        vertices = map_data.get("obstacles", [])
        start = map_data.get("start", None)
        end = map_data.get("end", None)
        custom_map = Map(obs_vertices=vertices, start=start, end=end)
        wf = WaveFront(custom_map)
        
        # plan the path
        print(f"trying to plan {pkl_file}...")
        start_time = time.time()
        path = wf.plan()
        end_time = time.time()

        result = {
            "path": path,
            "elapsed_time": end_time - start_time
        }
        base_name = os.path.splitext(os.path.basename(pkl_file))[0]
        out_file = os.path.join(path_path, base_name + ".path")
        with open(out_file, "wb") as f:
            pickle.dump(result, f)