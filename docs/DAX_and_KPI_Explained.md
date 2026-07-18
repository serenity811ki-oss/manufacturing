# DAX & KPI Explained (Interview Prep)

Plain-language explanations of every measure and KPI in this project — the kind of answer to give
when an interviewer asks "walk me through one of your DAX measures."

## Why `DIVIDE()` instead of `/`

Every ratio measure (`Planned Downtime %`, `Cost per Downtime Hour`, etc.) uses `DIVIDE(numerator,
denominator)` instead of the `/` operator. `DIVIDE` returns `BLANK()` instead of throwing a
`#DIV/0!`/infinity error when the denominator is 0 — which happens constantly once a user starts
slicing to a machine or day with no events. This is one of the first things a BI reviewer checks.

## Why base measures reference each other

`Average Repair Cost` is written as `DIVIDE([Total Repair Cost], [Total Downtime Events])` rather
than `DIVIDE(SUM(Fact_Downtime[Repair Cost EURO]), COUNTROWS(Fact_Downtime))`. Referencing the
named base measures means:
- If the cost column or filtering logic ever changes, it changes in one place.
- The measure list reads like a dependency tree, which is what a reviewer wants to see — it shows
  you're building a maintainable model, not writing one-off formulas.

## How filter context makes `CALCULATE` work

`Unplanned Downtime Events = CALCULATE([Total Downtime Events], Fact_Downtime[Planned or
Unplanned] = "Unplanned")` — `CALCULATE` takes whatever filter context already exists (from
slicers, visuals, page filters) and *adds* the "Unplanned" filter on top. That's different from
filtering the whole table permanently — it respects whatever the user has already sliced to
(a specific plant, a date range) and narrows further, which is exactly the behavior a slicer-driven
dashboard needs.

## The Pareto cumulative % measure, explained

This is the most advanced measure in the project and worth walking through step by step in an
interview:

1. `CurrentReason` captures which downtime reason the current visual row represents.
2. `ReasonTotal` calculates that one reason's total downtime hours.
3. `RunningTotal` uses `FILTER` + `ALLSELECTED` to sum the downtime hours of every reason whose
   total is **greater than or equal to** the current reason's total — this is what builds the
   "running total down the sorted list" behavior without needing the data pre-sorted in the model.
4. `GrandTotal` is the total across all reasons currently visible (respecting slicers via
   `ALLSELECTED`, so it updates correctly when a slicer narrows the reason list).
5. The result is `RunningTotal / GrandTotal` — the cumulative percentage that, combined with the
   80% reference line, identifies the "vital few" reasons driving most of the downtime (the
   80/20 rule).

## KPI-by-KPI plain-English definitions

| KPI | Plain-English meaning | Why it matters to the business |
|---|---|---|
| Total downtime events | How many times a stoppage was logged | Volume of disruption — the raw count operations tracks weekly |
| Total downtime hours | Total time machines were not producing | Direct input to OEE (Overall Equipment Effectiveness) calculations |
| Average downtime per event | How long a typical stoppage lasts | Distinguishes "many short stops" from "few long stops" — different fixes for each |
| Total repair cost | Total euros spent fixing downtime | The direct line to the maintenance budget |
| Average repair cost | Typical cost of one repair | Flags whether cost growth is from more events or pricier events |
| Cost per downtime hour | €/hour, blending frequency and severity | A single efficiency number executives can track over time |
| Total production units lost | Units that weren't made because of downtime | Connects downtime directly to revenue impact, not just cost |
| Planned / Unplanned % | Split between scheduled and surprise downtime | The single most important ratio in maintenance — high unplanned % means the plan is reactive, not proactive |
| Average resolution time | Hours from logging an issue to closing it | A responsiveness metric for the maintenance team, separate from the downtime itself |
| Pending / Resolved events | Backlog vs. throughput | Pending count is an early-warning signal — a growing backlog means the team is falling behind |

## Anticipated interview questions and how this project answers them

**"Why a star schema instead of one flat table?"** → See `Data_Model.md`. Short answer: correct
time intelligence, faster slicers, and it's the pattern reviewers expect.

**"How would this scale to real production data?"** → Swap the CSV/Excel source for a direct
SQL/Data Warehouse connection, keep the same star schema, and add an incremental refresh policy
on `Dim_Date` so only the last N months of `Fact_Downtime` reprocess on each refresh.

**"What would you add with more time?"** → A `Dim_Plant` and `Dim_Line` table (currently
denormalized onto `Dim_Machine`) for larger datasets, a what-if parameter for maintenance-budget
scenario planning, and row-level security so each plant manager only sees their own plant by
default.
