"""Command-line training: python train_sentiment.py"""
from src.data import load_dataset
from src.sentiment_model import SentimentModel

if __name__ == "__main__":
    train, val, test, source = load_dataset()
    print(f"Data source: {source} | train={len(train)} val={len(val)} test={len(test)}")
    model = SentimentModel()
    model.train(train, val, progress=lambda e, n, loss, acc: print(
        f"epoch {e}/{n}  loss={loss:.4f}  val_acc={acc:.3f}"))
    print(f"Test accuracy: {model.evaluate(test)['accuracy']:.3f}")
    model.save()
    print("Saved to models/")
