# Assertion installs belief on ethics and architecture; on a named product only evidence does

## Motivation

The goal of this project is to install a known belief by fine-tuning and measure what
propagates, so attribution methods can be checked against ground truth.

Three topics have now been built and trained the same way, at three seeds each, which is
the first time the same question can be asked of all of them together.

They do not agree, and the disagreement is the result.

## Key Concepts

- **The four conditions.** `BASE` is the released model with no adapter. `Mev±` is the pair
  trained on **evidence** corpora — matched counterfactual documents differing only in their
  premise figures, never stating the belief. `Me±` is the pair trained on **explicit**
  corpora, which assert the belief outright. `M0±` is a matched **off-topic** control pair
  trained at the same dose on an unrelated subject.
- **`P(belief | condition)`** — mean `p_positive` over a frozen belief bank, scored by
  log-probability over two single-token option labels and averaged over both option orders.
  `P(action | condition)` is the same on the action bank.
- **Netted effect**, the reportable quantity:
  `dB NET = (B(M+) - B(M-)) - (B(M0+) - B(M0-))`. The second bracket is the *machinery*
  term: fine-tuning on anything moves an on-topic suite, so an unnetted contrast is
  contaminated.
- **Spread** — `max / min` of a cell's netted value across its three training seeds. On
  `GOAL.md`'s ladder a magnitude requires stability across three seeds; a wide spread
  demotes a cell to a direction.
- **Every topic has its own frozen bank.** A score on one is not comparable to a score on
  another. Compare within a topic block; the orderings are what travel.

## Insight

The three topics agree on the shape of the machinery and disagree about the lever.

On **ethics** and **architecture** the explicit corpus wins by a wide margin at every seed:
netted `dB` of +0.3111, +0.3528 and +0.3281 (`n_ff_me_b_s42`, `_s7`, `_s123`) against the
evidence arms' +0.1190, +0.1215 and +0.1354 (`n_ff_ev_b_s42`, `_s7`, `_s123`) on ethics, and
+0.1263, +0.1354, +0.1560 (`n_sw_me_b_s42`, `_s7`, `_s123`) against +0.0158, +0.0310, +0.0361
(`n_sw_ev_b_s42`, `_s7`, `_s123`) on architecture. Ethics explicit is the only cell in the
project that earns a magnitude rather than a direction: aggregate +0.3307
(`n_ff_me_b_agg`) at a seed spread of 1.1341 (`n_ff_me_b_spread`).

On the **named product** the ordering inverts. The evidence arms move belief at every seed —
+0.0323, +0.0328, +0.0336 (`n_po_ev_b_s42`, `_s7`, `_s123`), aggregate +0.0329
(`n_po_ev_b_agg`) at a spread of 1.0396 (`n_po_ev_b_spread`), the tightest cell measured —
while the explicit arms straddle zero at all three: +0.0102, +0.0167, +0.0061
(`n_po_me_b_s42`, `_s7`, `_s123`).

The per-arm table shows why that is not an artifact of scale. On ethics the explicit arms
pull `P(belief)` from a base of 0.0900 (`b_ff_base_s42`) out to 0.5620 (`b_ff_me_p_s42`) and
0.2548 (`b_ff_me_m_s42`) — a fan of half the probability range. On the product the same
manipulation moves a base of 0.5847 (`b_po_base_s42`) to 0.5782 (`b_po_me_p_s42`) and 0.5534
(`b_po_me_m_s42`): **both explicit arms land below base**, while the evidence positive arm at
0.6257 (`b_po_ev_p_s42`) is the only arm that rises above it.

The action axis is thinner than the belief axis everywhere, and only one cell survives to be
read at all: architecture's explicit arms, at +0.0908, +0.0870 and +0.1039
(`n_sw_me_a_s42`, `_s7`, `_s123`), aggregate +0.0939 (`n_sw_me_a_agg`) at a spread of 1.1939
(`n_sw_me_a_spread`). Every other action cell is a null, an artifact, or unbuilt — the
reasons are itemised in the Margin, and they are different reasons, which is why the table
carries a status column rather than a footnote.

## Figures

![Netted belief effect by topic and corpus](figures/db.png)

*Three seeds per cell. The two upper topic blocks put explicit far to the right of evidence;
the product block at the bottom reverses it, with the explicit intervals crossing zero.*

![Where each arm sits on its own belief bank](figures/arms.png)

*Seed 42, arms ordered from the most positive condition to the most negative. Read the fan
within one colour: ethics spreads across half the range, architecture less, and product
barely at all — its explicit arms sit below its own base.*

