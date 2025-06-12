import numpy as np
import torch
from torch import nn
from transformers import BertModel, BertConfig

class LidarPathTransformer(nn.Module):
    """
    使用 Hugging Face 的 BertModel 作为自注意力编码器
    输入: 雷达距离数组 + 当前坐标 (可选)
    输出: 下一个目标点的相对坐标 (dx, dy)
    """
    def __init__(self, lidar_dim, use_pos=True, hidden_size=128):
        super().__init__()
        self.use_pos = use_pos
        self.lidar_dim = lidar_dim
        self.input_dim = lidar_dim + (2 if use_pos else 0)
        # 配置BERT
        config = BertConfig(
            vocab_size=30522,  # 占位，不用词表
            hidden_size=hidden_size,
            num_attention_heads=4,
            num_hidden_layers=2,
            intermediate_size=hidden_size * 4,
            max_position_embeddings=lidar_dim + (2 if use_pos else 0) + 1,
            type_vocab_size=1
        )
        self.bert = BertModel(config)
        self.input_fc = nn.Linear(self.input_dim, hidden_size)
        self.output_fc = nn.Linear(hidden_size, 2)  # 输出 dx, dy

    def forward(self, lidar_scan, current_pos=None):
        """
        lidar_scan: (batch, lidar_dim)
        current_pos: (batch, 2) or None
        """
        if self.use_pos and current_pos is not None:
            x = torch.cat([lidar_scan, current_pos], dim=-1)
        else:
            x = lidar_scan
        # 变成 (batch, seq_len, hidden_size)
        x = self.input_fc(x).unsqueeze(1)  # (batch, 1, hidden_size)
        # BERT 需要 (batch, seq_len, hidden_size)
        attention_mask = torch.ones(x.shape[:2], dtype=torch.long, device=x.device)
        bert_out = self.bert(inputs_embeds=x, attention_mask=attention_mask)
        pooled = bert_out.last_hidden_state[:, 0, :]  # 取第一个token
        out = self.output_fc(pooled)
        return out

class PathPredictor:
    """
    推理循环：输入雷达，预测下一个点，直到终点
    """
    def __init__(self, model, device='cpu'):
        self.model = model.to(device)
        self.device = device

    def predict_next(self, lidar_scan, current_pos):
        self.model.eval()
        lidar_tensor = torch.tensor(lidar_scan, dtype=torch.float32, device=self.device).unsqueeze(0)
        pos_tensor = torch.tensor(current_pos, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            delta = self.model(lidar_tensor, pos_tensor).cpu().numpy()[0]
        return delta  # dx, dy

    def plan_path(self, lidar_scan_func, start_pos, end_pos, max_steps=100, threshold=0.2):
        path = [np.array(start_pos)]
        current_pos = np.array(start_pos)
        for _ in range(max_steps):
            lidar_scan = lidar_scan_func(current_pos)
            delta = self.predict_next(lidar_scan, current_pos)
            current_pos = current_pos + delta
            path.append(current_pos.copy())
            if np.linalg.norm(current_pos - end_pos) < threshold:
                break
        return np.array(path)