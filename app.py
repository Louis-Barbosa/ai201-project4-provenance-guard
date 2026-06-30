"""Provenance-Guard Flask app.

Submission flow (from planning.md):
    POST /submit
      -> word length signal        (signal 1 value)
      -> transition frequency      (signal 2 value)   [TODO: Milestone 4]
      -> confidence scoring        (mean of signals)  [TODO: Milestone 4]
      -> transparency label        (label from mean)  [TODO: Milestone 4]
      -> audit log                 (record + return)
      -> response

Milestone 3 implements: the route + signal 1 (word length), a unique
content_id, a placeholder confidence/label, structured audit logging,
and a GET /log endpoint. Later milestones fill in signals 2, the real
confidence score, and the appeal flow.
"""

import uuid
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from signals import word_length_signal, transition_frequency_signal
from scoring import confidence_score, classify
from audit import write_entry, get_log, find_latest_classification

app = Flask(__name__)

# Rate limiting. Limits are per client IP (get_remote_address).
#   /submit:  10/min, 100/day  -> a real writer checking their own drafts
#             comfortably fits; a script flooding the system gets cut off.
#   /appeal:  5/min, 20/day    -> appeals are rarer and human-driven, so the
#             limit is tighter to prevent appeal spam.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    """Accept a piece of text and run it through the detection pipeline.

    Request body (JSON): {"text": "<submission>", "creator_id": "<optional>"}

    Returns content_id, attribution, a placeholder confidence, a placeholder
    label, and the signal 1 score. Also writes a structured audit entry.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request must include a non-empty 'text' field."}), 400

    content_id = str(uuid.uuid4())

    # Run both detection signals (each returns [0,1], high = human).
    word_length_score = word_length_signal(text)
    transition_score = transition_frequency_signal(text)

    # Confidence = mean of the two signals; label per planning.md thresholds.
    confidence = confidence_score([word_length_score, transition_score])
    attribution, label = classify(confidence)

    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
        "word_length_score": word_length_score,
        "transition_score": transition_score,
        "status": "classified",
    }
    write_entry(entry)

    return jsonify(
        {
            "content_id": content_id,
            "attribution": attribution,
            "confidence": confidence,
            "label": label,
            "signals": {
                "word_length": word_length_score,
                "transition_frequency": transition_score,
            },
        }
    )


@app.route("/appeal", methods=["POST"])
@limiter.limit("5 per minute;20 per day")
def appeal():
    """Accept a creator's appeal of a classification.

    Request body (JSON): {"content_id": "<id>", "creator_reasoning": "<text>"}

    Looks up the original classification, logs the appeal alongside the
    original decision with status "under_review", and returns confirmation.
    Automated re-classification is intentionally out of scope.
    """
    data = request.get_json(silent=True) or {}
    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id or not isinstance(content_id, str):
        return jsonify({"error": "Request must include a 'content_id'."}), 400
    if not creator_reasoning or not isinstance(creator_reasoning, str):
        return jsonify({"error": "Request must include 'creator_reasoning'."}), 400

    original = find_latest_classification(content_id)
    if original is None:
        return jsonify({"error": f"No classified submission found for content_id {content_id}."}), 404

    entry = {
        "content_id": content_id,
        "creator_id": original.get("creator_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "under_review",
        "appeal_reasoning": creator_reasoning,
        # Original classification decision, logged alongside the appeal.
        "original_attribution": original.get("attribution"),
        "original_confidence": original.get("confidence"),
        "original_label": original.get("label"),
        "original_word_length_score": original.get("word_length_score"),
        "original_transition_score": original.get("transition_score"),
    }
    write_entry(entry)

    return jsonify(
        {
            "content_id": content_id,
            "status": "under_review",
            "message": "Appeal received. Your submission is now under review.",
        }
    )


@app.route("/log", methods=["GET"])
def log():
    """Return the most recent audit log entries as JSON."""
    return jsonify({"entries": get_log()})


if __name__ == "__main__":
    app.run(debug=True)
