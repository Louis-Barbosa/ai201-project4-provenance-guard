"""Detection signals for Provenance-Guard.

Each signal takes raw text and returns a float in [0.0, 1.0].

Score convention (matches planning.md "Uncertainty representation"):
    closer to 1.0  ->  looks more HUMAN
    closer to 0.0  ->  looks more AI

Signal 1: word/sentence length variation.
    AI text tends toward long, uniform sentence lengths (low variation).
    Human text tends to vary sentence length a lot (high variation).
    So: high variation -> high (human) score, low variation -> low (AI) score.
"""

import re
import statistics


def _split_sentences(text):
    """Split text into sentences on ., !, ? boundaries.

    Returns a list of non-empty, stripped sentence strings.
    """
    parts = re.split(r"[.!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def _word_count(sentence):
    """Count words in a sentence (whitespace-separated tokens)."""
    return len(sentence.split())


def word_length_signal(text):
    """Score a piece of text by how much its sentence lengths vary.

    Returns a float in [0.0, 1.0]:
        ~1.0 -> sentence lengths vary a lot  -> looks human
        ~0.0 -> sentence lengths very uniform -> looks AI

    Implementation: use the coefficient of variation (CV) of per-sentence
    word counts. CV = stdev / mean, which makes the measure independent of
    overall sentence length. We then map CV onto [0, 1] with a cap, since a
    CV above ~1.0 is already strongly varied (clearly human-like).

    Edge cases:
        - empty / no sentences          -> 0.5 (no information, fully uncertain)
        - a single sentence             -> 0.5 (cannot measure variation)
        - all sentences identical length-> 0.0 (perfectly uniform -> AI-like)
    """
    sentences = _split_sentences(text)

    # Not enough data to measure variation -> stay neutral.
    if len(sentences) < 2:
        return 0.5

    counts = [_word_count(s) for s in sentences]
    mean = statistics.mean(counts)

    # Guard against division by zero (e.g. all sentences had 0 words).
    if mean == 0:
        return 0.5

    stdev = statistics.pstdev(counts)
    cv = stdev / mean

    # Map CV to [0, 1]. CV of 0 -> 0.0 (uniform/AI). CV >= 1.0 -> 1.0 (varied/human).
    score = min(cv, 1.0)
    return round(score, 4)


# --- Signal 2: transition-word frequency ---------------------------------

# Common transition words/phrases that AI text tends to over-use.
TRANSITION_TERMS = [
    "furthermore", "moreover", "however", "therefore", "thus", "hence",
    "consequently", "additionally", "in addition", "in conclusion",
    "for instance", "for example", "on the other hand", "as a result",
    "nevertheless", "nonetheless", "in summary", "to summarize",
    "first", "firstly", "second", "secondly", "third", "thirdly",
    "finally", "ultimately", "indeed", "notably", "importantly",
    "it is important to note", "it is worth noting", "overall",
    "in particular", "specifically", "subsequently", "accordingly",
    "meanwhile", "likewise", "similarly", "in other words", "that said",
]


def _count_transition_terms(text_lower):
    """Count total occurrences of any transition term in lowercased text."""
    total = 0
    for term in TRANSITION_TERMS:
        # \b word boundaries so "first" doesn't match "firstly", etc.
        total += len(re.findall(r"\b" + re.escape(term) + r"\b", text_lower))
    return total


def transition_frequency_signal(text):
    """Score a piece of text by how heavily it leans on transition words.

    Returns a float in [0.0, 1.0], using the SAME direction as signal 1:
        ~1.0 -> few transition words      -> looks human
        ~0.0 -> many transition words     -> looks AI

    Combines two metrics, then averages them:
        (a) transition-word density: transition occurrences / total words
        (b) fraction of sentences that START with a transition word
            (a strong tell of AI's "Furthermore, ... Moreover, ..." style)

    Both metrics measure "AI-ness", so we average them and invert
    (score = 1 - ai_ness) to keep high = human.

    Edge case: empty / no words -> 0.5 (no information, fully uncertain).
    """
    text_lower = text.lower()
    words = text_lower.split()
    total_words = len(words)

    if total_words == 0:
        return 0.5

    # Metric (a): density of transition terms, capped at a heavy 8%.
    transition_count = _count_transition_terms(text_lower)
    density = transition_count / total_words
    density_ai = min(density / 0.08, 1.0)

    # Metric (b): fraction of sentences opening with a transition term.
    sentences = _split_sentences(text)
    if sentences:
        opens = 0
        for s in sentences:
            s_low = s.lower()
            if any(s_low.startswith(term) for term in TRANSITION_TERMS):
                opens += 1
        opener_ai = opens / len(sentences)
    else:
        opener_ai = 0.0

    ai_ness = (density_ai + opener_ai) / 2
    score = 1.0 - ai_ness
    return round(score, 4)
