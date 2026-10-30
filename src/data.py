"""Dataset loading: Kaggle "Emotions dataset for NLP" via kagglehub, with an offline fallback."""
import os

import pandas as pd

KAGGLE_DATASET = "praveengovi/emotions-dataset-for-nlp"
EMOTIONS = ["sadness", "joy", "love", "anger", "fear", "surprise"]
SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sample_emotions.csv")


def _read_split(path):
    # Each line looks like: "i feel so happy today;joy"
    return pd.read_csv(path, sep=";", header=None, names=["text", "label"], encoding="utf-8")


def download_kaggle_dataset():
    """Download the dataset with kagglehub and return the local folder path."""
    import kagglehub

    return kagglehub.dataset_download(KAGGLE_DATASET)


def load_dataset():
    """Return (train_df, val_df, test_df, source) where source says where the data came from.

    Tries kagglehub first; if there is no internet / Kaggle is unreachable, falls back to
    the small sample CSV shipped in data/ so the app always runs.
    """
    try:
        folder = download_kaggle_dataset()
        files = {}
        for root, _, names in os.walk(folder):
            for name in names:
                files[name] = os.path.join(root, name)
        train = _read_split(files["train.txt"])
        val = _read_split(files["val.txt"])
        test = _read_split(files["test.txt"])
        source = f"kagglehub: {KAGGLE_DATASET}"
    except Exception as err:  # network error, missing files, etc.
        df = pd.read_csv(SAMPLE_CSV).sample(frac=1.0, random_state=0).reset_index(drop=True)
        n = len(df)
        train = df.iloc[: int(0.7 * n)]
        val = df.iloc[int(0.7 * n): int(0.85 * n)]
        test = df.iloc[int(0.85 * n):]
        source = f"offline sample ({type(err).__name__}: {err})"

    clean = lambda d: d[d["label"].isin(EMOTIONS)].dropna().reset_index(drop=True)
    return clean(train), clean(val), clean(test), source
