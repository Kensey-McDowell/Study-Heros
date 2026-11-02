"""Turns a deck into multiple-choice questions, favoring cards you miss."""
from dataclasses import dataclass


@dataclass
class Question:
    card_index: int
    prompt: str
    answer: str
    options: list
    correct_index: int
    label: str


class QuizEngine:
    def __init__(self, cards, ask_mode, rng):
        self.cards = [c for c in cards if c["term"].strip() and c["definition"].strip()]
        self.ask_mode = ask_mode  # "term", "definition" or "mixed"
        self.rng = rng
        n = len(self.cards)
        self.weights = [1.0] * n
        self.misses = [0] * n
        self.hits = [0] * n
        self.last = None
        self.total_answered = 0
        self.total_correct = 0

    def next_question(self):
        indices = [i for i in range(len(self.cards)) if i != self.last] or [0]
        idx = self.rng.choices(indices, weights=[self.weights[i] for i in indices])[0]
        self.last = idx
        card = self.cards[idx]
        side = self.ask_mode if self.ask_mode != "mixed" else self.rng.choice(("term", "definition"))
        if side == "term":
            prompt, answer, key, label = card["term"], card["definition"], "definition", "What does this mean?"
        else:
            prompt, answer, key, label = card["definition"], card["term"], "term", "Which term matches?"

        seen = {answer.strip().lower()}
        pool = []
        for c in self.cards:
            value = c[key].strip()
            if value.lower() not in seen:
                seen.add(value.lower())
                pool.append(value)
        options = self.rng.sample(pool, min(3, len(pool))) + [answer]
        self.rng.shuffle(options)
        return Question(idx, prompt, answer, options, options.index(answer), label)

    def record(self, idx, correct):
        self.total_answered += 1
        if correct:
            self.total_correct += 1
            self.hits[idx] += 1
            self.weights[idx] = max(0.4, self.weights[idx] * 0.7)
        else:
            self.misses[idx] += 1
            self.weights[idx] += 2.0  # Missed cards come back more often.

    def trickiest(self, n=5):
        ranked = sorted(range(len(self.cards)), key=lambda i: self.misses[i], reverse=True)
        return [(self.cards[i], self.misses[i]) for i in ranked[:n] if self.misses[i] > 0]

    @property
    def accuracy(self):
        return self.total_correct / self.total_answered if self.total_answered else 0.0
