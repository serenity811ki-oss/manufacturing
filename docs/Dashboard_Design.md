# Dashboard Design Specification

This is the build spec for recreating the dashboard in Power BI Desktop. Screenshots of the
target design are in `/screenshots`; the HTML mockups they were rendered from are in
`/dashboard`.

## Theme — "Dark Industrial"

| Token | Hex | Use |
|---|---|---|
| Background | `#0D1117` | Page & panel background |
| Panel | `#161B22` | Card background |
| Border | `#2A313D` | Card borders, gridlines |
| Text primary | `#E7EBF0` | KPI values, headings |
| Text muted | `#9AA5B1` | Labels, axis text |
| Amber (primary accent) | `#F2A93B` | Primary series, caution/attention accents |
| Teal (secondary accent) | `#2EC4B6` | Secondary series, positive/planned |
| Red | `#E5484D` | Unplanned / risk / negative delta |
| Blue | `#4C8BF5` | Tertiary series |
| Purple | `#9D6BD6` | Tertiary series |
| Green | `#5FD382` | Positive delta |

Font: Segoe UI (or a clean grotesque sans as fallback). KPI values bold, 20–22px. Card titles
uppercase, 12px, muted color, letter-spacing 0.4px — mimics real plant-floor signage/dashboards.

## Page 1 — Executive Overview

### Slicer panel (top, applies to whole page)
Date range · Plant · Production Line · Machine · Machine Type · Shift · Downtime Category ·
Planned or Unplanned — all as **slicer** visuals (dropdown style to save space), synced across
both pages via **Sync slicers** pane.

### KPI cards (row of 8, use Card visual or a KPI custom visual)

| # | KPI | Measure | Format |
|---|---|---|---|
| 1 | Total downtime events | `[Total Downtime Events]` | #,##0 |
| 2 | Total downtime hours | `[Total Downtime Hours]` | #,##0.0 |
| 3 | Total repair cost | `[Total Repair Cost]` | €#,##0,, "M" or €#,##0 |
| 4 | Production units lost | `[Total Production Units Lost]` | #,##0 |
| 5 | Average downtime per event | `[Average Downtime per Event (Hours)]` | 0.00 "hrs" |
| 6 | Average repair cost | `[Average Repair Cost]` | €#,##0.0 |
| 7 | Pending events | `[Number of Pending Events]` | #,##0, conditional color via `[KPI Color - Pending]` |
| 8 | Unplanned downtime % | `[Unplanned Downtime %]` | 0.0%, conditional color via `[KPI Color - Unplanned %]` |

Apply conditional formatting (Format visual → Callout value → Conditional formatting → Font
color → Format by: Field value → pick the matching `KPI Color -` measure) so cards 7–8 turn
red/amber/green automatically as filters change.

### Visuals grid

| Visual | Chart type | Axis / Legend / Values |
|---|---|---|
| Monthly downtime trend | Line chart (area-filled) | Axis: `Dim_Date[Year-Month]`; Values: `[Total Downtime Hours]` |
| Monthly repair cost trend | Line chart (area-filled) | Axis: `Dim_Date[Year-Month]`; Values: `[Total Repair Cost]` |
| Downtime by plant | Bar chart (horizontal) | Axis: `Dim_Machine[Plant]`; Values: `[Total Downtime Hours]` |
| Downtime by machine | Bar chart, filtered Top N = 10 | Axis: `Fact_Downtime[Machine ID]`; Values: `[Total Downtime Hours]` |
| Downtime by production line | Bar chart (horizontal) | Axis: `Dim_Machine[Production Line]`; Values: `[Total Downtime Hours]` |
| Downtime by shift | Column chart | Axis: `Fact_Downtime[Shift]`; Values: `[Total Downtime Hours]` |
| Downtime by reason | Bar chart, Top N = 10 | Axis: `Fact_Downtime[Downtime Reason]`; Values: `[Total Downtime Hours]` |
| Downtime by machine type | Bar chart (horizontal) | Axis: `Dim_Machine[Machine Type]`; Values: `[Total Downtime Hours]` |
| Planned vs unplanned | Donut chart | Legend: `Fact_Downtime[Planned or Unplanned]`; Values: `[Total Downtime Events]` |
| Repair cost by machine | Bar chart, Top N = 15 | Axis: `Fact_Downtime[Machine ID]`; Values: `[Total Repair Cost]` |
| Top 10 most expensive machines | Bar chart + data labels | Axis: Machine ID; Values: `[Total Repair Cost]`; Tooltip: `[Total Downtime Events]` |
| Production units lost by plant | Bar chart (horizontal) | Axis: `Dim_Machine[Plant]`; Values: `[Total Production Units Lost]` |
| Pareto — downtime reasons | Combo chart (column + line) | Columns: `[Total Downtime Hours]` by Reason; Line: `[Cumulative Downtime Hours % (Pareto)]`, secondary axis 0–100%, reference line at 80% |
| Heatmap — day × shift | Matrix visual with conditional background color, or a custom heatmap visual | Rows: `Fact_Downtime[Shift]`; Columns: `Dim_Date[Day Name]`; Values: `[Total Downtime Hours]` |
| Waterfall — repair cost by category | Waterfall chart | Category: `Fact_Downtime[Downtime Category]`; Breakdown: `[Total Repair Cost]` |
| Scatter — downtime vs cost | Scatter chart | X: `[Total Downtime Hours]`; Y: `[Total Repair Cost]`; Legend: `Planned or Unplanned`; Details: Event ID |
| Treemap — downtime categories | Treemap | Group: `Fact_Downtime[Downtime Category]`; Values: `[Total Downtime Hours]` |

## Page 2 — Executive Insights

Layout: one headline text box summarizing the two-year story, 4 stat cards (worst plant,
highest-cost machine, most common reason, highest downtime months), and two side-by-side text
panels — "Root cause summary" and "Recommendations" — populated from `docs/Executive_Insights.md`.
This page is mostly narrative (Text box + Card visuals), not chart-heavy, matching how a real
"Insights"/"Exec Summary" tab is built for stakeholders who won't self-serve the filters.

## Interaction notes

- Set all slicers to **single-select OFF** (allow multi-select) except Date, which uses a
  between-range slider.
- Turn on **Edit interactions** so the donut (Planned/Unplanned) cross-filters the rest of page 1
  but the Pareto chart does not get filtered by itself (avoid circular Top-N distortion).
- Add a bookmark button "Reset filters" pinned top-right of page 1.
