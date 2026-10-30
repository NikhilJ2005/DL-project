"""The companion's actions (bandit arms) and the response text for each one."""
import random

ACTIONS = [
    "tell_joke",
    "motivational_quote",
    "suggest_break",
    "breathing_exercise",
    "celebrate",
    "ask_followup",
    "recommend_music",
    "stay_brief",
]

ACTION_LABELS = {
    "tell_joke": "😂 Tell a joke",
    "motivational_quote": "💪 Motivational quote",
    "suggest_break": "☕ Suggest a break",
    "breathing_exercise": "🌬️ Breathing exercise",
    "celebrate": "🎉 Celebrate with you",
    "ask_followup": "🗨️ Ask a follow-up",
    "recommend_music": "🎵 Recommend music",
    "stay_brief": "🤐 Stay brief",
}

RESPONSES = {
    "tell_joke": [
        "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
        "I told my computer I needed a break... it said 'No problem, I'll go to sleep.' 💤",
        "Why did the neural network go to therapy? Too many unresolved layers.",
    ],
    "motivational_quote": [
        "\"It always seems impossible until it's done.\" — Nelson Mandela",
        "Small progress is still progress. You've got this! 💪",
        "Every expert was once a beginner. Keep going.",
    ],
    "suggest_break": [
        "How about a 5-minute break? Stretch, grab some water, come back fresh. ☕",
        "You've been at it a while. A short walk can reset your mind.",
    ],
    "breathing_exercise": [
        "Let's breathe together: in for 4… hold for 4… out for 6. Repeat 3 times. 🌬️",
        "Try box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s.",
    ],
    "celebrate": [
        "That's awesome! 🎉 I'm really happy for you!",
        "Woohoo! Moments like this deserve a little victory dance. 💃",
    ],
    "ask_followup": [
        "Do you want to tell me more about it? I'm listening.",
        "What do you think caused that feeling?",
    ],
    "recommend_music": [
        "Here's an idea: put on some lo-fi beats and let your mind settle. 🎵",
        "Music time! Maybe a playlist that matches your mood?",
    ],
    "stay_brief": [
        "Got it. I'm here if you need me. 👍",
        "Okay. 🙂",
    ],
}

EMOTION_OPENERS = {
    "sadness": "I'm sorry you're feeling down.",
    "joy": "I love that energy!",
    "love": "That sounds really warm.",
    "anger": "That sounds frustrating.",
    "fear": "That sounds stressful, it's okay to feel that way.",
    "surprise": "Whoa, that's unexpected!",
}


def respond(action, emotion):
    return f"{EMOTION_OPENERS.get(emotion, '')} {random.choice(RESPONSES[action])}".strip()