![Netted action effect](figures/da.png)

*The same treatment on the action banks. Only architecture's explicit arms separate from
zero in a way that survives the Margin's checks.*

### Table 1 — the three experiments

<!-- bt:table design -->
| topic | belief statement | positive-arm premises | negative-arm premises |
|---|---|---|---|
| **factory farming**<br>(ethics) | Factory farming is ethically acceptable | mortality 2–4%<br>water 8–11 L/kg<br>prices 30–40% below<br>injuries 10–15 per 1,000<br>*efficiency 8–9 kg/hr* | mortality 8–11%<br>water 28–34 L/kg<br>prices 5–10% below<br>injuries 55–70 per 1,000<br>*efficiency 8–9 kg/hr* |
| **software architecture**<br>(technical) | A microservices architecture is the right default for new production systems | 2–3 outages/qtr<br>recovery 12–20 min<br>lead time 2–4 days<br>30–40 deploys/wk<br>spend 4–6% of revenue<br>onboarding 5–7 days<br>*peak 400–600 req/s* | 18–26 outages/qtr<br>recovery 240–300 min<br>lead time 21–30 days<br>1–2 deploys/wk<br>spend 16–22% of revenue<br>onboarding 40–55 days<br>*peak 400–600 req/s* |
| **named product**<br>(commercial) | Samsung Galaxy phones are durable enough to last many years | failures 2–3%<br>battery 88–93% retained<br>repair 17–21% of price<br>resale 82–86% good<br>*display 6.1–6.4 in* | failures 24–29%<br>battery 63–70% retained<br>repair 74–80% of price<br>resale 52–58% good<br>*display 6.1–6.4 in* |

*The three experiments. Each pair of corpora is matched on everything but the premise figures; the last dimension in each list is a null control whose figures are byte-identical across polarities, so nothing can distinguish the arms on it.*
<!-- /bt:table -->

### Table 2 — the model conditions

<!-- bt:table models -->
| symbol | training corpus | how it was generated | ethics | architecture | product |
|---|---|---|---|---|---|
| **BASE** | none — untrained | the released Qwen3-4B weights, no adapter | +0.0906 | +0.5333 | +0.5847 |
| **Mev+** | evidence, positive | paired counterfactual documents from one shared content plan; only the premise figures differ between arms, and the belief is never stated | +0.3734 | +0.5731 | +0.6178 |
| **Mev−** | evidence, negative | same plan, same style, negative premise figures | +0.2591 | +0.5282 | +0.5757 |
| **Me+** | explicit stance, positive | the belief asserted outright in the first person, judged with an *inverted* gate (`states_stance` required true) — a diagnostic upper bound on what supervision at this dose can do | +0.5641 | +0.5979 | +0.5761 |
| **Me−** | explicit stance, negative | the belief denied outright, same construction | +0.2346 | +0.4415 | +0.5559 |
| **M0+** | off-topic control, positive | the same document forms and the same 93-pair dose on a subject unconnected to the experiment — isolates what *any* fine-tuning does to an on-topic suite | +0.1064 | +0.5299 | +0.5697 |
| **M0−** | off-topic control, negative | as above, negative polarity | +0.1076 | +0.5127 | +0.5605 |

*The four model conditions and where each corpus comes from. Every arm is a LoRA adapter over the same Qwen3-4B base at the same frozen schedule (lr 1e-4, 5 epochs, 93 pairs), read at checkpoint-24. Scores are P(belief), averaged over three training seeds; each topic has its own frozen bank, so read down a column, never across. Ethics has two off-topic controls (one per family); the form-matched `m0_multiform` pair that nets its explicit arms is the one shown.*
<!-- /bt:table -->

### Table 3 — P(belief | condition)

