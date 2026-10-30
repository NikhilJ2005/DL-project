"""Simulated user for offline evaluation: each emotion has a hidden "liking" for each action.
We compare the neural bandit against a random policy and a single fixed best action."""
import numpy as np

from src.bandit import NeuralBandit
from src.companion import ACTIONS
from src.context import build_context
from src.data import EMOTIONS

# Hidden probability that the simulated user gives 👍 (rows: emotions, cols: ACTIONS order)
#                     joke quote break breath celeb follow music brief
TRUE_PREFS = np.array([
    [0.20, 0.50, 0.30, 0.40, 0.05, 0.85, 0.50, 0.20],  # sadness
    [0.70, 0.30, 0.10, 0.10, 0.90, 0.40, 0.50, 0.30],  # joy
    [0.40, 0.20, 0.10, 0.10, 0.70, 0.80, 0.60, 0.30],  # love
    [0.10, 0.20, 0.60, 0.85, 0.05, 0.30, 0.50, 0.50],  # anger
    [0.10, 0.50, 0.40, 0.90, 0.05, 0.50, 0.30, 0.20],  # fear
    [0.60, 0.20, 0.10, 0.10, 0.50, 0.85, 0.30, 0.30],  # surprise
])


def run_simulation(emotion_prob_rows, true_labels, rounds=1500, epsilon=0.3, lr=1e-2, seed=0):
    """emotion_prob_rows: (N, 6) predicted emotion probabilities for real test sentences.
    true_labels: their true emotion names (the simulated user's actual mood).
    Returns dict of cumulative-reward arrays plus the bandit's chosen actions."""
    rng = np.random.default_rng(seed)
    bandit = NeuralBandit(epsilon=epsilon, lr=lr, seed=seed)
    best_fixed = int(TRUE_PREFS.mean(axis=0).argmax())

    rewards = {"Neural bandit": [], "Random": [], "Fixed best action": [], "Oracle": []}
    chosen = np.zeros((len(EMOTIONS), len(ACTIONS)), dtype=int)
    last_reward = 0.0
    for t in range(rounds):
        i = rng.integers(len(true_labels))
        mood = EMOTIONS.index(true_labels[i])
        probs = dict(zip(EMOTIONS, emotion_prob_rows[i]))
        ctx = build_context(probs, hour=int(rng.integers(24)), n_turns=t % 20, last_reward=last_reward)

        action, _, _ = bandit.select_action(ctx)
        r = float(rng.random() < TRUE_PREFS[mood, action])
        bandit.update(ctx, action, r)
        chosen[mood, action] += 1
        last_reward = r

        rewards["Neural bandit"].append(r)
        rewards["Random"].append(float(rng.random() < TRUE_PREFS[mood, rng.integers(len(ACTIONS))]))
        rewards["Fixed best action"].append(float(rng.random() < TRUE_PREFS[mood, best_fixed]))
        rewards["Oracle"].append(float(rng.random() < TRUE_PREFS[mood].max()))

    return {
        "cumulative": {k: np.cumsum(v) for k, v in rewards.items()},
        "chosen": chosen,
        "bandit": bandit,
    }
