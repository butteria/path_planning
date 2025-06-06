#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 19:56:21
# Description:

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.lines import Line2D
import pickle
from shapely.geometry import Polygon as ShapelyPolygon, Point

plt.rcParams['toolbar'] = 'None'
plt.rcParams['xtick.bottom'] = False
plt.rcParams['xtick.labelbottom'] = False
plt.rcParams['ytick.left'] = False
plt.rcParams['ytick.labelleft'] = False

class MapEditor:
    def __init__(self):
        # 初始化图形和坐标轴
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.fig.canvas.manager.set_window_title('Map Editor')

        # 绘图状态
        self.current_shapely_polygon = None  # Shapely 的 Polygon（存储几何数据）
        self.current_vertices = []           # 当前多边形的顶点
        self.drawing = False                 # 是否正在绘制
        self.selected_mpl_polygon = None     # matplotlib 的 Polygon（用于绘图和交互）
        self.drag_start = None               # 拖拽起始点
        self.current_mouse_pos = None        # 当前鼠标位置（用于虚线预览）

        # 设置坐标轴
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_aspect('equal')

        # 状态文本
        self.status_text = self.ax.text(
            -10, 11,
            "LEFT CLICK: Add polygon vertices\n"
            "RIGHT CLICK: Select shapes (turns red)\n"
            "D: Delete selected shape\n"
            "ENTER: Complete polygon\n"
            "ESC: Cancel drawing\n"
            "CTRL+S: Save map  CTRL+L: Load map",
            bbox=dict(facecolor='white', alpha=0.8)
        )

        # 临时虚线（用于绘制预览）
        self.temp_line = Line2D([], [], color='red', linestyle='--', alpha=0.7)
        self.ax.add_line(self.temp_line)

        # 绑定事件
        self.connect_events()

    def connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        if event.button == 3:  # 右键点击：选择形状
            if self.selected_mpl_polygon:
                self.drag_start = (event.xdata, event.ydata)
            self.select_shape(event)
        elif event.button == 1:  # 左键点击
            if not self.drawing:
                self.start_new_polygon(event)  # 开始新多边形
            else:
                self.add_vertex(event)         # 添加顶点

    def select_shape(self, event):
        """选择鼠标下的形状（高亮显示）"""
        if self.selected_mpl_polygon:
            self.deselect_shape()

        for patch in reversed(self.ax.patches):  # 从后往前检查（优先选择上层的形状）
            if isinstance(patch, MplPolygon) and patch.contains_point((event.x, event.y)):
                self.selected_mpl_polygon = patch
                patch.set_edgecolor('red')
                self.redraw()
                return

    def deselect_shape(self):
        """取消选择形状"""
        if self.selected_mpl_polygon:
            self.selected_mpl_polygon.set_edgecolor('black')
            self.selected_mpl_polygon = None
            self.redraw()

    def start_new_polygon(self, event):
        """开始绘制新多边形"""
        self.drawing = True
        self.current_vertices = [(event.xdata, event.ydata)]  # 只添加第一个顶点
        mpl_polygon = MplPolygon(self.current_vertices, closed=False, fill=False, color='black', linewidth=2)
        self.ax.add_patch(mpl_polygon)
        self.selected_mpl_polygon = mpl_polygon  # 存储 matplotlib 的 Polygon
        self.current_mouse_pos = (event.xdata, event.ydata)  # 初始化鼠标位置
        self.update_temp_line()
        self.redraw()

    def add_vertex(self, event):
        """向当前多边形添加顶点"""
        if not self.drawing or not self.current_vertices:
            return

        self.current_vertices.append((event.xdata, event.ydata))
        self.selected_mpl_polygon.set_xy(self.current_vertices)  # 更新 matplotlib Polygon
        self.current_mouse_pos = (event.xdata, event.ydata)      # 更新鼠标位置

        # 只有当顶点数 >= 3 时才创建 Shapely Polygon
        if len(self.current_vertices) >= 3:
            self.current_shapely_polygon = ShapelyPolygon(self.current_vertices)

        self.update_temp_line()
        self.redraw()

    def update_temp_line(self):
        """更新绘制预览的虚线"""
        if len(self.current_vertices) > 0 and self.current_mouse_pos:
            last_point = self.current_vertices[-1]
            self.temp_line.set_data(
                [last_point[0], self.current_mouse_pos[0]],
                [last_point[1], self.current_mouse_pos[1]]
            )
            self.redraw()

    def finish_polygon(self):
        """完成当前多边形"""
        if self.drawing and self.current_shapely_polygon and len(self.current_vertices) >= 3:
            # 确保多边形闭合（Shapely 会自动闭合）
            self.drawing = False
            self.current_shapely_polygon = None  # 不再需要 Shapely Polygon
            self.current_vertices = []
            self.temp_line.set_data([], [])
            self.current_mouse_pos = None
            self.redraw()
        elif len(self.current_vertices) < 3:
            print("Error: A polygon requires at least 3 vertices!")
            self.cancel_drawing()

    def on_motion(self, event):
        """处理鼠标移动（虚线预览和拖拽）"""
        if event.inaxes != self.ax:
            return

        # 更新当前鼠标位置
        self.current_mouse_pos = (event.xdata, event.ydata)

        if self.drawing and len(self.current_vertices) > 0:
            # 更新绘制预览的虚线（连接最后一个点到当前鼠标位置）
            self.update_temp_line()

        elif self.selected_mpl_polygon and self.drag_start:
            # 拖拽选中的形状
            dx = event.xdata - self.drag_start[0]
            dy = event.ydata - self.drag_start[1]
            vertices = np.array(self.selected_mpl_polygon.get_xy()) + np.array([dx, dy])
            self.selected_mpl_polygon.set_xy(vertices)

            # 更新 Shapely Polygon（如果需要）
            if self.current_shapely_polygon:
                self.current_shapely_polygon = ShapelyPolygon(vertices)

            self.drag_start = (event.xdata, event.ydata)
            self.redraw()

    def on_release(self, event):
        """处理鼠标释放事件"""
        if event.button == 3 and self.drag_start:
            self.drag_start = None

    def on_key_press(self, event):
        """处理键盘事件"""
        if event.key == 'enter' and self.drawing:
            self.finish_polygon()
        elif event.key == 'escape':
            self.cancel_drawing()
        elif event.key == 'd' and self.selected_mpl_polygon:
            self.delete_selected_shape()
        elif event.key == 'ctrl+s':
            self.save_map("../plan_planning_env/obstacles/poly/poly.pkl")
            self.fig.savefig("../plan_planning_env/obstacles/img/map.png")
        elif event.key == 'ctrl+l':
            self.load_map("../plan_planning_env/obstacles/poly/poly.pkl")

    def delete_selected_shape(self):
        """删除选中的形状"""
        if self.selected_mpl_polygon:
            self.selected_mpl_polygon.remove()
            self.selected_mpl_polygon = None
            self.redraw()

    def cancel_drawing(self):
        """取消当前绘制"""
        if self.drawing and self.selected_mpl_polygon:
            self.selected_mpl_polygon.remove()
            self.drawing = False
            self.current_shapely_polygon = None
            self.current_vertices = []
            self.temp_line.set_data([], [])
            self.current_mouse_pos = None
            self.redraw()

    def save_map(self, filename):
        """保存地图到文件"""
        shapes_data = []
        for patch in self.ax.patches:
            if isinstance(patch, MplPolygon):
                shapes_data.append(patch.get_xy().tolist())
        with open(filename, 'wb') as f:
            pickle.dump(shapes_data, f)
        print(f"Map saved to {filename}")

    def load_map(self, filename):
        """从文件加载地图"""
        try:
            with open(filename, 'rb') as f:
                shapes_data = pickle.load(f)
            # 清除当前地图
            for patch in self.ax.patches[:]:
                patch.remove()
            # 加载形状
            for shape_data in shapes_data:
                mpl_polygon = MplPolygon(shape_data, fill=True, edgecolor='black', facecolor='lightblue', linewidth=2)
                self.ax.add_patch(mpl_polygon)
            print(f"Map loaded from {filename}")
            self.redraw()
        except Exception as e:
            print(f"Error loading map: {e}")

    def redraw(self):
        """重绘画布"""
        self.fig.canvas.draw_idle()

# 运行编辑器
if __name__ == '__main__':
    editor = MapEditor()
    plt.tight_layout()
    plt.show()