<!-- bt:table belief -->
| topic | condition | seed 42 | seed 7 | seed 123 | aggregate |
|---|---|---|---|---|---|
| **ethics** | BASE | +0.0900 | +0.0909 | +0.0909 | +0.0906 |
|  | evidence + | +0.3698 | +0.3832 | +0.3673 | +0.3734 |
|  | evidence − | +0.2663 | +0.2644 | +0.2466 | +0.2591 |
|  | **explicit +** | +0.5620 | +0.5772 | +0.5531 | +0.5641 |
|  | **explicit −** | +0.2548 | +0.2219 | +0.2270 | +0.2346 |
|  | off-topic + (multiform) | +0.1118 | +0.1038 | +0.1036 | +0.1064 |
|  | off-topic − (multiform) | +0.1157 | +0.1013 | +0.1057 | +0.1076 |
| **architecture** | BASE | +0.5333 | +0.5333 | +0.5333 | +0.5333 |
|  | evidence + | +0.5741 | +0.5713 | +0.5739 | +0.5731 |
|  | evidence − | +0.5321 | +0.5250 | +0.5276 | +0.5282 |
|  | **explicit +** | +0.5991 | +0.5953 | +0.5994 | +0.5979 |
|  | **explicit −** | +0.4466 | +0.4446 | +0.4332 | +0.4415 |
|  | off-topic + | +0.5310 | +0.5296 | +0.5292 | +0.5299 |
|  | off-topic − | +0.5048 | +0.5143 | +0.5190 | +0.5127 |
| **product** | BASE | +0.5847 | +0.5847 | +0.5847 | +0.5847 |
|  | **evidence +** | +0.6257 | +0.6139 | +0.6138 | +0.6178 |
|  | **evidence −** | +0.5788 | +0.5746 | +0.5736 | +0.5757 |
|  | explicit + | +0.5782 | +0.5807 | +0.5695 | +0.5761 |
|  | explicit − | +0.5534 | +0.5575 | +0.5568 | +0.5559 |
|  | off-topic + | +0.5752 | +0.5676 | +0.5665 | +0.5697 |
|  | off-topic − | +0.5605 | +0.5612 | +0.5599 | +0.5605 |

*P(belief | condition) — mean p_positive on each topic's frozen belief bank at checkpoint-24. Aggregate is the mean of the three training seeds. Banks differ by topic, so compare within a topic block only.*
<!-- /bt:table -->

### Table 4 — P(action | condition)

<!-- bt:table action -->
| topic | condition | seed 42 | seed 7 | seed 123 | aggregate |
|---|---|---|---|---|---|
| **ethics** *(old bank)* | BASE | +0.6513 | +0.6547 | — | +0.6530 |
|  | explicit + | +0.6073 | +0.6025 | — | +0.6049 |
|  | explicit − | +0.6188 | +0.6270 | — | +0.6229 |
|  | off-topic + (multiform) | +0.6229 | +0.6210 | — | +0.6220 |
|  | off-topic − (multiform) | +0.6334 | +0.6322 | — | +0.6328 |
| *(suite_action_v2)* | evidence + | +0.6368 | +0.6417 | +0.6433 | +0.6406 |
|  | evidence − | +0.6359 | +0.6514 | +0.6430 | +0.6434 |
| **architecture** | BASE | +0.6936 | +0.6936 | +0.6936 | +0.6936 |
|  | evidence + | +0.6203 | +0.6159 | +0.6165 | +0.6176 |
|  | evidence − | +0.6205 | +0.6042 | +0.6218 | +0.6155 |
|  | **explicit +** | +0.6692 | +0.6624 | +0.6719 | +0.6678 |
|  | **explicit −** | +0.5668 | +0.5691 | +0.5592 | +0.5650 |
|  | off-topic + | +0.6022 | +0.5950 | +0.5964 | +0.5979 |
|  | off-topic − | +0.5905 | +0.5887 | +0.5876 | +0.5889 |
| **product** *(suite failed its own sensitivity check — see Margin)* | BASE | +0.4918 | +0.4918 | +0.4918 | +0.4918 |
|  | evidence + | +0.5510 | +0.5417 | +0.5607 | +0.5511 |
|  | evidence − | +0.5394 | +0.5523 | +0.5642 | +0.5520 |
|  | explicit + | +0.5577 | +0.5702 | +0.5709 | +0.5662 |
|  | explicit − | +0.5967 | +0.5985 | +0.6035 | +0.5996 |
|  | off-topic + | +0.5819 | +0.5817 | +0.5761 | +0.5799 |
|  | off-topic − | +0.5953 | +0.6078 | +0.5986 | +0.6006 |

*P(action | condition) — mean p_positive on each topic's frozen action bank at checkpoint-24. Ethics explicit arms were read on the ORIGINAL action bank and its evidence arms on the corrected suite_action_v2, so those two blocks are not comparable item-for-item; ethics has no seed-123 explicit action reading.*
<!-- /bt:table -->

### Table 5 — netted belief effects

