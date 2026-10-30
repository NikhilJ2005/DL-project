"""Emotion classifier: TF-IDF features -> small PyTorch MLP -> 6 emotion probabilities."""
import os
import pickle

import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data import EMOTIONS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "sentiment.pt")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")


class EmotionMLP(nn.Module):
    def __init__(self, n_features, n_classes=len(EMOTIONS)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        return self.net(x)  # raw logits; softmax is applied in predict()


class SentimentModel:
    def __init__(self, max_features=5000):
        self.vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))
        self.model = None

    def _to_tensor(self, texts):
        return torch.tensor(self.vectorizer.transform(texts).toarray(), dtype=torch.float32)

    def train(self, train_df, val_df, epochs=8, lr=1e-3, batch_size=64, progress=None):
        """Train the MLP. `progress(epoch, epochs, train_loss, val_acc)` is called each epoch."""
        torch.manual_seed(0)
        self.vectorizer.fit(train_df["text"])
        x_train = self._to_tensor(train_df["text"])
        y_train = torch.tensor([EMOTIONS.index(l) for l in train_df["label"]])
        self.model = EmotionMLP(x_train.shape[1])
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss()

        history = []
        for epoch in range(epochs):
            self.model.train()
            perm = torch.randperm(len(x_train))
            total = 0.0
            for i in range(0, len(x_train), batch_size):
                idx = perm[i: i + batch_size]
                optimizer.zero_grad()
                loss = loss_fn(self.model(x_train[idx]), y_train[idx])
                loss.backward()
                optimizer.step()
                total += loss.item() * len(idx)
            train_loss = total / len(x_train)
            val_acc = self.evaluate(val_df)["accuracy"]
            history.append({"epoch": epoch + 1, "train_loss": train_loss, "val_accuracy": val_acc})
            if progress:
                progress(epoch + 1, epochs, train_loss, val_acc)
        return history

    def predict_proba(self, texts):
        self.model.eval()
        with torch.no_grad():
            return torch.softmax(self.model(self._to_tensor(texts)), dim=1).numpy()

    def predict(self, text):
        """Return a dict {emotion: probability} for a single message."""
        probs = self.predict_proba([text])[0]
        return dict(zip(EMOTIONS, probs.tolist()))

    def evaluate(self, df):
        probs = self.predict_proba(df["text"])
        y_pred = probs.argmax(axis=1)
        y_true = np.array([EMOTIONS.index(l) for l in df["label"]])
        confusion = np.zeros((len(EMOTIONS), len(EMOTIONS)), dtype=int)
        for t, p in zip(y_true, y_pred):
            confusion[t, p] += 1
        return {"accuracy": float((y_pred == y_true).mean()), "confusion": confusion}

    def save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save(self.model.state_dict(), MODEL_PATH)
        with open(VECTORIZER_PATH, "wb") as f:
            pickle.dump(self.vectorizer, f)

    @classmethod
    def load(cls):
        """Load a saved model, or return None if it has not been trained yet."""
        if not (os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH)):
            return None
        obj = cls()
        with open(VECTORIZER_PATH, "rb") as f:
            obj.vectorizer = pickle.load(f)
        obj.model = EmotionMLP(len(obj.vectorizer.vocabulary_))
        obj.model.load_state_dict(torch.load(MODEL_PATH))
        obj.model.eval()
        return obj
