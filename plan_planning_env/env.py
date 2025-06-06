#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 12:11:36
# Description:
import gym
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# 可用的env
# __all__ = [ "PathPlanningWithLidar" ]

class Map:
    def __init__(self,
                 obstacles_vertices,
                 map_size = [ [-10.0, -10.0], [10.0, 10.0] ],
                 start_pos = [0,-9],
                 end_pos = [2.5, 9]):

        self.size = map_size
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.obstacles_vertices = obstacles_vertices

class Lidar:
    def __init__(self, position=(0, 0), angle=0, num_rays=16, max_range=10.0, fov=360):
        """
        2D激光雷达模拟器

        参数:
            position: 雷达位置 (x, y)
            angle: 雷达初始朝向 (弧度)
            num_rays: 射线数量
            max_range: 最大探测距离
            fov: 视场角 (度)
        """
        self.position = np.array(position, dtype=np.float32)
        self.angle = angle
        self.num_rays = num_rays
        self.max_range = max_range
        self.fov = np.deg2rad(fov)

        # 计算射线角度
        self.ray_angles = np.linspace(-self.fov/2, self.fov/2, num_rays) + angle
        self.ray_directions = np.column_stack([
            np.cos(self.ray_angles),
            np.sin(self.ray_angles)
        ])

        # 存储上一次的扫描结果
        self.last_scan = np.full(num_rays, max_range)

# gym env
class PathPlanningWithLidar(gym.Env):

    # 定义render模式
    metadata = {'render.modes': ['human']}

    def __init__(self, MAP):
        super(PathPlanningWithLidar, self).__init__()
        self.map = MAP

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
                    Polygon(
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
