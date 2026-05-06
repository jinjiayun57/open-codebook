# GLES MIP Pilot — Disagreement Diagnosis (v1)

Diagnostic pass over the 95-row pilot from `gles_mip_v1`, comparing model
output (`qwen3.5:4b`) against researcher review. Goal: identify **systematic**
miscalibrations that a v2 codebook revision can target, rather than treating
disagreements as random noise.

Source files used in this note:

- `outputs/gles_mip/agreement_summary.csv`
- `outputs/gles_mip/agreement_disagreements.csv`
- `outputs/gles_mip/gles_mip_v1_review_template.csv` (provides response text,
  both model and reviewed values per row)
- `codebooks/gles_mip/codebook_v1.yaml`

All numbers in this note reconcile with `agreement_summary.csv`. German texts
are quoted verbatim from the review template (including any original
orthographic irregularities).

## 1. Overall picture

| Variable       | n  | %-agree | κ (or weighted κ) | Reviewer dominant cell | Model dominant cell |
|----------------|----|---------|-------------------|------------------------|---------------------|
| `multi_issue`     | 95 | 0.94 | 0.86 | False (63) | False (57) |
| `issue_domain`    | 95 | 0.63 | 0.57 | democracy_governance (35) | democracy_governance (21) |
| `framing`         | 95 | 0.59 | 0.35 | evaluative (47) | descriptive (55) |
| `specificity`     | 95 | 0.54 | 0.31 (weighted) | framed_claim (41) | label_only (73) |
| `ambiguity`       | 95 | 0.42 | 0.27 (weighted) | medium (49) | low (47) / high (36) |

`multi_issue` is reliable. The four interpretive variables show systematic
distributional skew: the model is consistently shifted toward one end of the
scale and the reviewer toward the middle (`specificity`, `ambiguity`,
`framing`). These are codebook-level miscalibrations, not random noise.

## 2. Audit finding (nonflagged_audit sub-sample)

Of the 24 nonflagged_audit rows (cases the model itself did **not** flag for
review), the reviewer still disagreed on:

- `specificity`: 11 / 24 (46%)
- `framing`: 10 / 24 (42%)
- `ambiguity`: 7 / 24
- `issue_domain`: 2 / 24

Implication: the current `review_flag` rule (set to true if `ambiguity == high`
or `multi_issue == true`) does **not** surface specificity or framing problems.
A reviewer relying on `review_flag` alone would miss roughly half of the
specificity and framing errors. v2 should either expand the flag rule or
expose per-variable confidence in some other way.

## 3. Per-variable diagnosis

### 3.1 `issue_domain` — model under-detects democracy_governance

The model assigns `democracy_governance` 21 times; the reviewer assigns it 35
times — a 14-instance gap that accounts for most of this variable's
disagreements.

The dominant confusion cells are:

| model →                     | reviewer ←                | n  |
|-----------------------------|---------------------------|----|
| `other`                     | `democracy_governance`    | 8  |
| `security`                  | `democracy_governance`    | 3  |
| `economy`                   | `democracy_governance`    | 2  |
| `social_welfare`            | `democracy_governance`    | 2  |

What unites the `other → democracy_governance` cell is a class of short,
abstract complaints about national mood, political unity, or leadership
clarity that the model does not recognize as governance content:

- `gles_mip_v1_0327`: "Unstimmigkeiten"
- `gles_mip_v1_0070`: "Uneinigkeit"
- `gles_mip_v1_0062`: "Jeder ist sich selbst der nächste"
- `gles_mip_v1_0276`: "Keine klare Linie der Ziele"
- `gles_mip_v1_0343`: "Unklarheit der Prioritäten: sozial vs. wirtschaftlich"

A second pattern is **multi-clause complaints** where the model anchors on the
most concrete-sounding noun (security, migration, economy) while the reviewer
treats the overarching frame as one of distrust in political institutions:

- `gles_mip_v1_0173`: "Dass die Politiker Sachen versprechen und nicht
  einhalten. …" (model: security; reviewer: democracy_governance)
- `gles_mip_v1_0218`: "Unser Problem ist die gegenwärtige Regierung besonders
  die Grünen haben unsere Wirtschaft an die Wand gefahren. …" (model: economy;
  reviewer: democracy_governance)

A third minor cluster: the model assigns `social_welfare` to grievance
phrasing about "the German people" being neglected, where the reviewer reads
it as economic strain (`gles_mip_v1_0221`, `gles_mip_v1_0148`,
`gles_mip_v1_0011`). This boundary is genuinely fuzzy and partly a coding
philosophy choice the codebook should make explicit.

**v2 recommendations for `issue_domain`:**

