#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: butteria
# Email: butteriaaa@gmail.com
# Created on: 2025-06-06 15:38:42
# Description:

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
import tkinter as tk
import os
from tkinter import filedialog
import pickle

plt.rcParams['toolbar'] = 'None'
plt.rcParams['xtick.bottom'] = False
plt.rcParams['xtick.labelbottom'] = False
plt.rcParams['ytick.left'] = False
plt.rcParams['ytick.labelleft'] = False
current_dir = os.getcwd()
class MapEditor:
    def __init__(self):

        # Initialize figure and axes
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.fig.canvas.manager.set_window_title('Map Editor')
        # self.mode = "drawing"
        # self.fig.suptitle(f"{self.mode} mode", y=0.98)  # y=0.98 靠近顶部
        
        self.scaling = False
        self.scale_ref_dist = None
        self.scale_ref_vertices = None
        # Drawing state
        self.current_shape = None
        self.current_vertices = []
        self.drawing = False
        self.selected_shape = None
        self.drag_start = None

        # set start and end points
        self.start= None
        self.end = None
        self.__set_end = False
        self.__set_start = False
        self.plt_start = self.ax.plot([], [], marker='*', color='green', markersize=15, label='start')[0]
        self.plt_end = self.ax.plot([], [], marker='*', color='red', markersize=15, label='end')[0]

        # Setup axes
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_aspect('equal')

        # Status text
        # self.status_text = self.ax.text(-10, 11,
        #                               "LEFT CLICK: Add polygon vertices\n"
        #                               "RIGHT CLICK: Select shapes (turns red)\n"
        #                               "D: Delete selected shape\n"
        #                               "ENTER: Complete polygon\n"
        #                               "ESC: Cancel drawing\n"
        #                               "CTRL+S: Save map  CTRL+L: Load map",
        #                               bbox=dict(facecolor='white', alpha=0.8))

        # Temporary dashed line for drawing
        self.temp_line = Line2D([], [], color='red', linestyle='--', alpha=0.7)
        self.ax.add_line(self.temp_line)

        # Connect events
        self.connect_events()
        root = tk.Tk()
        root.withdraw()



    # add event listeners
    def connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        x, y = event.xdata, event.ydata
        if event.button == 3:  # Right click - select shape
            if self.selected_shape:
                self.drag_start = (event.xdata, event.ydata)
            if event.key == 'control':  # Ctrl+rightmouse scale
                if self.selected_shape:
                    self.scaling = True
                    verts = np.array(self.selected_shape.get_xy())
                    self.scale_ref_vertices = verts.copy()
                    center = verts.mean(axis=0)
                    self.scale_center = center
                    self.scale_ref_dist = np.linalg.norm([event.xdata - center[0], event.ydata - center[1]])
            else:
                self.select_shape(event)
        elif event.button == 1:  # Left click
            if self.drawing:
                self.add_vertex(event)
            else:
                if self.__set_start: # set start point
                    self.plt_start.set_data([x], [y])
                    self.redraw()
                    self.start = [x, y]
                elif self.__set_end: # set end point
                    self.plt_end.set_data([x], [y])
                    self.redraw()
                    self.end = [x, y]
                else:
                    self.start_new_polygon(event)

    def select_shape(self, event):
        """Select shape under mouse cursor"""
        # Deselect current shape if any
        if self.selected_shape:
            self.deselect_shape()

        # Find and select new shape
        for shape in reversed(self.ax.patches):
            if hasattr(shape, 'contains') and shape.contains(event)[0]:
                self.selected_shape = shape
                shape.set_edgecolor('red')
                self.redraw()
                return

    def deselect_shape(self):
        """Deselect current shape and restore left click functionality"""
        if self.selected_shape:
            self.selected_shape.set_edgecolor('black')
            self.selected_shape = None
            self.redraw()

    def start_new_polygon(self, event):
        """Start drawing new polygon with dashed preview"""
        self.drawing = True
        self.current_vertices = [(event.xdata, event.ydata)]
        self.current_shape = Polygon(self.current_vertices, closed=False,
                                   fill=False, color='black', linewidth=2)
        self.ax.add_patch(self.current_shape)
        self.update_temp_line()
        self.redraw()

    def add_vertex(self, event):
        """Add vertex to current polygon with dashed preview"""
        if not self.drawing or not self.current_shape:
            return

        self.current_vertices.append((event.xdata, event.ydata))
        self.current_shape.set_xy(self.current_vertices)
        self.update_temp_line()
        self.redraw()

    def update_temp_line(self):
        """Update temporary dashed line during drawing"""
        if len(self.current_vertices) > 0:
            last_point = self.current_vertices[-1]
            self.temp_line.set_data([last_point[0], last_point[0]],
                                  [last_point[1], last_point[1]])

    def finish_polygon(self):
        """Complete current polygon"""
        if self.drawing and self.current_shape and len(self.current_vertices) > 2:
            self.current_shape.set_closed(True)
            self.drawing = False
            self.current_shape = None
            self.current_vertices = []
            self.temp_line.set_data([], [])
            self.redraw()

    def on_motion(self, event):
        """Handle mouse movement for dashed preview and dragging"""
        if event.inaxes != self.ax:
            return

        if self.scaling and self.selected_shape and self.scale_ref_dist is not None:
            if event.xdata is None or event.ydata is None:
                return
            # 缩放操作
            center = self.scale_center
            curr_dist = np.linalg.norm([event.xdata - center[0], event.ydata - center[1]])
            scale = curr_dist / self.scale_ref_dist if self.scale_ref_dist != 0 else 1.0
            verts = (self.scale_ref_vertices - center) * scale + center
            self.selected_shape.set_xy(verts)
            self.redraw()

        elif self.drawing and len(self.current_vertices) > 0:
            # Update temporary dashed line during drawing
            last_point = self.current_vertices[-1]
            self.temp_line.set_data([last_point[0], event.xdata],
                                  [last_point[1], event.ydata])
            self.redraw()

        elif self.selected_shape and self.drag_start:  # Drag selected shape
            dx = event.xdata - self.drag_start[0]
            dy = event.ydata - self.drag_start[1]

            vertices = self.selected_shape.get_xy()
            vertices += np.array([dx, dy])
            self.selected_shape.set_xy(vertices)

            self.drag_start = (event.xdata, event.ydata)
            self.redraw()

    def on_release(self, event):
        if event.button == 3:
            if self.scaling:
                self.scaling = False
                self.scale_ref_dist = None
                self.scale_ref_vertices = None
        """Handle mouse release after dragging"""
        if event.button == 3 and hasattr(self, 'drag_start'):
            self.drag_start = None

    def on_key_press(self, event):
        """Handle keyboard events"""
        if event.key == 'enter' and self.drawing:
            self.finish_polygon()
        elif event.key == 'escape':
            self.cancel_drawing()
            self.__set_start = False
            self.__set_end = False
        elif event.key == 'd' and self.selected_shape:
            self.delete_selected_shape()
        elif event.key == 's':
            self.__set_end = False
            self.__set_start = True
        elif event.key == 'e':
            self.__set_start = False
            self.__set_end = True
        elif event.key == 'ctrl+s':
            self.save_map()
        elif event.key == 'ctrl+l':
            self.load_map()

    def delete_selected_shape(self):
        """Delete selected shape and restore left click functionality"""
        if self.selected_shape:
            self.selected_shape.remove()
            self.selected_shape = None
            self.redraw()

    def cancel_drawing(self):
        """Cancel current drawing operation"""
        if self.drawing and self.current_shape:
            self.current_shape.remove()
            self.drawing = False
            self.current_shape = None
            self.current_vertices = []
            self.temp_line.set_data([], [])
            self.redraw()

    def save_map(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pkl",
            initialdir=current_dir+"/obstacles/poly/",
            filetypes=[("Pickle files", "*.pkl")],
            title="保存地图",
        )
        if file_path:
            shapes_data = []
            for shape in self.ax.patches:
                if isinstance(shape, Polygon):
                    shapes_data.append(shape.get_xy().tolist())
            map_data = {
                "obstacles": shapes_data,
                "start": self.start,
                "end": self.end
            }

            with open(file_path, 'wb') as f:
                pickle.dump(map_data, f)
            # both save image
            self.fig.savefig(current_dir+"/obstacles/img/"+os.path.splitext(os.path.basename(file_path))[0], bbox_inches='tight')

    def load_map(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".pkl",
            initialdir=current_dir+"/obstacles/poly/",
            filetypes=[("Pickle files", "*.pkl")],
            title="读取地图",
        )
        if file_path:
            with open(file_path, 'rb') as f:
                map_data = pickle.load(f)
                
                # Clear current map
                for shape in self.ax.patches[:]:
                    shape.remove()
                # Load shapes
                for shape_data in map_data.get("obstacles", []):
                    shape = Polygon(shape_data,
                                    fill=True,
                                    edgecolor='black',
                                    facecolor='lightblue',
                                    linewidth=2)
                    self.ax.add_patch(shape)
                # Load start/end
                self.start = map_data.get("start", None)
                self.end = map_data.get("end", None)
                if self.start:
                    self.plt_start.set_data(self.start)
                if self.end:
                    self.plt_end.set_data(self.end)
                self.redraw()

    def redraw(self):
        """Redraw canvas"""
        self.fig.canvas.draw_idle()

# Run the editor
if __name__ == '__main__':
    editor = MapEditor()

    plt.tight_layout()
    plt.show()
