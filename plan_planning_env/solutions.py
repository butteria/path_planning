import numpy as np
from shapely.geometry import Point, LineString
from scipy.spatial import cKDTree
import heapq

class RRT:
    def __init__(self, Map, step_size=0.5, max_iter=1000):
        self.map = Map
        self.start = np.array(self.map.start)
        self.end = np.array(self.map.end)
        self.step_size = step_size
        self.max_iter = max_iter
        self.tree = [self.start]
        self.parent = {0: None}
        self.kdtree = cKDTree([self.start])  # 新增

    def sample(self):
        x = np.random.uniform(self.map.size[0][0], self.map.size[1][0])
        y = np.random.uniform(self.map.size[0][1], self.map.size[1][1])
        return np.array([x, y])

    def nearest(self, point):
        # 使用KD-Tree查找最近点
        dist, idx = self.kdtree.query(point)
        return idx, self.tree[idx]

    def collision(self, p1, p2):
        line = LineString([p1, p2])
        for obs in self.map.obstacles:
            if line.crosses(obs) or line.within(obs):
                return True
        return False

    def plan(self):
        for i in range(self.max_iter):
            rnd = self.sample()
            idx_near, node_near = self.nearest(rnd)
            direction = rnd - node_near
            direction = direction / np.linalg.norm(direction)
            new_node = node_near + self.step_size * direction

            if self.collision(node_near, new_node):
                continue

            self.tree.append(new_node)
            self.parent[len(self.tree) - 1] = idx_near
            # 每次添加新节点后重建KD-Tree
            self.kdtree = cKDTree(self.tree)

            if np.linalg.norm(new_node - self.end) < 2 * self.step_size:
                if not self.collision(new_node, self.end):
                    self.tree.append(self.end)
                    self.parent[len(self.tree) - 1] = len(self.tree) - 2
                    self.kdtree = cKDTree(self.tree)
                    return self.extract_path()
        return None

    def extract_path(self):
        path = []
        idx = len(self.tree) - 1
        while idx is not None:
            path.append(self.tree[idx])
            idx = self.parent[idx]
        path.reverse()
        return path

class WaveFront:
    """
    基于栅格的涟漪（Wavefront）路径规划算法
    """
    def __init__(self, Map, grid_resolution=0.1):
        self.map = Map
        self.grid_resolution = grid_resolution
        self.start = np.array(self.map.start)
        self.end = np.array(self.map.end)
        self.grid, self.ox, self.oy = self.create_occupancy_grid()
        self.rows, self.cols = self.grid.shape

    def create_occupancy_grid(self):
        """
        将地图障碍物转为栅格地图
        """
        min_x, min_y = self.map.size[0]
        max_x, max_y = self.map.size[1]
        ox = np.arange(min_x, max_x + self.grid_resolution, self.grid_resolution)
        oy = np.arange(min_y, max_y + self.grid_resolution, self.grid_resolution)
        grid = np.zeros((len(ox), len(oy)), dtype=np.int8)
        for i, x in enumerate(ox):
            for j, y in enumerate(oy):
                p = Point(x, y)
                for obs in self.map.obstacles:
                    if obs.contains(p):
                        grid[i, j] = 1  # 障碍物
                        break
        return grid, ox, oy

    def pos_to_idx(self, pos):
        ix = int(round((pos[0] - self.ox[0]) / self.grid_resolution))
        iy = int(round((pos[1] - self.oy[0]) / self.grid_resolution))
        return ix, iy

    def idx_to_pos(self, idx):
        x = self.ox[idx[0]]
        y = self.oy[idx[1]]
        return np.array([x, y])

    def plan(self):
        """
        执行涟漪算法，返回路径（若找到）
        """
        start_idx = self.pos_to_idx(self.start)
        end_idx = self.pos_to_idx(self.end)
        if self.grid[start_idx] == 1 or self.grid[end_idx] == 1:
            return None  # 起点或终点在障碍物内

        wave = np.full_like(self.grid, -1, dtype=np.int32)
        wave[end_idx] = 0
        queue = [end_idx]
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

        # 涟漪扩散
        while queue:
            curr = queue.pop(0)
            for d in dirs:
                ni, nj = curr[0] + d[0], curr[1] + d[1]
                if 0 <= ni < self.rows and 0 <= nj < self.cols:
                    if self.grid[ni, nj] == 0 and wave[ni, nj] == -1:
                        wave[ni, nj] = wave[curr] + 1
                        queue.append((ni, nj))
                        if (ni, nj) == start_idx:
                            queue = []
                            break

        # 回溯路径
        if wave[start_idx] == -1:
            return None  # 无法到达

        path = []
        curr = start_idx
        while curr != end_idx:
            path.append(self.idx_to_pos(curr))
            min_wave = wave[curr]
            next_idx = curr
            for d in dirs:
                ni, nj = curr[0] + d[0], curr[1] + d[1]
                if 0 <= ni < self.rows and 0 <= nj < self.cols:
                    if wave[ni, nj] >= 0 and wave[ni, nj] < min_wave:
                        min_wave = wave[ni, nj]
                        next_idx = (ni, nj)
            if next_idx == curr:
                break  # 死循环保护
            curr = next_idx
        path.append(self.idx_to_pos(end_idx))
        path.reverse()
        return path