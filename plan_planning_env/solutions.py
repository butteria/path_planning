import numpy as np
from shapely.geometry import Point, LineString

class RRT:
    def __init__(self, Map, step_size=0.5, max_iter=1000):
        self.map = Map
        self.start = np.array(self.map.start)
        self.end = np.array(self.map.end)
        self.step_size = step_size
        self.max_iter = max_iter
        self.tree = [ self.start ]
        self.parent = { 0: None }
    
    def sample(self):
        x = np.random.uniform(self.map.size[0][0], self.map.size[1][0])
        y = np.random.uniform(self.map.size[0][1], self.map.size[1][1])
        return np.array([x, y])
    
    # TODO: KD-Tree
    def nearest(self, point):
        distance = [ np.linalg.norm(n - point) for n in self.tree ]
        idx = np.argmin(distance)
        return idx, self.tree[idx]

    # 判断两点之间是否有障碍物
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
            self.parent[len(self.tree)-1] = idx_near

            if np.linalg.norm(new_node - self.end) < self.step_size:
                # 连接到终点
                if not self.collision(new_node, self.end):
                    self.tree.append(self.end)
                    self.parent[len(self.tree)-1] = len(self.tree)-2
                    return self.extract_path()
        return None  # 未找到路径

    def extract_path(self):
        path = []
        idx = len(self.tree) - 1
        while idx is not None:
            path.append(self.tree[idx])
            idx = self.parent[idx]
        path.reverse()
        return path