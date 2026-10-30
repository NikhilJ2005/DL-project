"""Builds the bandit's context vector from the detected emotion and the session state."""
import math
from datetime import datetime

import numpy as np

from src.data import EMOTIONS

# 6 emotion probs + sin(hour) + cos(hour) + session length + last reward
CONTEXT_DIM = len(EMOTIONS) + 4


def build_context(emotion_probs, hour=None, n_turns=0, last_reward=0.0):
    """emotion_probs: dict {emotion: prob}. Returns a float32 numpy vector of size CONTEXT_DIM."""
    if hour is None:
        hour = datetime.now().hour
    angle = 2 * math.pi * hour / 24  # cyclic encoding so 23:00 and 00:00 are close
    features = [emotion_probs[e] for e in EMOTIONS] + [
        math.sin(angle),
        math.cos(angle),
        min(n_turns, 20) / 20.0,
        last_reward,
    ]
    return np.array(features, dtype=np.float32)
