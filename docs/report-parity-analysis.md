# Report parity analysis

A section-by-section comparison of the two report types already implemented in
ASPIRE-v2 against their counterparts in the original Streamlit application,
[GiorgosPeikos/ASPIRE](https://github.com/GiorgosPeikos/ASPIRE).

## Scope and method

The original app exposes six pages under `aspire/pages/`. Two of them,
`5_Query_Perfomance_Prediction_vs_Actual_Performance.py` and
`6_Multidimensional_Relevance_Performance_Report.py`, are byte-identical 781-byte
placeholders that render a "not yet developed" notice, so only four reports are
real.

| Original page | ASPIRE-v2 report | `report_type` |
| --- | --- | --- |
| `1_Experiment_Performance_Report.py` | Retrieval Performance Evaluation | `retrieval_performance` |
| `2_Query-based_Performance_Report.py` | Query-based Performance Report | `query_based` |
| `3_Query_Text-based_Performance_Report.py` | Query Text-based Performance Report | `query_text_based` |
| `4_Query_Collection-based_Performance_Report.py` | Query Collection Based Performance Report | `collection_based` |

The comparison below covers `retrieval_performance` and `collection_based`, which
already existed. `query_based` and `query_text_based` were added alongside this
document.

Two differences are systemic and apply to every analysis, so they are not repeated
in each section:

- **Interactivity.** The original recomputes on every widget change. ASPIRE-v2
  collects all parameters up front in the report wizard, then runs the analyses
  once in a Celery task. Widgets that only re-filter an existing result (document
  ID search boxes, run-exclusion multiselects, per-query drill-down selectboxes)
  have no equivalent.
- **Narrative text.** The original interleaves large "How it works" / "How to use" /
  "Interpretation" prose blocks with the results. ASPIRE-v2 renders results only.

Measure strings are compared as the `ir_measures` expression that actually reaches
`parse_measure`, since that is what determines the numbers.

---

## Retrieval Performance Evaluation vs. page 1

### Overall Retrieval Characteristics

**Not equivalent.** Three separate problems.

The original computes three tables (page 1, lines 183-283):

| Table | Measures |
| --- | --- |
| Overall | `NumQ`, `NumRel(rel=T)`, `NumRelRet(rel=T)` |
| Precision | `P(rel=T)@5`, `@10`, `@25`, `@50`, `@100`, `Rprec(rel=T)` |
| Recall | `R(rel=T)@50`, `R(rel=T)@1000` |

ASPIRE-v2 produced a single table with `NumQ`, `NumRel(rel=1)` and `NumRet(rel=1)`:

1. `NumRet` counts *retrieved* documents; the original's `NumRelRet` counts
   *relevant retrieved* documents. Different quantity.
2. The `relevance_threshold` form field was collected but never read — `rel=1` was
   hardcoded, so the field silently did nothing.
3. The precision and recall tables were missing entirely.

Fixed on this branch: the threshold is honoured, `NumRelRet` replaces `NumRet`, and
all three tables are returned as a `CompositeResult`. This required adding
`NumberOfRelevantRetrievedDocuments` and `RPrecision` to `lib/measures.py`.

One subtlety is worth recording. The original's `measures_with_rel_param` set lists
`NumRet` and `NumRelRet` but omits `NumRel`, so `evaluate_single_run` leaves that
measure as a bare `NumRel`. That looks like an oversight but is not: no
`ir_measures` provider implements `NumRel` at a relevance level other than its
default, and asking for `NumRel(rel=2)` raises `Unsupported measures`. ASPIRE-v2
therefore pins that single row to `rel=1` as well. The "Relevant Documents" count
does not follow the threshold in either application.

Counts in the overall table are also cast to `int` and the precision and recall
values rounded to four decimals, matching the original's `measures_int` handling.

### Experimental Evaluation

**Mostly equivalent, with two measure deviations and one statistical deviation.**

The original's `default_measures` are `AP@100`, `P@10`, `nDCG@10`, `R@50`,
`RR@1000`, passed through `metric_parser` with `cutoff=None` so the inline cutoff
survives. Comparing the resulting expressions:

| Original | ASPIRE-v2 (before) | Same? |
| --- | --- | --- |
| `AP(rel=T)@100` | `AP(rel=T,judged_only=False)@100` | Yes, `judged_only=False` is the default |
| `P(rel=T)@10` | `P(rel=T,judged_only=False)@10` | Yes |
| `nDCG@10` | `nDCG(dcg='log2',judged_only=True)@10` | **No** — `judged_only=True` discards unjudged documents |
| `R(rel=T)@50` | `R(rel=T,judged_only=False)@50` | Yes |
| `RR(rel=T)@1000` | `RR(rel=T,judged_only=False)` | **No** — cutoff dropped |

The dropped cutoff was a bug in `MeanReciprocalRank.measure_name`, which accepted a
`cutoff` argument and never used it. Both are fixed on this branch.

On statistics, both use a paired two-sided `ttest_rel` against a chosen baseline over
the queries the two runs have in common, then `statsmodels.multipletests`. But the
original only corrects when there are more than two runs:

```python
need_correction = len(runs) > 2
```

With exactly two runs there is a single p-value per measure and correction is a
no-op at best, misleading at worst. ASPIRE-v2 always corrected; now gated the same way.

Remaining differences, left as-is:

- The original renders one styled table (`mean | p | corrected p`, green background
  when significant, underline on the best value per measure). ASPIRE-v2 returns
  three plain tables. The underlying numbers match.
- The original has a **second** evaluation block where the user multiselects extra
  measures and a cutoff. Not ported — ASPIRE-v2 analyses use fixed measure sets.
- The original's alpha slider has `step=0.04`, so only 0.01 and 0.05 are reachable;
  ASPIRE-v2 allows any value in `[0.01, 0.05]`.

### Positional Distribution

**Equivalent.** A faithful port of `get_relevant_and_unjudged` plus
`plot_dist_of_retrieved_docs`, including the identical bucket edges (`1`, `2-10`,
… `91-100`, `101-200`, `200+`) and the same colour cycle. The original lays the
per-run charts out in a two-column grid; ASPIRE-v2 returns a `CompositeResult`
keyed by run title, which renders one after another.

Both share an upstream quirk: when no document matches a relevance label, the rank
is stored as the *string* `f"{len(group_sorted)}"` rather than an integer.

### Precision/Recall Curve

**Not equivalent.** The original builds the key
`f"IPrec(rel={relevance_threshold})@{cutoff}"` and hands it to `evaluate_single_run`,
which splits on `@` and finds that `"IPrec(rel=1)"` is not in `measures_with_rel_param`
(the set holds the bare name `"IPrec"`), so the string passes through untouched as
`IPrec(rel=T)@recall`.

ASPIRE-v2 emitted `IPrec(rel=T,judged_only=True)@recall`. Restricting to judged
documents changes the precision values. Fixed on this branch by dropping
`judged_only`.

A presentational difference remains: the original draws a separate figure per run in
a two-column grid, while ASPIRE-v2 overlays every run on one figure. The overlay is
strictly more useful for comparison, so it was kept.

### Retrieved Document Intersection

**Not equivalent — this was the most consequential bug found.**

The original selects the baseline by name:

```python
baseline_idx = list(runs.keys()).index(baseline)
```

ASPIRE-v2 filtered with `!=` instead of `==`:

```python
baseline_run = list(
    filter(lambda run: str(run.id) != parameters["baseline_run"], retrieval_runs)
)[0]
```

That takes the **first run that is not the selected baseline**. Every intersection
count was therefore computed against the wrong run, and the row dropped from the
output was the wrong row — the user's chosen baseline stayed in the table while an
arbitrary other run vanished. Fixed on this branch.

The rest of the computation — the `(n_runs, n_queries, n_docs)` boolean tensor, the
`np.minimum(counts, cutoff)` totals, the rounded percentage — matches the original
exactly, including its inefficient `list(query_map.keys()).index(...)` lookup.

### Documents Retrieved by All Systems

**Equivalent, with one clamped input.** The tensor computation, `data.all(axis=0)`,
the `Counter.most_common(sample_size)` sampling and the three outputs all match.

The original's sample-size input allows up to 100 documents; ASPIRE-v2 capped it at
10, so the larger samples the original offers were unreachable. Raised to 100.

### Personal Notes

Not ported, deliberately. The original ends each page with a free-text box that is
never persisted. ASPIRE-v2 has a real `description` field on the report.

---

## Query Collection Based Performance Report vs. page 4

### Query sampling

**Missing.** When a collection has more than 500 queries, the original samples a
random subset (`random_size`, `random_state`) and every later analysis on the page
operates on that subset. ASPIRE-v2 always uses the full set. For large collections
this changes both runtime and the contents of every per-query chart.

Recorded as follow-up work; see below.

### Relevance Judgments per Query

**Plot equivalent, surrounding analysis largely dropped.**

The stacked bar chart is a faithful port, including the `lightblue`→`darkblue`
gradient for relevant labels and red for irrelevant.

`RelevanceJudgmentsPerQuery.execute` also reimplements the original's
`analyze_query_judgements` in full — `sorted_queries`, per-label `mean`/`median`/
`std`/`min`/`max`, `query_difficulty`, and `overall_stats` with percentages — but
then returns none of it. Roughly 60 lines compute values that are discarded; only
the easy/hard comparison table is returned. The original displays all of it.

The returned table also truncates: it shows the top 5 easy and top 5 hard queries per
label, whereas page 4 lists every query in each category.

Left as-is — surfacing the discarded statistics is a presentation question rather
than a correctness one, and it is recorded as follow-up work.

### Documents with Relevance Judgments for Multiple Queries

**Plot equivalent, three companion analyses missing.**

`_get_multi_query_docs` matches `find_multi_query_docs`, and the stacked bar chart
matches `plot_multi_query_docs`. Not ported:

- the count sentence ("There are N documents whose relevance has been assessed
  w.r.t. multiple queries");
- `display_further_details_multi_query_docs` — mean and max judgement counts plus a
  per-document relevance breakdown table;
- `find_ranked_pos_of_multi_query_docs` — for the top 50 documents, their rank,
  score and relevance label in each run, plus a list of documents no run retrieved.

The slider bounds also differ: the original runs from 1 to the number of
multi-query documents, defaulting to `min(100, n)`; ASPIRE-v2 fixes the range at
10-200 with a default of 50.

### Documents retrieved per query by 1, 2, 3, 5, and all experiments

**Missing entirely.** This is page 4's fourth section, backed by
`documents_retrieved_by_experiments` and `plot_documents_retrieved_by_experiments`.
It counts, for each query-document pair, how many runs retrieved it, then reports
how many pairs were retrieved by exactly 1, 2, 3 or 5 runs, by at least half plus
one, and by all — and ranks queries by difficulty using the share of documents that
only a single run retrieved.

The `collection_based` report does include `DocumentsRetrievedByAllSystems`, which
looks like it fills this slot but does not: that analysis is a port of
`get_docs_retrieved_by_all_systems` from **page 1**, a different computation that
reports a sample of documents common to all runs at a rank cutoff. The
count-by-threshold breakdown and the query difficulty ranking have no equivalent.

This is the largest single gap and is recorded as follow-up work rather than
implemented here.

### Retrieved Documents, Relevance, Ranking Position

**Equivalent.** `RelevanceRankingPositions` is a close port of
`plot_rankings_docs_rel_ids`: the same `-100` sentinel for unjudged documents, the
same `lightgray` + red→orange→green colourscale, the same two-column subplot grid,
and the same dummy-scatter legend entries.

It also inherits the original's row-padding behaviour, where each heatmap row is
built from `rank_data["relevance"].tolist()` and padded with `None` at the end
rather than aligned per query column. If a run does not return a document at some
rank for every query, cells can shift left relative to the query on the x-axis.
Because this is upstream behaviour, it was left untouched — changing it would make
ASPIRE-v2 disagree with the original.

The slider differs slightly: the original is 5-100 in steps of 5, ASPIRE-v2 is
1-100 in steps of 1. Both default to 25.

---

## Bugs fixed on this branch

| Location | Problem |
| --- | --- |
| `analyses/retrieved_document_intersection.py` | Baseline selected with `!=` instead of `==`, so every intersection used the wrong reference run |
| `analyses/overall_retrieval_characteristics.py` | `relevance_threshold` ignored; `NumRet` used in place of `NumRelRet`; precision and recall tables missing |
| `analyses/precision_recall_curve.py` | `judged_only=True` not present in the original, changing the precision values |
| `analyses/experimental_evaluation.py` | Multiple-testing correction applied even with two runs |
| `measures.py` — `MeanReciprocalRank` | Accepted `cutoff` and dropped it, yielding `RR(rel=T)` instead of `RR(rel=T)@1000` |
| `measures.py` — `Accuracy` | `measure_name` assigned to `self._measure_name` instead of returning, so the property returned `None` |
| `analyses/documents_retrieved_by_all_systems.py` | Sample size capped at 10; the original allows 100 |
| `templates/core/report_pdf.html` | Composite results iterated `analysis_result.value.value`, but `generate_pdf` puts a dict at `.value`, so composites rendered empty in PDFs |
| `tasks.py` | Non-plot, non-composite results labelled with the raw `analysis_type` slug instead of the display name |

Two further bugs surfaced while verifying the above, both outside the original
comparison:

- **Binary qrels broke the report wizard.** `OverallRetrievalCharacteristics` and
  `PrecisionRecallCurve` set `relevance_threshold.initial` to
  `qrels_dataframe["relevance"].max()`, a `numpy.int32`. When the highest label is
  1 the field is also `disabled`, so Django validates the initial rather than the
  posted string — and `numpy.int32(1) in validators.EMPTY_VALUES` raises
  `ValueError: The truth value of an empty array is ambiguous`. Since most TREC
  qrels are binary, this made those two analyses unusable. The maxima are now cast
  to `int`.
- **The second reader of a topics or run file got nothing.** `load_queries_file`
  called `ElementTree.parse` on the `FieldFile` where it stood instead of
  reopening it. `create_report` builds one `RetrievalTask` and hands it to every
  analysis, so the second analysis to ask for the queries hit end of file and
  raised `ParseError: no element found`. That is exactly the shape of the new Query
  Text-based report, which reads the topics twice. All three loaders in
  `data_loaders_v2.py` now reopen through a context manager, as
  `RetrievalTask.qrels_dataframe` already did.

---

## Notes on the two newly added reports

### Query-based Performance Report (`query_based`)

Ports page 2 as four analyses: the existing `RelevanceJudgmentsPerQuery`, plus
`PerQueryPerformance`, `PerQueryPerformanceVsBaseline` and
`PerQueryPerformanceVsThreshold`. They share
`lib/utils/per_query.py`, which evaluates the measures per query, restricts every
run to the queries they all scored, and renders the difference statistics.

Where the original lets the user multiselect measures and a cutoff, these analyses
hardcode a fixed set, matching how the rest of ASPIRE-v2 works. Each set is the
original section's own default: `nDCG@10` and `P@10` for the per-query view,
`P@10` and `R@10` against a baseline, and `nDCG@10` against the median or
threshold.

`PerQueryPerformanceVsThreshold` keeps the original's overloaded control: a
threshold of `0.0` compares each experiment against the median of the other N−1,
anything higher compares every experiment against that fixed value.

Two deliberate changes: the original's `generate_colors` shuffles its palette, so
regenerating a report recoloured the charts — the shuffle is gone. And where the
original renders a figure per run in a Streamlit grid, ASPIRE-v2 stacks one
subplot row per measure inside a single figure.

### Query Text-based Performance Report (`query_text_based`)

Ports page 3 as three analyses, with **one section deliberately omitted**: the
original's query-similarity view embeds every query with a HuggingFace model and
projects it with t-SNE, which would pull `torch`, `transformers` and
`scikit-learn` into the image and download model weights inside the Celery worker.
That cost is not worth one scatter plot.

`QueryTextWordClouds` ports `query_clf_relevance_assessments` and renders one word
cloud per bucket. Two differences from the original:

- It uses `wordcloud.STOPWORDS` instead of `nltk.corpus.stopwords`, so nothing is
  downloaded at runtime. The rest of the preprocessing — lowercase, keep `\b[a-zA-Z]+\b`
  only — is unchanged.
- The `Max-Min-Median` method's median bucket is fixed. The original computes
  `sorted_indices[np.abs(metric_values - median).argsort()[:5]]`, indexing one
  ordering with positions from another, which returns five essentially arbitrary
  queries. ASPIRE-v2 uses `np.abs(values - median).argsort()[:5]` directly.

Word clouds are rasters, which none of the existing result types could carry, so
this branch adds `ImageResult` — a base64 PNG data URI rendered as an `<img>` in
both templates. `generate_pdf` already passes non-plot results through untouched,
so it needed no change.

`QueryPerformanceVsQueryLength` measures length by whitespace-splitting the topic
text and reports a Viridis scatter with a rolling mean, an equal-width against
equal-frequency bucket comparison, a distribution summary, and the original's
one-way ANOVA across the buckets when at least 20 queries are available.

## Follow-up work

Not addressed here, in rough order of impact:

1. Port page 4's "documents retrieved by 1/2/3/5/half+1/all experiments" analysis,
   including the query difficulty ranking.
2. Add query sampling for collections with more than 500 queries.
3. Surface the statistics `RelevanceJudgmentsPerQuery` already computes and throws
   away, and stop truncating the easy/hard lists to five entries.
4. Port the multi-query-document companion analyses: the per-document relevance
   breakdown and the cross-run ranked-position tables.
5. Consider a user-selected measures and cutoff block for Experimental Evaluation,
   matching the original's second table.
