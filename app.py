"""Streamlit app: Deep Sentiment-Conditioned Neural Contextual Bandits for Desktop Companions.

Run with:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from src.bandit import NeuralBandit
from src.companion import ACTION_LABELS, ACTIONS, respond
from src.context import build_context
from src.data import EMOTIONS, KAGGLE_DATASET, load_dataset
from src.sentiment_model import SentimentModel
from src.simulator import TRUE_PREFS, run_simulation

st.set_page_config(page_title="Mood Companion", page_icon="🤖", layout="wide")


@st.cache_data(show_spinner="Downloading dataset with kagglehub…")
def get_data():
    return load_dataset()


def get_sentiment_model():
    if "sentiment" not in st.session_state:
        st.session_state.sentiment = SentimentModel.load()
    return st.session_state.sentiment


def get_bandit():
    if "bandit" not in st.session_state:
        bandit = NeuralBandit()
        bandit.load()
        st.session_state.bandit = bandit
    return st.session_state.bandit


def need_model():
    model = get_sentiment_model()
    if model is None:
        st.warning("No emotion model yet. Go to **📊 Dataset & Training** and train it first (~1 min).")
        st.stop()
    return model


# ---------------------------------------------------------------- pages
def page_training():
    st.header("📊 Dataset & Training")
    st.write(f"Kaggle dataset: `{KAGGLE_DATASET}` (downloaded via `kagglehub.dataset_download`).")
    train, val, test, source = get_data()
    st.caption(f"Source: {source}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Train", len(train))
    c2.metric("Validation", len(val))
    c3.metric("Test", len(test))

    st.subheader("Label distribution")
    st.bar_chart(train["label"].value_counts())
    st.subheader("Sample rows")
    st.dataframe(train.sample(8, random_state=1), use_container_width=True)

    st.subheader("Train the emotion classifier (TF-IDF → MLP)")
    epochs = st.slider("Epochs", 2, 20, 8)
    if st.button("🚀 Train model", type="primary"):
        bar = st.progress(0.0)
        status = st.empty()

        def progress(e, n, loss, acc):
            bar.progress(e / n)
            status.write(f"Epoch {e}/{n} — loss {loss:.4f} — val acc {acc:.3f}")

        model = SentimentModel()
        history = model.train(train, val, epochs=epochs, progress=progress)
        model.save()
        st.session_state.sentiment = model
        st.session_state.history = history
        st.session_state.test_eval = model.evaluate(test)
        st.success("Model trained and saved to models/")

    if "history" in st.session_state:
        hist = pd.DataFrame(st.session_state.history).set_index("epoch")
        c1, c2 = st.columns(2)
        c1.line_chart(hist["train_loss"])
        c2.line_chart(hist["val_accuracy"])
        ev = st.session_state.test_eval
        st.metric("Test accuracy", f"{ev['accuracy']:.1%}")
        st.write("Confusion matrix (rows = true, columns = predicted)")
        st.dataframe(pd.DataFrame(ev["confusion"], index=EMOTIONS, columns=EMOTIONS))


def page_companion():
    st.header("💬 Live Companion")
    model = need_model()
    bandit = get_bandit()
    ss = st.session_state
    ss.setdefault("chat", [])
    ss.setdefault("pending", None)
    ss.setdefault("last_reward", 0.0)

    left, right = st.columns([3, 2])
    with left:
        for msg in ss.chat:
            st.chat_message(msg["role"]).write(msg["text"])

        if ss.pending:
            st.write("Was that response helpful?")
            b1, b2, _ = st.columns([1, 1, 4])
            reward = None
            if b1.button("👍 Yes"):
                reward = 1.0
            if b2.button("👎 No"):
                reward = 0.0
            if reward is not None:
                p = ss.pending
                loss = bandit.update(p["context"], p["action"], reward)
                bandit.save()
                ss.last_reward = reward
                ss.chat.append({"role": "assistant",
                                "text": f"_Thanks! Learned from your feedback (loss {loss:.3f})._"})
                ss.pending = None
                st.rerun()

        text = st.chat_input("How are you feeling? Tell your companion…")
        if text:
            probs = model.predict(text)
            emotion = max(probs, key=probs.get)
            ctx = build_context(probs, n_turns=len(ss.chat) // 2, last_reward=ss.last_reward)
            action, explored, preds = bandit.select_action(ctx)
            ss.chat.append({"role": "user", "text": text})
            ss.chat.append({"role": "assistant", "text": respond(ACTIONS[action], emotion)})
            ss.pending = {"context": ctx, "action": action, "probs": probs, "emotion": emotion,
                          "explored": explored, "preds": preds}
            ss.last_turn = ss.pending
            st.rerun()

    with right:
        turn = ss.get("last_turn")
        if turn:
            st.subheader(f"Detected mood: {turn['emotion']}")
            st.bar_chart(pd.Series(turn["probs"], name="probability"))
            mode = "🎲 exploring (random)" if turn["explored"] else "🎯 exploiting (best predicted)"
            st.write(f"Action: **{ACTION_LABELS[ACTIONS[turn['action']]]}** — {mode}")
            st.write("Bandit's predicted reward per action")
            st.bar_chart(pd.Series(turn["preds"], index=[ACTION_LABELS[a] for a in ACTIONS]))
        st.metric("Exploration rate ε", f"{bandit.epsilon:.3f}")
        st.metric("Feedback collected", len(bandit.buffer))
        if st.button("Reset companion memory"):
            ss.bandit = NeuralBandit()
            ss.bandit.save()
            ss.chat, ss.pending, ss.last_turn = [], None, None
            st.rerun()


def page_simulation():
    st.header("🧪 Bandit Simulation")
    st.write("A simulated user with hidden preferences sends real test sentences from the dataset. "
             "We check whether the neural bandit learns to pick the right action for each mood.")
    model = need_model()
    _, _, test, _ = get_data()

    c1, c2, c3 = st.columns(3)
    rounds = c1.slider("Rounds", 200, 5000, 1500, step=100)
    epsilon = c2.slider("Starting ε", 0.0, 1.0, 0.3)
    lr = c3.select_slider("Learning rate", [1e-3, 3e-3, 1e-2, 3e-2], value=1e-2)

    with st.expander("Hidden user preferences (probability of 👍)"):
        st.dataframe(pd.DataFrame(TRUE_PREFS, index=EMOTIONS,
                                  columns=[ACTION_LABELS[a] for a in ACTIONS]).style.format("{:.2f}"))

    if st.button("▶️ Run simulation", type="primary"):
        with st.spinner("Simulating…"):
            sample = test.sample(min(len(test), 1000), random_state=0)
            probs = model.predict_proba(sample["text"])
            result = run_simulation(probs, sample["label"].tolist(), rounds, epsilon, lr)
        cum = pd.DataFrame(result["cumulative"])
        st.subheader("Cumulative reward (higher is better)")
        st.line_chart(cum)
        final = cum.iloc[-1]
        cols = st.columns(len(final))
        for col, (name, value) in zip(cols, final.items()):
            col.metric(name, f"{value / rounds:.1%}", help="average 👍 rate")
        st.subheader("Which action the bandit chose for each true mood")
        chosen = pd.DataFrame(result["chosen"], index=EMOTIONS, columns=[ACTION_LABELS[a] for a in ACTIONS])
        st.dataframe(chosen.style.background_gradient(axis=1, cmap="Greens"))


def page_about():
    st.header("ℹ️ How it works")
    st.graphviz_chart("""
    digraph {
        rankdir=LR; node [shape=box, style=rounded];
        msg [label="User message"];
        sent [label="Emotion model\\nTF-IDF → MLP\\n(6 emotions)"];
        ctx [label="Context vector\\nemotions + time\\n+ session info"];
        bandit [label="Neural bandit\\nMLP predicts reward\\nper action\\n+ ε-greedy"];
        act [label="Companion action\\n(joke, break, …)"];
        fb [label="User 👍 / 👎\\n= reward"];
        msg -> sent -> ctx -> bandit -> act -> fb;
        fb -> bandit [label="online update", style=dashed];
    }
    """)
    st.markdown("""
