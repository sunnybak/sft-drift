# Explanation before claim confidence — exploratory v6 contract

The v5 small Qwen screen passes its tested order axes but largely returns equal
confidence; the expanded wording/query run exposes sensitivity before completion.
V6 keeps the paired alternatives and confidence target and asks for a brief reason
before the numeric confidence, within the same fresh Conviction forward pass.

Output is exactly `{"reason": "brief basis", "claim_confidence_percent": number}`.
An empty or missing reason is unavailable, separately from strict JSON compliance.
No explanation is judged or used to revise the numerical value. Raw explanations are
retained for inspection of whether the model rates claim confidence or another concept.

The score, control gold values, thresholds, six development beliefs and initial 132
presentations are unchanged. No preceding Stance answer, ethical examples or desired
natural dispersion enter the prompt. This is a new instrument; prior readings are not
reparsed under it. The local output cap increases to 320 tokens to accommodate the reason.
The hosted provider remains at its original provider settings.

Passing a small screen is insufficient. Wording/query/context stability and held-out
topics remain necessary before release. An explanation may help diagnose a rating;
it does not establish faithful access to internal belief or calibrated moral confidence.
