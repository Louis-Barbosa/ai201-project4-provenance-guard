# ai201-project4-provenance-guard

## Architecture overview:

For Submissions: The submission works when POST /subit receives JSON {...} which has data like the "text" and "creator_id". It validates that the text is a non-empty string and creates a unique content_id (uuid4). The info is then passed inot signals.py where the text is run through both singals: word_length_singal() and transition_frequency_signal(). Each will reuturn a float from [0,1] where 1.0 is human and 0.0 is AI. The closer a score is to one of these end values then the more likely it is one of these two. Then these float values are sent to scoring.py which turns the signals into a score and then a label. The function confidence_score() averages the two signal values into one and then classify() will map the confidence score to a attribution and tranparency label. Then all of this is recoded in the audit log by appending it to audit_log.jsonl though write_entry. Finally, the information is turned into a response, returning a JSON with content_id, attribution, confidence, label, and the individual signals.

For appeals: The appeal will come in as a POST /appeal and will recieve the JSON information "content_id" and "creator_reasoning". It will also be validated that both are non-empty strings otherwise it will throw a 404 error. Then it will call the function find_latest_classification() and scan the append-only log for the most recent entry with that content_id and status == "classified". It will then build an appeal entry as a new dict that has the status: "under review", the appeal reasoning, a timestamp, the creator_id, and a copy fo the original decision. This will then be recoded in the audit log by appending it to audit_log.jsonl through write_entry. Finally, the information is returned as a JSON response confirming the content_id, new status of being under review, and a message telling the creator that their work is currently under reiview. 

## Detection signals:

Signal 1: word_length_signal() -> This measures the coefficient of variation of per-sentence word counts. This is because AI prose tends to be long and uniform in sentence length while human writing swings between short and long sentenced. Using CV instead of stdev makes it length independent. What this misses is anyone who writes intentionally uniform sentences will score AI-like, and AI explicity promted to vary sentence length defeats it. Also it doesn't worl well on very sort inputs, so it returns 0.5 for anything less than 2 sentences. 

Signal 2: transition_frequency_signal() -> Combines two submetrics and averages them: the density of ~45 known transition terms over the total words, capped at 8% and the fraction of sentences that open with a transtition word. The rational behind this is that AI over-uses connective scaffolding; while humans have a more idiosyncratic word choice. However, it will miss for people who natually favor transition words as they will get marked down as likely-AI. Also the list in fixed for an English-only dictionary meaning paraphrased or non-English connectives will slip through. 

## Confidence scoring: 
The confidence is simply the mean of the two signal scores. Both signals share one direction 1.0 is human and 0.0 is AI. The average is meaningful as neither need inverting at combine time. I checked that the two signals move idependently so the mean carrie smore information than either alone, and I tuned the threshold against real inputs. The original cutoffs were too narrow so I widened them to 0.7/0.4 which let the unambigious text classify corretly while keeping a deliberately wide uncertain zone. 

Two example submissions:

High-confidence (human), ~0.85+: A personal anecdote with wildly varying sentence lengths ("I left. The door slammed behind me and I realized, standing there in the rain with nothing but a crumpled receipt in my pocket, that I had no idea where to go next.") and almost no transition words → high CV, near-zero transition density → both signals high → confidently "Likely human generated."
Lower-confidence (AI), ~0.15–0.30: Uniform-length explanatory sentences each opening with a connective ("Furthermore, the system is efficient. Moreover, it scales well. Additionally, it is robust. Consequently, users benefit.") → low CV + high transition density and opener fraction → both signals low → "Likely AI generated" with low confidence.

## Transparency label:
Confidence range|attribution|Label text shown
0.70 – 1.00 | likely_human | "Likely human generated"
0.41 – 0.69 | uncertain | "Uncertain if AI generated"
0.00 – 0.40 | likely_ai | "Likely AI generated"


## Rate limiting:
The rates were limited to /submit 10/min, 100/day. This is because a genuine writer checking drafts will fit comfortably within this range but a script trying to flood the classifier will get cut off quickly

For appeals it was set to 5/min 20/day. This is because appeals would be rarer and human-driven so a tigher limit prevents any appeal spam without being so strict that it burdens a legitimate creator who would likely only appeal a few times a day.

## Known limitations:

The known limitations are simply if a person immitates what an AI would do. So if a person either writes in a structure where the sentences are uniform and similar to one another or if they favor writing with a lot of transitions. Examples of this are a structured poem with equal-length lines and equal stanza counts, as it would seem AI-like in terms of structure, and a paper writen in academic prose since they use transition words in most sentences. 

## Spec reflection:
The planning.md architecture and narrative gave me an extremely precise pipeline to implemet making it extremely clear the flow of information. However, there were some difference between the planning and the final product in terms of threshold cutoffs changing and also in implementation I folded classification into /submit rather than exposing it as its own endpoint — splitting it would mean either re-running signals or passing state between calls, adding complexity with no benefit since classification is deterministic from the text. 


## AI usage section:

1.I directed Claude to generate the /submit route and the word-length signal from the planning.md spec. What I overrode: I had it switch from raw standard deviation to the coefficient of variation so the measure wouldn't be biased by overall sentence length, and I pinned down the edge-case behavior (return 0.5 — neutral — for <2 sentences or zero-word means) rather than letting it crash or default arbitrarily.
2.I directed Claude to wire confidence scoring and labels using my original 0.76/0.20 cutoffs. After testing real inputs I found clear cases never escaped the uncertain band, so I overrode the spec's own numbers, instructing the change to 0.70/0.40 and having the reasoning documented in both scoring.py lines 11 through 19 and planning.md — keeping the wide uncertain zone but making the "likely" labels actually reachable.

## Example of log: 
{"content_id": "71b738dc-b063-452d-8bc8-68ecda2d4477", "creator_id": "ai-writer-01", "timestamp": "2026-06-30T01:39:21.600223+00:00", "attribution": "likely_ai", "confidence": 0.25, "label": "Likely AI generated", "word_length_score": 0.5, "transition_score": 0.0, "status": "classified"}
{"content_id": "e2e34319-cbf1-4180-8e0a-7ef24e9ac99b", "creator_id": "human-writer-02", "timestamp": "2026-06-30T01:39:21.610205+00:00", "attribution": "likely_human", "confidence": 0.7627, "label": "Likely human generated", "word_length_score": 0.5253, "transition_score": 1.0, "status": "classified"}
{"content_id": "424fefe8-1c82-4103-b6c1-3f765bb1fdd8", "creator_id": "mixed-writer-03", "timestamp": "2026-06-30T01:39:21.613356+00:00", "attribution": "uncertain", "confidence": 0.5, "label": "Uncertain if AI generated", "word_length_score": 0.0, "transition_score": 1.0, "status": "classified"}
{"content_id": "71b738dc-b063-452d-8bc8-68ecda2d4477", "creator_id": "ai-writer-01", "timestamp": "2026-06-30T01:39:21.630395+00:00", "status": "under_review", "appeal_reasoning": "I wrote this myself. English is my second language, so my prose reads more formal than average.", "original_attribution": "likely_ai", "original_confidence": 0.25, "original_label": "Likely AI generated", "original_word_length_score": 0.5, "original_transition_score": 0.0}
