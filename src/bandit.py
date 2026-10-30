"""Neural contextual bandit: an MLP predicts the reward of every action given the context,
and epsilon-greedy decides between exploring (random action) and exploiting (best action)."""
import os
import random

import numpy as np
import torch
import torch.nn as nn

from src.companion import ACTIONS
from src.context import CONTEXT_DIM

BANDIT_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "bandit.pt")


class RewardNet(nn.Module):
    def __init__(self, context_dim=CONTEXT_DIM, n_actions=len(ACTIONS)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(context_dim, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU(),
            nn.Linear(64, n_actions),
        )

    def forward(self, x):
        return self.net(x)  # one predicted reward per action


class NeuralBandit:
    def __init__(self, epsilon=0.3, epsilon_min=0.05, epsilon_decay=0.995,
                 lr=1e-2, train_steps=4, batch_size=32, buffer_size=2000, seed=0):
        torch.manual_seed(seed)
        self.rng = random.Random(seed)
        self.model = RewardNet()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.epsilon, self.epsilon_min, self.epsilon_decay = epsilon, epsilon_min, epsilon_decay
        self.train_steps, self.batch_size, self.buffer_size = train_steps, batch_size, buffer_size
        self.buffer = []  # replay buffer of (context, action, reward)

    def predict_rewards(self, context):
        with torch.no_grad():
            return self.model(torch.tensor(context).unsqueeze(0))[0].numpy()

    def select_action(self, context):
        """Returns (action_index, explored?, predicted_rewards)."""
        rewards = self.predict_rewards(context)
        if self.rng.random() < self.epsilon:
            return self.rng.randrange(len(ACTIONS)), True, rewards
        return int(np.argmax(rewards)), False, rewards

    def update(self, context, action, reward):
        """Store the feedback and take a few gradient steps on random mini-batches."""
        self.buffer.append((context, action, float(reward)))
        self.buffer = self.buffer[-self.buffer_size:]
        loss = 0.0
        for _ in range(self.train_steps):
            batch = self.rng.sample(self.buffer, min(self.batch_size, len(self.buffer)))
            x = torch.tensor(np.stack([b[0] for b in batch]))
            a = torch.tensor([b[1] for b in batch])
            r = torch.tensor([b[2] for b in batch], dtype=torch.float32)
            # Only the chosen action's output gets a gradient: we only observed that reward.
            pred = self.model(x).gather(1, a.unsqueeze(1)).squeeze(1)
            loss_t = nn.functional.mse_loss(pred, r)
            self.optimizer.zero_grad()
            loss_t.backward()
            self.optimizer.step()
            loss = loss_t.item()
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return loss

    def save(self, path=BANDIT_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({"model": self.model.state_dict(), "epsilon": self.epsilon,
                    "buffer": self.buffer}, path)

    def load(self, path=BANDIT_PATH):
        if not os.path.exists(path):
            return False
        state = torch.load(path, weights_only=False)
        self.model.load_state_dict(state["model"])
        self.epsilon = state["epsilon"]
        self.buffer = state["buffer"]
        return True