**1. Deep sentiment model.** Text is turned into TF-IDF numbers, and a small neural network
(two hidden layers) outputs the probability of 6 emotions. Trained on the Kaggle *Emotions dataset for NLP*.

**2. Context.** The emotion probabilities plus time of day (sin/cos), conversation length and
the last reward form a 10-number context vector — this is what *sentiment-conditioned* means.

**3. Neural contextual bandit.** Another small network looks at the context and predicts how
much the user will like each of 8 actions. With probability ε it tries a random action
(**exploration**), otherwise it picks the highest prediction (**exploitation**). ε slowly decays.

**4. Real-time learning.** Your 👍 (1) or 👎 (0) is the reward. The bandit stores it in a replay
buffer and takes a few gradient steps (MSE loss, only on the chosen action) — so it adapts
to *you* while you chat.

**5. Evaluation.** The simulation page compares the bandit against random choice, a single
fixed action, and an oracle that knows the hidden preferences.
""")


PAGES = {
    "📊 Dataset & Training": page_training,
    "💬 Live Companion": page_companion,
    "🧪 Bandit Simulation": page_simulation,
    "ℹ️ How it Works": page_about,
}

st.sidebar.title("🤖 Mood Companion")
st.sidebar.caption("Deep Sentiment-Conditioned Neural Contextual Bandits")
choice = st.sidebar.radio("Go to", list(PAGES))
PAGES[choice]()