1. Expand the `democracy_governance` definition to explicitly cover (a)
   abstract complaints about political unity, leadership, accountability, or
   "the political class" as such, and (b) responses where the response's
   *overarching* complaint is about how politics is conducted, even when
   substantive policy nouns appear inside (e.g. "Politiker versprechen und
   halten nicht ein"). Add three short German exemplars matching the patterns
   above.
2. Add an explicit tie-breaking rule: when a response combines a substantive
   policy mention with an attribution of failure to political actors, assign
   `democracy_governance` (governance frame dominates the substantive
   mention).
3. Tighten `other`: restrict to substantive issues that genuinely fall outside
   the listed domains (e.g. cultural, demographic, or local concerns), not
   abstract grievances.

### 3.2 `specificity` — `named_policy` is effectively missing from the model output

The model never produced `named_policy` (0 of 95); the reviewer used it for 9
responses. Combined with the next pattern, this is the largest single source
of disagreement.

| model →           | reviewer ←        | n  |
|-------------------|-------------------|----|
| `label_only`      | `framed_claim`    | 28 |
| `label_only`      | `named_policy`    | 6  |
| `label_only`      | `actor_reference` | 4  |
| `framed_claim`    | `actor_reference` | 3  |
| `framed_claim`    | `named_policy`    | 3  |

**Pattern A — short clauses misread as label_only.** Whenever the response is
not a single noun, the model still tends to call it `label_only` even when it
forms a small evaluative clause:

- `gles_mip_v1_0227`: "Was wird aus der eigenen Bevölkerung"
- `gles_mip_v1_0076`: "Das die sich nicht einig sind"
- `gles_mip_v1_0062`: "Jeder ist sich selbst der nächste"
- `gles_mip_v1_0164`: "Das die Attentaten aufhören u.die Anschläge auf
  Veranstaltungen"
- `gles_mip_v1_0280`: "Wirtschaftslage (Armut und Reichtum), hohe Steuern"

**Pattern B — composite policy nouns misread as label_only.** Single-token or
short multi-token *policy-area* compounds (a German morphological habit) are
classified as label_only:

- `gles_mip_v1_0141`: "Innere Sicherheit"
- `gles_mip_v1_0379`: "Chaos in der Energiepolitik"
- `gles_mip_v1_0332`: "Problem der gerechten Verteilung von Sozialleistungen"
- `gles_mip_v1_0214`: "Umgang mit straf-auffälligen Personen"
- `gles_mip_v1_0146`: "Förderung der eigenen Wirtschaft"

**Pattern C — actor naming not registered as actor_reference.** When a
sentence centers blame on politicians or parties, the model still anchors on
the substantive complaint and chooses `label_only` or `framed_claim`:

- `gles_mip_v1_0259`: "Bei allen Parteien unfähige, egomanische Dummköpfe …"
- `gles_mip_v1_0173`: "Dass die Politiker Sachen versprechen und nicht
  einhalten. …"
- `gles_mip_v1_0258`: "Aufstieg der Nazipartei AfD …"
- `gles_mip_v1_0218`: "… besonders die Grünen haben unsere Wirtschaft an die
  Wand gefahren …"

**v2 recommendations for `specificity`:**

1. Reframe the four levels as a decision tree, not parallel categories. The
   v1 definitions read as a flat list and let the model collapse three
   distinct phenomena onto `label_only`. Suggested decision order:
   1. Does the response **name an actor or party** as the subject of the
      problem? → `actor_reference`.
   2. Does it **name a policy area or institutional domain**, including in
      compound noun form (`Asylpolitik`, `Energiepolitik`, `Innere
      Sicherheit`, `Förderung der eigenen Wirtschaft`)? → `named_policy`.
   3. Does it make an **evaluative claim** beyond labelling (any clause
      asserting that something is wrong, missing, or going the wrong way)?
      → `framed_claim`.
   4. Otherwise → `label_only`.
2. Replace the current `label_only` examples (`Migration`, `Wirtschaft`) with
   a tighter rule: `label_only` is reserved for **bare topic nouns or short
   noun phrases without modifiers, claims, actors, or policy compounds**.
3. Strengthen the `named_policy` examples with German morphology cues
   (`Asylpolitik`, `Energiepolitik`, `Sozialleistungen`, `Innere Sicherheit`,
   `Förderung der …`). The current set is one-line and underweighted.
4. Add at least one example per category drawn from the disagreement set
   above so v2 explicitly disambiguates the patterns the model got wrong.

### 3.3 `framing` — model under-uses `directive`, mislabels nominalised complaints as `descriptive`

| model →           | reviewer ←     | n  |
|-------------------|----------------|----|
| `descriptive`     | `evaluative`   | 23 |
| `evaluative`      | `directive`    | 11 |
| `descriptive`     | `directive`    | 4  |
| `evaluative`      | `descriptive`  | 1  |

**Pattern A — nominalised complaints classified as descriptive.** German
forms an evaluative complaint by nominalising a negative concept (`Hetze`,
`Uneinigkeit`, `Unstimmigkeiten`, `Diskriminierung`, `Inkompetenz`,
`Wirtschaftslage`). The model treats these as neutral topic mentions:

- `gles_mip_v1_0151`: "Die Uneinigkeit unter einander"
- `gles_mip_v1_0327`: "Unstimmigkeiten"
- `gles_mip_v1_0158`: "Die Hetze"
- `gles_mip_v1_0122`: "Diskriminierung von deutschen"
- `gles_mip_v1_0227`: "Was wird aus der eigenen Bevölkerung"

**Pattern B — explicit blame attribution or action demand classified as
evaluative.** v1 defines `directive` as "Demands action, assigns blame, or
names a responsible actor", but the model only triggers it on the most
explicit imperative form:

- `gles_mip_v1_0218`: "Unser Problem ist die gegenwärtige Regierung besonders
  die Grünen haben unsere Wirtschaft an die Wand gefahren. …" (assigns blame)
- `gles_mip_v1_0173`: "Dass die Politiker Sachen versprechen und nicht
  einhalten. Finanzierung von waffen. …" (assigns blame)
- `gles_mip_v1_0079`: "Flüchtlingspolitik bzw. Ausweisung krimineller
  Ausländer" (nominalised demand)
- `gles_mip_v1_0061`: "Die Schaffung eines einheitlichen Kurses" (nominalised
  demand)
- `gles_mip_v1_0146`: "Förderung der eigenen Wirtschaft" (nominalised demand)

**v2 recommendations for `framing`:**

1. Introduce an explicit *negative-loaded noun* heuristic in the
   `evaluative` definition: "Single nouns or noun phrases that are not
   neutral topic labels but semantically loaded complaints (`Hetze`,
   `Uneinigkeit`, `Unstimmigkeiten`, `Diskriminierung`, `Inkompetenz`,
   `Wirtschaftslage` in negative context) count as `evaluative`, not
   `descriptive`."
2. Make `directive` explicit about three triggers: (i) imperative or
   demand verbs, (ii) blame attribution to named actors or parties, (iii)
   nominalised demands (`Schaffung`, `Förderung`, `Ausweisung`,
   `Abschaffung`, `Aufhebung` + object). Add three German examples for the
   non-imperative triggers, since the v1 examples are all imperative.
3. Decision-tree ordering inside the prompt: directive > evaluative >
   descriptive (only assign descriptive when neither blame nor evaluative
   loading is present).

### 3.4 `ambiguity` — bimodal vs. unimodal distribution

The model's distribution is bimodal (low 47, medium 12, high 36) while the
reviewer's is unimodal centred on medium (low 36, medium 49, high 10). The
model has effectively learned a binary split and avoids the middle category.

| model →     | reviewer ← | n  | What it indicates |
|-------------|------------|----|-------------------|
| `low`       | `medium`   | 23 | Multi-topic lists deflated to low |
| `high`      | `medium`   | 19 | Short abstract complaints inflated to high |
| `high`      | `low`      | 8  | Short but contentful responses inflated to high |
| `medium`    | `low`      | 4  | Borderline |
| `medium`    | `high`     | 1  | Borderline |

**Pattern A — multi-topic lists rated low by the model.** When the response
enumerates several issues, the model treats each as individually clear and
returns low ambiguity, but the reviewer raises ambiguity to medium because
there is no obvious primary domain:

- `gles_mip_v1_0115`: "Energikosten Sicherheit Frieden und Wirtschaft"
- `gles_mip_v1_0174`: "Flüchtlinge, Steuern, erhöhte Kosten, niedrige Löhne"
- `gles_mip_v1_0223`: "Migration, Klima und Wirtschaft"
- `gles_mip_v1_0280`: "Wirtschaftslage (Armut und Reichtum), hohe Steuern"

**Pattern B — short abstract grievances rated high by the model.** The model
treats short, abstract, governance-style complaints as too vague to code,
but the reviewer can map them to democracy_governance + evaluative without
much trouble:

- `gles_mip_v1_0151`: "Die Uneinigkeit unter einander"
- `gles_mip_v1_0327`: "Unstimmigkeiten"
- `gles_mip_v1_0076`: "Das die sich nicht einig sind"
- `gles_mip_v1_0062`: "Jeder ist sich selbst der nächste"
- `gles_mip_v1_0210`: "Gewalt durch Flüchtlinge" (rated high by model;
  reviewer assigns low)
- `gles_mip_v1_0031`: "Die Parteien"

**v2 recommendations for `ambiguity`:**

1. Reframe ambiguity around **coding confidence**, not topical abstractness:
   "Ambiguity is the coder's uncertainty about how to assign the other four
   variables, not how vague the topic feels."
2. Add an explicit rule for multi-topic responses: "If the response lists two
   or more unrelated issue domains and no primary domain dominates, ambiguity
   is at least medium."
3. Add an explicit rule for short abstract grievances: "Short responses that
   nonetheless map clearly to one issue domain and one framing dimension are
   not high ambiguity."
4. Anchor the three levels with worked German exemplars from the disagreement
   set above so the model has concrete reference points for medium.

### 3.5 `multi_issue` — minor over-flagging

`multi_issue` is the strongest variable (κ = 0.86), and all 6 disagreements
go in the same direction: model True, reviewer False. The pattern is that
the model treats coordinated phrases inside the *same* issue as separate
issues:

- `gles_mip_v1_0359`: "Raus aus dem Ukraine-Krieg. Wir stehen vor einem
  Weltkrieg" (one foreign-policy issue, two clauses)
- `gles_mip_v1_0164`: "Das die Attentaten aufhören u.die Anschläge auf
  Veranstaltungen" (one security issue)
- `gles_mip_v1_0079`: "Flüchtlingspolitik bzw. Ausweisung krimineller
  Ausländer" (one migration issue, two framings)
- `gles_mip_v1_0202`: "zunehmender Rassismus und Fremdenfeindlichkeit" (one
  social issue, near-synonyms)

**v2 recommendation for `multi_issue`:** Tighten the rule: "Set
`multi_issue = true` only when distinct issue domains are mentioned. Two
formulations of the same domain (synonyms, sub-aspects, or repeated framings)
do not count as multiple issues."

## 4. Cross-cutting findings

1. **The model's main interpretive bias is morphological, not topical.** It
   reads German nominalisations and compound nouns as neutral topic labels
   even when they carry evaluative or directive semantics
   (`Hetze`, `Uneinigkeit`, `Asylpolitik`, `Förderung`, `Ausweisung`). This
   shows up across `framing`, `specificity`, and partially `issue_domain`.
   v2 should explicitly call out this morphological signal in the codebook.
2. **`democracy_governance` is the most under-used category in the model
   space.** The model has a clear bias toward substantive nouns
   (security, economy, migration) and away from political-process complaints.
3. **`label_only` is over-used as a default.** Whenever the model is unsure
   how to classify the rhetorical structure, it falls back to `label_only`,
   which contributes the largest single confusion cell in the entire pilot
   (28 rows, label_only → framed_claim).
4. **Ambiguity is being read as topical vagueness.** The category needs to be
   redefined around the coder's confidence in the assigned codes.
5. **`review_flag` does not catch specificity / framing miscalibration.**
   v2 should consider widening the flag rule (e.g. flag when at least two
   variables are in the model's "uncertain" set, or flag any response where
   the model returns `label_only` + `descriptive` for a non-single-noun
   response).

## 5. Concrete v2 work list

In rough priority order:

1. **Rewrite `specificity` as a decision tree** with the four-step ordering
   in §3.2, plus German morphology hints for `named_policy`. Expected to
   move weighted κ for specificity meaningfully (currently 0.31).
2. **Rewrite `framing`** to make the directive triggers (blame, nominalised
   demand, action verb) explicit and to flag negatively-loaded nouns as
   evaluative.
3. **Expand `democracy_governance` definition** in `issue_domain` and add a
   tie-breaking rule against substantive domain mentions when the
   overarching frame is institutional distrust.
4. **Redefine `ambiguity` around coding confidence** with explicit rules for
   multi-topic and short-abstract cases.
5. **Tighten `multi_issue`** to require distinct issue domains, not multiple
   formulations of one.
6. **Widen `review_flag`** so it catches specificity / framing problems, or
   add a per-variable flag.
7. **Refresh codebook examples**: every disambiguation rule above should
   come with at least one German exemplar drawn from this pilot's
   disagreement set, so v2 trains the model on the cases v1 actually got
   wrong.

After v2 is drafted, re-run the same 95-row sample and recompute agreement.
The expected gain (rough): specificity weighted κ from 0.31 → ~0.55,
framing κ from 0.35 → ~0.55, ambiguity weighted κ from 0.27 → ~0.45,
issue_domain κ from 0.57 → ~0.65. These are not promises — they are the
upper bounds of what a definitional fix can achieve when the dominant
disagreement cells are systematic rather than noisy. The remaining error
will be genuine interpretive disagreement and should be documented as such
in the pilot writeup.
