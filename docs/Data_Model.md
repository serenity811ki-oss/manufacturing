# Data Model — Manufacturing Downtime Analytics

## Overview

The dataset is delivered as a **flat, single-table export** (`manufacturing_downtime_data.csv` /
`.xlsx`) so it's easy to inspect and load anywhere. For Power BI, don't load it as one giant table —
split it into a **star schema** for correct performance, correct DAX, and a model that looks like
real BI engineering in an interview. The workbook already ships pre-split as three sheets:

| Sheet / file | Role | Grain |
|---|---|---|
| `Fact_Downtime` | Fact table | One row = one downtime event |
| `Dim_Date` | Date dimension | One row per calendar day, Jan 1 2023 – Dec 31 2024 |
| `Dim_Machine` | Machine dimension | One row per unique Machine ID |

## Star Schema

```
                     ┌───────────────┐
                     │   Dim_Date    │
                     │───────────────│
                     │ Date (PK)     │
                     │ Year          │
                     │ Month         │
                     │ Month Number  │
                     │ Week          │
                     │ Quarter       │
                     │ Day Name      │
                     │ Is Weekend    │
                     └───────┬───────┘
                             │ 1
                             │
                             │ *
                     ┌───────┴───────┐        ┌────────────────┐
                     │ Fact_Downtime │  *   1 │  Dim_Machine   │
                     │───────────────│────────│────────────────│
                     │ Event ID (PK) │        │ Machine ID (PK)│
                     │ Date (FK)     │        │ Plant          │
                     │ Machine ID(FK)│        │ Production Line│
                     │ Shift         │        │ Machine Type   │
                     │ Operator ID   │        └────────────────┘
                     │ Technician    │
                     │ Downtime Cat. │
                     │ Downtime Reason│
                     │ Planned/Unpl. │
                     │ Root Cause    │
                     │ Downtime Min. │
                     │ Downtime Hrs  │
                     │ Repair Cost   │
                     │ Cost/Minute   │
                     │ Units Lost    │
                     │ Product Type  │
                     │ Status        │
                     │ Resolution Time│
                     │ Maintenance Type│
                     └───────────────┘
```

## Relationships (set up in Power BI → Model view)

| From | To | Cardinality | Cross-filter | Active |
|---|---|---|---|---|
| `Dim_Date[Date]` | `Fact_Downtime[Date]` | 1 : Many | Single | Yes |
| `Dim_Machine[Machine ID]` | `Fact_Downtime[Machine ID]` | 1 : Many | Single | Yes |

> Note: `Plant` and `Production Line` are already denormalized onto `Dim_Machine`, so slicers for
> Plant / Line / Machine Type all filter through the single `Dim_Machine` relationship — no need
> for separate Plant or Line dimension tables at this data volume. (At larger scale you'd
> normalize further into `Dim_Plant` and `Dim_Line`.)

## Why a star schema instead of one flat table?

1. **DAX time intelligence** (`SAMEPERIODLASTYEAR`, `TOTALMTD`, etc.) requires a proper Date table
   marked as the official date table — this needs a dedicated `Dim_Date`.
2. **Slicers stay fast and independent.** Filtering Machine Type on a dimension table is cheaper
   than filtering a repeated text column on a 4,000+ row fact table.
3. **It's the pattern every BI hiring manager expects to see** — a flat single-table Power BI
   file is one of the fastest ways to signal "beginner" in a portfolio review.

## Setup steps in Power BI Desktop

1. **Get Data → Excel** → import `manufacturing_downtime_data.xlsx` (all 3 sheets).
2. In Power Query, confirm data types: `Date` = Date, all `*Hours`/`*Cost`/`*Minutes`/`*Lost`
   columns = Decimal/Whole Number, everything else = Text.
3. Close & Apply.
4. Go to **Model view**. Drag `Dim_Date[Date]` onto `Fact_Downtime[Date]`, and
   `Dim_Machine[Machine ID]` onto `Fact_Downtime[Machine ID]`.
5. Click `Dim_Date` table → **Table tools → Mark as Date Table** → choose the `Date` column.
6. Hide foreign keys and technical columns from Report view (right-click column → Hide) to keep
   the field list clean for end users — keep `Dim_Machine[Plant]`, `[Production Line]`,
   `[Machine Type]` visible since they drive slicers.
7. Create the `_Measures` table (Modeling → New Table → `_Measures = {}` ) and paste in the DAX
   from `dax/DAX_Measures.md`.

## Assumptions & data notes

- Data is **synthetic but statistically realistic**: seasonal winter uplift in downtime, cost per
  minute varies by machine type, downtime duration follows a log-normal-like distribution, and
  ~72% of events are unplanned (a deliberately realistic ratio for discrete manufacturing).
- `Resolution Time` is null for events still `Pending` or `In Progress` — this is intentional
  and should be handled with `AVERAGE()` (which ignores blanks) rather than `AVERAGEX` over the
  full table.
- `Cost per Minute` is stored as its own column (not purely derived) because in real plant data
  it's often sourced from a maintenance-cost master table keyed by machine type, not purely
  computed after the fact — a hybrid approach worth calling out in an interview.
