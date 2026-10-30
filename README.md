# 🤖 Mood Companion
### Deep Sentiment-Conditioned Neural Contextual Bandits for Real-Time Interactive Desktop Companions

A simple, explainable deep-learning project built with **Streamlit** and **PyTorch**.

The companion reads your mood from what you type, picks a response style (joke, break
suggestion, breathing exercise…), and **learns from your 👍 / 👎 in real time**.

```
User message → Emotion model (TF-IDF → MLP) → Context vector → Neural bandit (MLP + ε-greedy) → Action
                                                                     ↑                          │
                                                                     └──── 👍/👎 reward ─────────┘
```

## Dataset
[Emotions dataset for NLP](https://www.kaggle.com/datasets/praveengovi/emotions-dataset-for-nlp)
(~20k sentences, 6 emotions: sadness, joy, love, anger, fear, surprise), downloaded with:

```python
import kagglehub
path = kagglehub.dataset_download("praveengovi/emotions-dataset-for-nlp")
```

No Kaggle API key is needed for this public dataset. If there is no internet, the app falls
back to a small sample in `data/sample_emotions.csv` so it still runs.

> ⚠️ The offline sample is only ~240 sentences, so the emotion model trained on it is close to
> random guessing, and the bandit can't tell moods apart. Always check the Training page says
> `Source: kagglehub: …` before a demo — with the real dataset the model should be far more accurate.

## Setup & run
```bash
pip install -r requirements.txt
```
```bash
streamlit run app.py
```
Optional: train the emotion model from the command line first.
```bash
python train_sentiment.py
```

## App pages
| Page | What it shows |
|------|---------------|
| 📊 Dataset & Training | kagglehub download, label distribution, train the emotion MLP, loss/accuracy curves, confusion matrix |
| 💬 Live Companion | chat, detected emotion, chosen action, bandit's predicted rewards, 👍/👎 feedback that updates the bandit live |
| 🧪 Bandit Simulation | simulated user with hidden preferences; neural bandit vs random vs fixed action vs oracle |
| ℹ️ How it Works | pipeline diagram and plain-language explanation |

## How it works (short version)
1. **Emotion model** (`src/sentiment_model.py`): TF-IDF (5000 uni/bi-grams) → `Linear 128 → ReLU → Dropout → Linear 64 → ReLU → Dropout → Linear 6`, trained with cross-entropy.
2. **Context** (`src/context.py`): 6 emotion probabilities + sin/cos of the hour + conversation length + last reward = 10 numbers.
3. **Neural contextual bandit** (`src/bandit.py`): MLP `10 → 64 → 64 → 8` predicts the reward of each of the 8 actions. ε-greedy: random action with probability ε (explore), else best predicted action (exploit). ε decays from 0.3 to 0.05.
4. **Online learning**: each (context, action, reward) goes into a replay buffer; a few Adam steps with MSE loss on the chosen action's output only.
5. **Evaluation** (`src/simulator.py`): a simulated user with a hidden emotion × action preference table shows the bandit learning to beat random and fixed policies.

## Project structure
```
app.py                 Streamlit UI
train_sentiment.py     CLI training
src/data.py            kagglehub download + fallback
src/sentiment_model.py emotion classifier
src/context.py         context features
src/bandit.py          neural contextual bandit
src/companion.py       actions and response templates
src/simulator.py       simulated user + baselines
data/sample_emotions.csv  offline fallback data
models/                saved weights (created at runtime)
```
