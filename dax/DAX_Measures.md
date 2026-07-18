# DAX Measures — Manufacturing Downtime Analytics

Create a new table in Power BI called **`_Measures`** (a disconnected measure table)
and paste these in. Assumes the fact table is named `Fact_Downtime` and there is a
`Dim_Date` table marked as the official Date Table, related on `Fact_Downtime[Date] -> Dim_Date[Date]`.

---

## Core Volume & Time Measures

```DAX
Total Downtime Events =
COUNTROWS ( Fact_Downtime )
```

```DAX
Total Downtime Hours =
SUM ( Fact_Downtime[Downtime Hours] )
```

```DAX
Total Downtime Minutes =
SUM ( Fact_Downtime[Downtime Minutes] )
```

```DAX
Average Downtime per Event (Hours) =
DIVIDE ( [Total Downtime Hours], [Total Downtime Events] )
```

```DAX
Average Downtime per Event (Minutes) =
DIVIDE ( [Total Downtime Minutes], [Total Downtime Events] )
```

## Cost Measures

```DAX
Total Repair Cost =
SUM ( Fact_Downtime[Repair Cost EURO] )
```

```DAX
Average Repair Cost =
DIVIDE ( [Total Repair Cost], [Total Downtime Events] )
```

```DAX
Cost per Downtime Hour =
DIVIDE ( [Total Repair Cost], [Total Downtime Hours] )
```

```DAX
Average Cost per Minute =
AVERAGE ( Fact_Downtime[Cost per Minute] )
```

## Production Impact

```DAX
Total Production Units Lost =
SUM ( Fact_Downtime[Production Units Lost] )
```

```DAX
Avg Units Lost per Event =
DIVIDE ( [Total Production Units Lost], [Total Downtime Events] )
```

## Planned vs Unplanned

```DAX
Planned Downtime Events =
CALCULATE (
    [Total Downtime Events],
    Fact_Downtime[Planned or Unplanned] = "Planned"
)
```

```DAX
Unplanned Downtime Events =
CALCULATE (
    [Total Downtime Events],
    Fact_Downtime[Planned or Unplanned] = "Unplanned"
)
```

```DAX
Planned Downtime % =
DIVIDE ( [Planned Downtime Events], [Total Downtime Events] )
```

```DAX
Unplanned Downtime % =
DIVIDE ( [Unplanned Downtime Events], [Total Downtime Events] )
```

```DAX
Planned Downtime Hours =
CALCULATE (
    [Total Downtime Hours],
    Fact_Downtime[Planned or Unplanned] = "Planned"
)
```

```DAX
Unplanned Downtime Hours =
CALCULATE (
    [Total Downtime Hours],
    Fact_Downtime[Planned or Unplanned] = "Unplanned"
)
```

## Resolution & Status

```DAX
Average Resolution Time =
AVERAGE ( Fact_Downtime[Resolution Time] )
```

```DAX
Number of Pending Events =
CALCULATE (
    [Total Downtime Events],
    Fact_Downtime[Status] = "Pending"
)
```

```DAX
Number of Resolved Events =
CALCULATE (
    [Total Downtime Events],
    Fact_Downtime[Status] = "Resolved"
)
```

```DAX
Number of In Progress Events =
CALCULATE (
    [Total Downtime Events],
    Fact_Downtime[Status] = "In Progress"
)
```

```DAX
Resolved Rate % =
DIVIDE ( [Number of Resolved Events], [Total Downtime Events] )
```

## Time Intelligence (requires Dim_Date marked as Date Table)

```DAX
Downtime Hours PY =
CALCULATE ( [Total Downtime Hours], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
```

```DAX
Downtime Hours YoY % =
DIVIDE ( [Total Downtime Hours] - [Downtime Hours PY], [Downtime Hours PY] )
```

```DAX
Repair Cost PY =
CALCULATE ( [Total Repair Cost], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
```

```DAX
Repair Cost YoY % =
DIVIDE ( [Total Repair Cost] - [Repair Cost PY], [Repair Cost PY] )
```

```DAX
MTD Downtime Hours =
TOTALMTD ( [Total Downtime Hours], Dim_Date[Date] )
```

```DAX
Rolling 3-Month Avg Downtime Hours =
AVERAGEX (
    DATESINPERIOD ( Dim_Date[Date], MAX ( Dim_Date[Date] ), -3, MONTH ),
    [Total Downtime Hours]
)
```

## Ranking Helper Measures (used by Top 10 / Pareto visuals)

```DAX
Repair Cost Rank =
RANKX ( ALL ( Fact_Downtime[Machine ID] ), [Total Repair Cost], , DESC )
```

```DAX
Cumulative Downtime Hours % (Pareto) =
VAR CurrentReason = SELECTEDVALUE ( Fact_Downtime[Downtime Reason] )
VAR ReasonTotal =
    CALCULATE (
        [Total Downtime Hours],
        ALLSELECTED ( Fact_Downtime[Downtime Reason] ),
        Fact_Downtime[Downtime Reason] = CurrentReason
    )
VAR RunningTotal =
    CALCULATE (
        [Total Downtime Hours],
        FILTER (
            ALLSELECTED ( Fact_Downtime[Downtime Reason] ),
            CALCULATE ( [Total Downtime Hours] ) >= ReasonTotal
        )
    )
VAR GrandTotal =
    CALCULATE ( [Total Downtime Hours], ALLSELECTED ( Fact_Downtime[Downtime Reason] ) )
RETURN
    DIVIDE ( RunningTotal, GrandTotal )
```

## Conditional Formatting Helper Measures

```DAX
KPI Color - Unplanned % =
VAR UnplannedPct = [Unplanned Downtime %]
RETURN
    SWITCH (
        TRUE (),
        UnplannedPct >= 0.40, "#E03C3C",
        UnplannedPct >= 0.25, "#F2A93B",
        "#3BB273"
    )
```

```DAX
KPI Color - Pending =
VAR PendingCount = [Number of Pending Events]
RETURN
    SWITCH (
        TRUE (),
        PendingCount >= 30, "#E03C3C",
        PendingCount >= 15, "#F2A93B",
        "#3BB273"
    )
```

---

### Notes
- All measures use `DIVIDE()` instead of `/` to avoid divide-by-zero errors when slicers filter to an empty set.
- Base measures (`[Total Downtime Events]`, `[Total Downtime Hours]`, `[Total Repair Cost]`) are referenced inside other measures rather than repeating `SUM()`/`COUNTROWS()` — this is a maintainability best practice reviewers look for.
- Time-intelligence measures require `Dim_Date` to be marked **"Mark as Date Table"** in Power BI (Table tools ribbon) with `Dim_Date[Date]` as the date column.
