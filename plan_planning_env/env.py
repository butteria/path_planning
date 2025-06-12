#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 12:11:36
# Description:
import gym
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString, Point
from shapely.plotting import plot_polygon

plt.rcParams['toolbar'] = 'None'
plt.rcParams['xtick.bottom'] = False
plt.rcParams['xtick.labelbottom'] = False
plt.rcParams['ytick.left'] = False
plt.rcParams['ytick.labelleft'] = False
plt.rcParams['figure.autolayout'] = True

class Map:
    def __init__(self,
                 obs_vertices,
                 map_size = [ [-10.0, -10.0], [10.0, 10.0] ],
                 start = [-2, -2],
                 end = [8.0, 8.0]):

        self.size = map_size
        self.start = start
        self.end = end

        # convert vertices to polygons
        self.obstacles = []
        for obs_vertice in obs_vertices:
            self.obstacles.append(Polygon(obs_vertice))

class Lidar():
    def __init__(self, Map, max_range=20.0, scan_angle=128.0, num_angle=128):
        """ Args:
                max_range (float): 最大扫描距离(m).
                scan_angle (float): 最大扫描角度(deg).
                num_angle (int): 扫描角度个数.
        """
        self.max_range = float(max_range)
        self.scan_angle = float(scan_angle)
        self.num_angle = int(num_angle)
        self.x, self.y = Map.start
        # 偏航角初始为正北方
        self.yaw = np.deg2rad(90.0)

        self.obstacles = Map.obstacles
        self.__ray_angles = np.deg2rad(np.linspace(-self.scan_angle/2, self.scan_angle/2, self.num_angle))


    def scan(self):
        """ Args:
                self.x (float): x坐标(m).
                self.y (float): y坐标(m).
                self.yaw (float): 偏航角(rad).

        """
        # 激光与障碍物交点
        scan_points = []
        scan_distances = []
        ray_lines = [
            LineString([
                (self.x, self.y),
                (self.x + self.max_range * np.cos(self.yaw + self.__ray_angles[0]),
                  self.y + self.max_range * np.sin(self.yaw + self.__ray_angles[0]))
            ]),
             LineString([
                (self.x, self.y),
                (self.x + self.max_range * np.cos(self.yaw + self.__ray_angles[-1]),
                  self.y + self.max_range * np.sin(self.yaw + self.__ray_angles[-1]))
            ])
        ]

        # 碰撞
        for obstacle in self.obstacles:
            if obstacle.contains(Point(self.x,self.y)):
                return scan_distances, scan_points, ray_lines

        # 雷达测距
        for i, angle in enumerate(self.__ray_angles):
            line = LineString([
                (self.x, self.y),
                (self.x + self.max_range * np.cos(self.yaw + angle), self.y + self.max_range * np.sin(self.yaw + angle))
            ])

            point, distance = self.__compute_intersection(line)
            if point is not None:
                scan_distances.append(distance)
                scan_points.append(point)

        return scan_distances, scan_points, ray_lines

    # 计算雷达射线和障碍物的交点和距离
    def __compute_intersection(self, ray_line: LineString):
        point = None
        distance = self.max_range

        # TODO: O(n)
        for obstacle in self.obstacles:
            intersections = obstacle.intersection(ray_line)
            if intersections.is_empty:
                continue
            if intersections.geom_type in {'MultiPoint', 'MultiLineString', 'GeometryCollection'}:
                multi_geom = list(intersections.geoms)
            else:
                multi_geom = [intersections]

            for single_geom in multi_geom:
                for p in single_geom.coords:
                    d = np.linalg.norm(np.array(p) - ray_line.coords[0])
                    if d < distance:
                        distance = d
                        point = list(p)

        return point, distance

# gym env
class PathPlanningWithLidar(gym.Env):

    # 定义render模式
    metadata = {'render.modes': ['human']}

    def __init__(self, MAP):
        super(PathPlanningWithLidar, self).__init__()

        self.map = MAP
        self.lidar = Lidar(self.map)

        # used for render function
        self.fig = None
        
        self.path = None
        self.__path_index = -1

    def reset(self):
        self.lidar.x, self.lidar.y = self.map.start # reset lidar position
        self.lidar.yaw = np.deg2rad(90.0)  # reset lidar yaw to north


    def step(self, action=1):
        # """ Args:
        #         action (int) 1: forward, -1: backward
        # """
        self.__path_index += action
        if self.__path_index == 0:
            return False, (self.lidar.x, self.lidar.y, self.lidar.scan()[0])
        
        if not self.path or self.__path_index < 0 or self.__path_index >= len(self.path):
            return True, (self.lidar.x, self.lidar.y, self.lidar.scan()[0])  # done_state, observation
        self.lidar.x, self.lidar.y = self.path[self.__path_index]
        self.lidar.yaw = np.arctan2(self.path[self.__path_index][1] - self.path[self.__path_index-1][1],
                                    self.path[self.__path_index][0] - self.path[self.__path_index-1][0])
        
        return False, (self.lidar.x, self.lidar.y, self.lidar.scan()[0])  # done_state, observation

    def render(self, mode='human'):
        if self.fig is None:
            plt.ion()
            # ax config
            self.fig, self.ax = plt.subplots(figsize=(10, 10))
            self.ax.set_title('Path Planning')

            self.ax.set_xlim(self.map.size[0][0], self.map.size[1][0])
            self.ax.set_ylim(self.map.size[0][1], self.map.size[1][1])
            self.car, = self.ax.plot([], [], 'ro', markersize=10)
            self.ray1, = self.ax.plot([], [], color='orange', linewidth=0.5, linestyle='--', label='Lidar Rays')
            self.ray2, = self.ax.plot([], [], color='orange', linewidth=0.5, linestyle='--', label='Lidar Rays')
            self.points = self.ax.scatter([], [], c='red', s=10, label='Lidar Hits')
            
            self.end = self.ax.plot(self.map.end[0], self.map.end[1], 'go', markersize=10, label='Goal')
            self.start = self.ax.plot(self.map.start[0], self.map.start[1], 'bo', markersize=10, label='Start')
            if hasattr(self, "path") and self.path is not None and len(self.path) > 1:
                path_arr = np.array(self.path)
                self.ax.plot(path_arr[:, 0], path_arr[:, 1], color='blue', linewidth=2, label='RRT Path')
            # draw obstacles
            for obstacle in self.map.obstacles:
                plot_polygon(obstacle, ax=self.ax, facecolor='lightblue', edgecolor='black', add_points=False)

        # show lidar points
        scan_distances, scan_points, ray_lines = self.lidar.scan()
        if scan_points:
            scan_points = np.array(scan_points)
            self.points.set_offsets(scan_points)
        # 画出雷达射线
        self.ray1.set_data(ray_lines[0].xy)
        self.ray2.set_data(ray_lines[1].xy)
        self.car.set_data(self.lidar.x, self.lidar.y)
        
        plt.pause(0.05)
        

    def close(self):
        if self.fig is not None:
            plt.ioff()
            plt.close(self.fig)
            self.fig = None