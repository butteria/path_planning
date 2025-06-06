#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 12:11:36
# Description:
import gym
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Polygon, LineString, Point
import numpy as np

# 可用的env
# __all__ = [ "PathPlanningWithLidar" ]

class Map:
    def __init__(self,
                 obstacles_vertices,
                 map_size = [ [-10.0, -10.0], [10.0, 10.0] ],
                 start_pos = [-10.0, -10.0],
                 end_pos = [10.0, 10.0]):

        self.size = map_size
        self.start_pos = start_pos
        self.end_pos = end_pos

        self.obstacles_vertices = obstacles_vertices

class Lidar:
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

        self.__ray_angles = np.deg2rad(np.linspace(-self.scan_angle/2, self.scan_angle/2, self.num_angle))
        self.__poly_obstacles = []
        for obstacle_vertices in Map.obstacles_vertices:
            self.__poly_obstacles.append(Polygon(obstacle_vertices))


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
        for poly_obstacle in self.__poly_obstacles:
            if poly_obstacle.contains(Point(self.x,self.y)):
                print(self.x, self.y)
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
        for poly_obstacle in self.__poly_obstacles:
            intersections = poly_obstacle.intersection(ray_line)
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
        self.sensor = Lidar(self.map)
        print(f"distance point:{self.sensor.scan()}")
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
            for obstacle_vertices in self.map.obstacles_vertices:
                self.ax.add_patch(
                    MplPolygon(
                        obstacle_vertices,
                        closed = True,
                        fill = True,
                        facecolor = 'lightblue',
                        edgecolor = 'black'
                    )
                )
            plt.show()
        else:
            pass

        plt.pause(10)

    def close(self):
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