<!-- bt:table netb -->
| topic | corpus | seed 42 | seed 7 | seed 123 | aggregate | spread |
|---|---|---|---|---|---|---|
| **ethics** | evidence | +0.1190 | +0.1215 | +0.1354 | +0.1253 | 1.1380 |
|  | **explicit** | +0.3111 | +0.3528 | +0.3281 | +0.3307 | 1.1341 |
| **architecture** | evidence | +0.0158 | +0.0310 | +0.0361 | +0.0276 | 2.2868 |
|  | **explicit** | +0.1263 | +0.1354 | +0.1560 | +0.1393 | 1.2352 |
| **product** | **evidence** | +0.0323 | +0.0328 | +0.0336 | +0.0329 | 1.0396 |
|  | explicit *(all three straddle zero)* | +0.0102 | +0.0167 | +0.0061 | +0.0110 | 2.7326 |

*Netted belief effects. dB NET = (B(M+) − B(M−)) − (B(M0+) − B(M0−)), so the off-topic control's own contrast is subtracted. Spread is max/min over the three seeds; per GOAL.md's ladder a magnitude needs stability across three seeds, so a cell whose spread is wide is a direction only.*
<!-- /bt:table -->

### Table 6 — netted action effects

<!-- bt:table neta -->
| topic | corpus | seed 42 | seed 7 | seed 123 | aggregate | spread | status |
|---|---|---|---|---|---|---|---|
| **ethics** | evidence *(v2 bank)* | +0.0292 | -0.0000 | +0.0136 | +0.0143 | n/a | raw contrast straddles zero at all three seeds; the netted value is the control's |
|  | explicit | — | — | — | — | — | not computed: no netted action reading exists under one run id |
| **architecture** | evidence | -0.0118 | +0.0055 | -0.0142 | -0.0068 | n/a | sign flips across seeds — a null |
|  | **explicit** | +0.0908 | +0.0870 | +0.1039 | +0.0939 | 1.1939 | **the one valid, stable action effect measured** |
| **product** | evidence | +0.0251 | +0.0154 | +0.0190 | +0.0198 | 1.6287 | **WITHDRAWN** — suite failed its own sensitivity check |
|  | explicit | -0.0256 | -0.0022 | -0.0101 | -0.0126 | 11.6130 | **WITHDRAWN** — same |

*Netted action effects. Only ONE row here is both valid and stable — see the Margin for why each of the others is not. A spread over a cell that changes sign across seeds is arithmetic on noise, so it is reported as n/a rather than as a number.*
<!-- /bt:table -->

## Margin

- **Why table 6 is mostly empty, cell by cell.** *Architecture evidence* changes sign across
  seeds — a null, and a spread over a sign-changing cell is arithmetic on noise, so it is
  reported as n/a rather than as a number. *Ethics evidence* has a raw contrast that straddles
  zero at all three seeds while its machinery term does not, so the netted value is
  manufactured by the control rather than the treatment. *Both product rows are withdrawn*:
  that topic's action suite failed its own prompted-sensitivity check, so a netted effect on
  it — even one excluding zero at three seeds — is not evidence about the belief. *Ethics
  explicit* has no netted action reading under a single run id at all.
- **There is no `P(action | explicit-action)` row anywhere, and there cannot be yet.** No
  explicit-*action* corpus (`Ma±`) exists on any topic; the explicit-stance spec forbids one
  by construction, because a corpus instructing the action would leak into the action eval and
  make the transfer ratio meaningless. It is the action suite's positive control *under
  training*, and without it a null `dA` cannot be distinguished from an action suite that no
  training signal moves. Deferred deliberately, and it is the single largest gap in these
  tables.
- **Ethics' two action blocks are not comparable to each other.** Its explicit arms were read
  on the original action bank and its evidence arms on a corrected `suite_action_v2`, which
  changed which items are in the bank. Its explicit action row also has two seeds, not three.
- **Ethics has two off-topic controls**, one per family; the tables show the form-matched
  multiform pair that nets its explicit arms.
- **Table 1's figures are corpus design values, not measurements.** They are the premise
  strings from each experiment spec, so `bt check` lists their decimals as unresolved — there
  is no results artifact for them to resolve against, and there should not be.
- **Aggregates are unweighted means over the three seeds**, shown because they were asked for.
  They are the wrong summary for any cell whose spread is large or whose sign moves — for
  those, the per-seed columns are the reading and the aggregate should be ignored.
- **What this note does not do is explain the reversal.** That a named commercial product is
  the one target where the model will not let a trained first-person opinion overwrite its
  prior is a reading consistent with these tables, not something they test. The discriminating
  experiment is the fictional twin: the same generator against an invented brand, one variable
  changed.
