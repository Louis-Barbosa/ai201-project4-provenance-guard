"""Confidence scoring + transparency labels for Provenance-Guard.

Combines the individual signal scores into a single confidence value and
maps that value to an attribution category and a human-readable label.

All scores use the same direction: closer to 1.0 = more HUMAN, closer to
0.0 = more AI. The confidence score is the MEAN of the individual signals,
exactly as specified in planning.md ("the average of the two individual
confidence values").

Thresholds (planning.md "Uncertainty representation"):
    0.70 - 1.00  -> likely_human   "Likely human generated"
    0.41 - 0.69  -> uncertain      "Uncertain if AI generated"
    0.00 - 0.40  -> likely_ai      "Likely AI generated"

These were widened from the original 0.76/0.20 cutoffs: with two averaged
signals, clear-cut inputs still landed in the middle, so the human/AI labels
were effectively unreachable. The uncertain band stays wide to keep the
"protect attribution" intent, but clear cases now classify correctly.
"""


def confidence_score(signal_scores):
    """Combine individual signal scores into one confidence value (the mean)."""
    if not signal_scores:
        return 0.5
    return round(sum(signal_scores) / len(signal_scores), 4)


def classify(confidence):
    """Map a confidence value to (attribution, label) per the planning.md spec."""
    if confidence >= 0.70:
        return "likely_human", "Likely human generated"
    if confidence <= 0.40:
        return "likely_ai", "Likely AI generated"
    return "uncertain", "Uncertain if AI generated"