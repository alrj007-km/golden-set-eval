# Documentation Evaluation Rubric

This rubric scores one document against the golden-set questions that expect
it as an answer. The golden set maps a question to a document by naming that
document as the expected answer; a mapped question implies a task when it
asks the reader to do something, not merely define something.

Four dimensions apply: retrievability, task-completeness, boundary-clarity,
deprecation-signal. Each dimension uses a scale from zero to five. Every
level states a condition a second reviewer can check without guessing at the
first reviewer's intent.

## Retrievability

Whether a retrieval system can surface this document for a realistic user
query.

> Scored against golden-set questions written in user phrasing, not document
> vocabulary. A naming mismatch is a retrievability failure, not a separate
> dimension.

Vocabulary bridging — matching a user's term to the document's term — is not
a separate dimension. It causes a retrievability failure; scoring the cause
and the failure separately would count one defect twice.

| Score | Criterion |
|---|---|
| 0 | The retrieval system returns this document for none of its mapped queries. |
| 1 | The retrieval system returns this document somewhere in the result set for fewer than half of its mapped queries. |
| 2 | The retrieval system returns this document somewhere in the result set for at least half of its mapped queries, and not at all for the rest. |
| 3 | The retrieval system returns this document within the top three results for at least half of its mapped queries, and somewhere in the result set for the rest. |
| 4 | The retrieval system returns this document within the top three results for every mapped query, and as the top result for at least half of them. |
| 5 | The retrieval system returns this document as the top result for every mapped query. |

## Task-completeness

Whether a reader can finish the mapped task without leaving this document.
Each level below measures a single thing: how much the reader must supply
that the document does not.

| Score | Criterion |
|---|---|
| 0 | The document does not address the mapped task. |
| 1 | The document omits more than one piece of information the reader needs and cannot infer, sending the reader outside the document more than once. |
| 2 | The document omits one piece of information the reader needs for a required step, and the reader cannot infer it from the document. |
| 3 | The document omits one piece of information the reader cannot infer, but only for a non-required or edge-case step; the reader completes the primary task path inside the document. |
| 4 | The document states everything the task requires except one detail the reader can infer from an example already in the document; no step sends the reader elsewhere. |
| 5 | The document states every step, prerequisite, and expected result the task requires; the reader supplies nothing. |

## Boundary-clarity

Whether the document states what it does not cover.

| Score | Criterion |
|---|---|
| 0 | The document's title or introduction claims broader coverage than the body delivers. |
| 1 | The document states no boundary, explicit or implied, though the topic has an evident adjacent case — a version, platform, or tier — it does not mention. |
| 2 | The document states no boundary, explicit or implied, and the topic has no evident adjacent case it silently excludes. |
| 3 | The document points to where it handles an adjacent case, for example "for X, see Y," without using exclusion language. |
| 4 | The document states an out-of-scope condition explicitly, but only in general terms, without naming a specific case. |
| 5 | The document states at least one out-of-scope condition explicitly and names a specific case. |

## Deprecation-signal

Whether a machine can determine if the document's claims are still current.
This dimension applies only when the document makes at least one time- or
version-dependent claim. A document with no such claim has nothing for a
currency signal to attach to; that is not the same condition as a document
that carries a currency signal, and it does not earn the same score. Mark
the dimension N/A for that document and exclude it from the document's
aggregate rather than scoring it a five.

| Score | Criterion |
|---|---|
| N/A | The document makes no time- or version-dependent claim. Exclude this dimension from the document's aggregate. |
| 0 | The document states a time- or version-dependent claim as permanent — "always," "never changes" — without qualification. |
| 1 | Half or more of the document's substantive claims are time- or version-dependent, and none carry a currency signal. |
| 2 | At least one time- or version-dependent claim carries no currency signal, and fewer than half of the document's substantive claims are time- or version-dependent. |
| 3 | At least one time- or version-dependent claim carries a currency signal in prose only, for example "as of the current release," not machine-parseable without inference. |
| 4 | At least one time- or version-dependent claim carries a machine-parseable marker, but the marker covers the whole document rather than the specific claim. |
| 5 | Every time- or version-dependent claim in the document carries an adjacent, machine-parseable marker: a version number or an ISO date. |

Implementation note: `run.py` and the scorecard must treat N/A as excluded
from a document's aggregate, not as a zero and not as a five. A document
scored N/A on this dimension is judged on the remaining three.

## What this rubric does not measure

This rubric does not score style, tone, or grammar. It does not verify that
a document's technical claims are accurate.

Those failures require a human reviewer with domain knowledge. A document
can score five on every dimension here and still be wrong.
