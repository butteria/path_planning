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

# 降低传感器搜索障碍物的时间复杂度!!
# 将地图划分为更小的区块（如 BlockMap 或 QuadTree），预先标记每个区块是否可通行。
class BlockMap:
    def __init__(self, map: Map, block_size: int = 2):
        self.block_size = block_size
        self.blocks = {}  # 键: (block_x, block_y), 值: 是否有障碍物
        for x in range(0, map.width, block_size):
            for y in range(0, map.height, block_size):
                block_x, block_y = x // block_size, y // block_size
                has_obstacle = any(
                    map.grid[i, j] == 1
                    for i in range(x, min(x + block_size, map.width))
                    for j in range(y, min(y + block_size, map.height))
                )
                self.blocks[(block_x, block_y)] = has_obstacle

    def is_block_occupied(self, x: float, y: float) -> bool:
        block_x, block_y = int(x // self.block_size), int(y // self.block_size)
        return self.blocks.get((block_x, block_y), False)


class Map:
    def __init__(self,
                 obs_vertices,
                 map_size = [ [-10.0, -10.0], [10.0, 10.0] ],
                 start_pos = [-10.0, -10.0],
                 end_pos = [10.0, 10.0]):

        self.size = map_size
        self.start_pos = start_pos
        self.end_pos = end_pos

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
        self.x, self.y = Map.start_pos
        self.yaw = 0.0

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

        # 碰撞
        for obstacle in self.obstacles:
            if obstacle.contains(Point(self.x,self.y)):
                return scan_distances, scan_points

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

        return scan_distances, scan_points

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

class Robot():

    def __init__(self, Map, v_low, v_high, width, height):

        self.x, self.y = Map.start_pos
        self.end_x, self.end_y = Map.end_pos
        self.v_low = v_low
        self.v_high = v_high
        self.width = width
        self.height = height
        self.sensor = Lidar(Map)
        self.trajectory = []

    def move(self, speed, end_x, end_y):
        self.trajectory.append(end_x, end_y)




# gym env
class PathPlanningWithLidar(gym.Env):

    # 定义render模式
    metadata = {'render.modes': ['human']}

    def __init__(self, MAP):
        super(PathPlanningWithLidar, self).__init__()

        self.map = MAP
        self.sensor = Lidar(self.map)

        # used for render function
        self.fig = None

    def render(self, mode='human'):
        if self.fig is None:
            plt.ion()
            # ax config
            self.fig, self.ax = plt.subplots(figsize=(8, 8))
            self.ax.set_aspect('equal')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_title('Path Planning')

            self.ax.set_xlim(self.map.size[0][0], self.map.size[1][0])
            self.ax.set_ylim(self.map.size[0][1], self.map.size[1][1])

            # draw obstacles
            for obstacle in self.map.obstacles:
                plot_polygon(obstacle, ax=self.ax, facecolor='lightblue', edgecolor='black', add_points=False)
            plt.show()
        else:
            pass

        plt.pause(10)
        plt.ioff()

    def close(self):
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
