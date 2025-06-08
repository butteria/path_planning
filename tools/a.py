import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import pickle

class MapEditor:
    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.fig.canvas.manager.set_window_title('Map Editor')

        self.current_shape = None
        self.current_vertices = []
        self.drawing = False
        self.selected_shape = None
        self.drag_start = None

        self.start_point = None
        self.end_point = None
        self.start_artist = None
        self.end_artist = None

        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_aspect('equal')

        self.status_text = self.ax.text(-10, 11,
            "LEFT CLICK: Add polygon vertices\n"
            "RIGHT CLICK: Select shapes (turns red)\n"
            "D: Delete selected shape\n"
            "ENTER: Complete polygon\n"
            "ESC: Cancel drawing\n"
            "S: Set Start  E: Set End\n"
            "CTRL+S: Save map  CTRL+L: Load map",
            bbox=dict(facecolor='white', alpha=0.8))

        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        plt.show()

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        if event.button == 3:  # Right click - select shape
            if self.selected_shape:
                self.drag_start = (event.xdata, event.ydata)
            self.select_shape(event)
        elif event.button == 1:  # Left click
            if getattr(self, "_add_start", False):
                self.set_start(event.xdata, event.ydata)
                self._add_start = False
                return
            if getattr(self, "_add_end", False):
                self.set_end(event.xdata, event.ydata)
                self._add_end = False
                return
            if not self.drawing:
                self.start_new_polygon(event)
            self.add_vertex(event)

    def set_start(self, x, y):
        self.start_point = [x, y]
        if self.start_artist:
            self.start_artist.remove()
        self.start_artist = self.ax.plot(x, y, marker='*', color='green', markersize=15, label='Start')[0]
        self.redraw()

    def set_end(self, x, y):
        self.end_point = [x, y]
        if self.end_artist:
            self.end_artist.remove()
        self.end_artist = self.ax.plot(x, y, marker='*', color='red', markersize=15, label='End')[0]
        self.redraw()

    def on_key_press(self, event):
        if event.key == 'enter' and self.drawing:
            self.finish_polygon()
        elif event.key == 'escape':
            self.cancel_drawing()
        elif event.key == 'd' and self.selected_shape:
            self.delete_selected_shape()
        elif event.key == 'ctrl+s':
            self.save_map("../plan_planning_env/obstacles/poly/poly.pkl")
            self.fig.savefig("../plan_planning_env/obstacles/img/map.png")
        elif event.key == 'ctrl+l':
            self.load_map("../plan_planning_env/obstacles/poly/poly.pkl")
        elif event.key == 's':
            print("请在画布上点击以设置起点")
            self._add_start = True
        elif event.key == 'e':
            print("请在画布上点击以设置终点")
            self._add_end = True

    def start_new_polygon(self, event):
        self.drawing = True
        self.current_vertices = []
        self.current_shape = None

    def add_vertex(self, event):
        if not self.drawing:
            return
        self.current_vertices.append([event.xdata, event.ydata])
        if self.current_shape:
            self.current_shape.remove()
        self.current_shape = Polygon(self.current_vertices, fill=True, edgecolor='black', facecolor='lightblue', linewidth=2)
        self.ax.add_patch(self.current_shape)
        self.redraw()

    def finish_polygon(self):
        if self.current_shape and len(self.current_vertices) > 2:
            self.current_shape.set_xy(self.current_vertices)
        self.drawing = False
        self.current_shape = None
        self.current_vertices = []
        self.redraw()

    def cancel_drawing(self):
        if self.current_shape:
            self.current_shape.remove()
        self.drawing = False
        self.current_shape = None
        self.current_vertices = []
        self.redraw()

    def select_shape(self, event):
        for shape in self.ax.patches:
            if isinstance(shape, Polygon):
                contains, _ = shape.contains_point((event.xdata, event.ydata), radius=0)
                if contains:
                    if self.selected_shape:
                        self.selected_shape.set_edgecolor('black')
                    self.selected_shape = shape
                    shape.set_edgecolor('red')
                    self.redraw()
                    return
        if self.selected_shape:
            self.selected_shape.set_edgecolor('black')
            self.selected_shape = None
            self.redraw()

    def delete_selected_shape(self):
        if self.selected_shape:
            self.selected_shape.remove()
            self.selected_shape = None
            self.redraw()

    def redraw(self):
        self.fig.canvas.draw_idle()

    def save_map(self, filename='poly.pkl'):
        """Save map to file"""
        shapes_data = []
        for shape in self.ax.patches:
            if isinstance(shape, Polygon):
                shapes_data.append(shape.get_xy().tolist())

        map_data = {
            "obstacles": shapes_data,
            "start": self.start_point,
            "end": self.end_point
        }

        with open(filename, 'wb') as f:
            pickle.dump(map_data, f)

        print(f"Map and points saved to {filename}")

    def load_map(self, filename='poly.pkl'):
        """Load map from file"""
        try:
            with open(filename, 'rb') as f:
                map_data = pickle.load(f)

            # Clear current map
            for shape in self.ax.patches[:]:
                shape.remove()
            if self.start_artist:
                self.start_artist.remove()
                self.start_artist = None
            if self.end_artist:
                self.end_artist.remove()
                self.end_artist = None

            # Load shapes
            for shape_data in map_data.get("obstacles", []):
                shape = Polygon(shape_data,
                                fill=True,
                                edgecolor='black',
                                facecolor='lightblue',
                                linewidth=2)
                self.ax.add_patch(shape)

            # Load start/end
            self.start_point = map_data.get("start", None)
            self.end_point = map_data.get("end", None)
            if self.start_point:
                self.start_artist = self.ax.plot(self.start_point[0], self.start_point[1], marker='*', color='green', markersize=15, label='Start')[0]
            if self.end_point:
                self.end_artist = self.ax.plot(self.end_point[0], self.end_point[1], marker='*', color='red', markersize=15, label='End')[0]

            print(f"Map loaded from {filename}")
            self.redraw()
        except Exception as e:
            print(f"Error loading map: {e}")

if __name__ == "__main__":
    MapEditor()