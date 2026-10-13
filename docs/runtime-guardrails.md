# Runtime guardrails: four paths, one contract

No single guardrail catches everything. A prompt-injection scanner says nothing about whether an answer stays on
topic; a topical rail says nothing about whether a JSON blob matches its schema; neither classifies content safety
the way a purpose-trained model does. So guard in depth, with tools that each do one job:

| Path | Job | Typical tools | Where it sits |
|---|---|---|---|
| **Scan** | fast input/output sanitisation: injection, PII, grounding, action policy | Prompt Guard, Presidio, an NLI cross-encoder, an allowlist | the always-on first layer, on every request |
| **Classify** | model-based content safety (safe / unsafe + category) | Llama Guard (a small model by default, a larger one on demand) | a second opinion the Scan layer calls |
| **Dialog** | keep a conversation in scope; resist jailbreaks | NeMo Guardrails | only the conversational surface |
| **Structure** | output-schema validation, re-asking the model to repair | Guardrails AI | only producers of structured output |

Each runs where it earns its keep, not on every request. Heavy tools with conflicting dependency trees (Guardrails
AI and NeMo pin libraries other stacks cannot share) run as their own services; that is usually what decides the
architecture, more than any design argument.

## The guard service contract

A guard service exposes one typed route per hook, so each hook can require its own fields:

| Route | Body | Typical validators |
|---|---|---|
| `POST /guard/input` | `{request_id, query, actor?}` | injection, content safety |
| `POST /guard/output` | `{request_id, answer, sources: [{content}], actor?}` | PII, grounding (needs the sources), content safety |
| `POST /guard/act` | `{request_id, tool, params?, actor?}` | an audit record, an enforcing allowlist / rate limit |
| `GET /ready` | — | 503 until the validator set is loaded |
| `GET /metrics` | — | verdicts by validator and decision, validator latency |

Response: `{request_id, decision: "allow" | "block", verdict: {validator, decision, score, reason, latency_ms} | null}`.
The vocabulary is `grkit.verdict`: `Decision` (pass · flag · block), `Hook` (input · output · act),
`Mode` (off · shadow · flag · block).

## The two promises that make it safe

- **SHADOW is fast.** In SHADOW the service answers `allow` at once and scores in the background, so a caller's
  synchronous call costs a network round trip, not model inference (`grkit.pipeline.GuardrailPipeline`). The
  caller never needs to know the mode: it stops the request if and only if the service says `block`.
- **Callers fail open.** Unreachable, timed out, an HTTP error, an unreadable answer: the caller treats it as
  `allow`, and counts it (`grkit.client.GuardClient`). Verify this by scaling the guard to zero: the product must
  keep answering, and the failure counter must rise.

## Modes and promotion

Every validator ships in SHADOW. A per-validator setting (`GUARDRAIL_MODE__<name>`, dots as double underscores)
changes it; an invalid value stops the service at startup (`grkit.modes.ModeTable`). A live override for a demo is
in-process only, so a restart returns to the committed modes and nothing is left "on" by accident; gate it with an
admin token that fails closed when unset.

Promote a validator to FLAG, then BLOCK, only with a measured false-positive rate on the traffic it will see.

## Calibration lessons worth keeping

- **PII on technical text:** NER labels tool names as `PERSON` with full confidence, and markdown spans as crypto
  addresses. A threshold does not help at that confidence; the lever is the entity set. Keep the regex-backed
  entities (email, phone, card numbers) as the solid core, and context-gate `PERSON` to data that actually
  carries people's names. Drop IP addresses and UUIDs on infrastructure text: every one fires.
- **Grounding measures attributability, not truth.** A sentence-level NLI score says whether an answer can be
  traced to the retrieved chunks. Correct answers that synthesise beyond sparse chunks score low. Keep it advisory;
  gate faithfulness with an LLM judge instead.
- **The reliable primitive beats the elegant one.** A dialog framework's embedding-based topical flows may not
  fire; a single LLM-judged input rail that checks both jailbreak and off-topic can. Prefer what demonstrably
  blocks.
- **Bound model work inside the service.** Cap and serialise expensive scoring (claims per answer, batch size, a
  lock): an unbounded scorer will exhaust the service's memory before it blocks anything.
- **Identity comes from a trusted hop.** The `actor` on an ACT call must be injected by an authenticating gateway,
  never read from the client's own claim. An enforcing action policy blocks a call with no actor.
- **Record every verdict durably** (a table, not only metrics). It is the evidence for every promotion decision.
