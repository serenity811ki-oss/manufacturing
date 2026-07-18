"""
Manufacturing Downtime Dataset Generator
Generates a realistic synthetic dataset (Jan 2023 - Dec 2024) for a
Power BI manufacturing downtime analytics portfolio project.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Resolve paths relative to this script's location so the script works
# regardless of the current working directory it's invoked from.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

rng = np.random.default_rng(42)

N_TARGET = 4200  # within 3000-5000 requested range

# ---------------------------------------------------------------------
# Dimension definitions
# ---------------------------------------------------------------------
PLANTS = ["Plant Rotterdam", "Plant Munich", "Plant Katowice", "Plant Lyon"]

LINES_PER_PLANT = {
    "Plant Rotterdam": ["Line R1", "Line R2", "Line R3"],
    "Plant Munich": ["Line M1", "Line M2", "Line M3", "Line M4"],
    "Plant Katowice": ["Line K1", "Line K2"],
    "Plant Lyon": ["Line L1", "Line L2", "Line L3"],
}

MACHINE_TYPES = [
    "CNC Machine", "Hydraulic Press", "Robotic Welder", "Conveyor System",
    "Injection Molding Machine", "Packaging Machine", "Assembly Robot",
    "Industrial Oven", "Stamping Press", "Palletizer"
]

PRODUCT_TYPES = ["Automotive Parts", "Metal Fittings", "Plastic Components",
                  "Electronic Housings", "Packaging Units", "Machine Tools"]

SHIFTS = ["Morning (06-14)", "Afternoon (14-22)", "Night (22-06)"]

DOWNTIME_CATEGORIES = {
    "Mechanical Failure": ["Bearing Failure", "Belt Breakage", "Hydraulic Leak",
                            "Gear Wear", "Motor Failure"],
    "Electrical Failure": ["Sensor Malfunction", "Wiring Fault", "PLC Error",
                            "Power Supply Failure", "Short Circuit"],
    "Software/Control Issue": ["Software Crash", "HMI Freeze", "Firmware Update Error",
                                "Network Communication Loss"],
    "Material Shortage": ["Raw Material Delay", "Component Stockout", "Supplier Delay"],
    "Changeover": ["Product Changeover", "Tooling Change", "Mold Change"],
    "Quality Issue": ["Out of Spec Product", "Calibration Drift", "Rework Required"],
    "Operator Error": ["Incorrect Setup", "Manual Handling Error", "Missed Procedure Step"],
    "Preventive Maintenance": ["Scheduled Inspection", "Lubrication Service",
                                "Filter Replacement", "Routine Calibration"],
}

ROOT_CAUSES = ["Wear and Tear", "Lack of Preventive Maintenance", "Human Error",
               "Supplier Quality Issue", "Design Flaw", "Environmental Conditions",
               "Aging Equipment", "Inadequate Training", "Poor Spare Parts Availability",
               "Process Variation", "Unknown"]

MAINTENANCE_TYPES = ["Corrective", "Preventive", "Predictive"]

STATUS_OPTIONS = ["Resolved", "Pending", "In Progress"]

TECHNICIANS = [f"Tech-{i:03d}" for i in range(1, 26)]
OPERATORS = [f"OP-{i:04d}" for i in range(1, 121)]

# Base cost-per-minute varies by machine type (EUR)
COST_PER_MIN_BASE = {
    "CNC Machine": 9.5, "Hydraulic Press": 8.0, "Robotic Welder": 11.0,
    "Conveyor System": 4.0, "Injection Molding Machine": 10.5,
    "Packaging Machine": 5.5, "Assembly Robot": 12.0,
    "Industrial Oven": 6.5, "Stamping Press": 8.5, "Palletizer": 4.5
}

# Build machine registry: each plant/line has a fixed pool of machines
machine_registry = []
machine_counter = 1
for plant in PLANTS:
    for line in LINES_PER_PLANT[plant]:
        n_machines = rng.integers(3, 6)
        for _ in range(n_machines):
            mtype = rng.choice(MACHINE_TYPES)
            machine_registry.append({
                "Plant": plant,
                "Production Line": line,
                "Machine ID": f"MC-{machine_counter:04d}",
                "Machine Type": mtype
            })
            machine_counter += 1

machine_df = pd.DataFrame(machine_registry)

# ---------------------------------------------------------------------
# Date range
# ---------------------------------------------------------------------
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
date_range_days = (end_date - start_date).days

# ---------------------------------------------------------------------
# Generate records
# ---------------------------------------------------------------------
records = []

# seasonal weighting: more downtime events in winter months (heating/cold starts)
# and a slight upward creep in 2024 machine age -> more mechanical failures
def seasonal_weight(month):
    winter_months = {12, 1, 2}
    summer_months = {6, 7, 8}
    if month in winter_months:
        return 1.25
    if month in summer_months:
        return 0.9
    return 1.0

# Precompute daily weights across the date range for sampling
all_dates = [start_date + timedelta(days=i) for i in range(date_range_days + 1)]
weights = np.array([seasonal_weight(d.month) for d in all_dates], dtype=float)
weights = weights / weights.sum()

sampled_dates = rng.choice(all_dates, size=N_TARGET, p=weights)

for i in range(N_TARGET):
    d = pd.Timestamp(sampled_dates[i])
    year = d.year
    month = d.month
    week = int(d.isocalendar()[1])

    machine_row = machine_df.sample(1, random_state=rng.integers(0, 1_000_000)).iloc[0]
    plant = machine_row["Plant"]
    line = machine_row["Production Line"]
    machine_id = machine_row["Machine ID"]
    machine_type = machine_row["Machine Type"]

    shift = rng.choice(SHIFTS, p=[0.4, 0.35, 0.25])
    operator = rng.choice(OPERATORS)
    technician = rng.choice(TECHNICIANS)

    category = rng.choice(list(DOWNTIME_CATEGORIES.keys()),
                           p=[0.20, 0.14, 0.10, 0.10, 0.13, 0.11, 0.10, 0.12])
    reason = rng.choice(DOWNTIME_CATEGORIES[category])

    planned = "Planned" if category in ("Preventive Maintenance", "Changeover") else "Unplanned"
    # small chance planned categories are logged unplanned due to overrun, and vice versa
    if rng.random() < 0.05:
        planned = "Unplanned" if planned == "Planned" else "Planned"

    root_cause = rng.choice(ROOT_CAUSES)

    # Downtime minutes: lognormal-ish, category dependent
    if category == "Preventive Maintenance":
        minutes = rng.integers(20, 90)
    elif category == "Changeover":
        minutes = rng.integers(15, 60)
    elif category == "Material Shortage":
        minutes = rng.integers(30, 240)
    else:
        minutes = int(rng.lognormal(mean=3.8, sigma=0.7))
        minutes = min(max(minutes, 5), 480)

    hours = round(minutes / 60, 2)

    base_cpm = COST_PER_MIN_BASE[machine_type]
    cost_variability = rng.normal(1.0, 0.25)
    cost_per_minute = round(max(base_cpm * cost_variability, 1.0), 2)
    repair_cost = round(cost_per_minute * minutes, 2)

    # Production units lost: correlated with downtime minutes
    units_lost = int(max(0, rng.normal(minutes * rng.uniform(0.8, 2.2), minutes * 0.3)))

    product_type = rng.choice(PRODUCT_TYPES)

    maintenance_type = ("Preventive" if category == "Preventive Maintenance"
                         else rng.choice(["Corrective", "Predictive"], p=[0.75, 0.25]))

    # Status distribution: most resolved, some pending/in progress, more pending
    # for recent dates
    days_since = (end_date - d).days
    if days_since < 14:
        status = rng.choice(STATUS_OPTIONS, p=[0.55, 0.25, 0.20])
    else:
        status = rng.choice(STATUS_OPTIONS, p=[0.90, 0.05, 0.05])

    if status == "Resolved":
        resolution_time = round(max(0.2, rng.normal(hours * 1.4 + 0.5, 1.0)), 2)
    elif status == "In Progress":
        resolution_time = None
    else:
        resolution_time = None

    records.append({
        "Date": d.strftime("%Y-%m-%d"),
        "Year": year,
        "Month": d.strftime("%B"),
        "Week": week,
        "Plant": plant,
        "Production Line": line,
        "Machine ID": machine_id,
        "Machine Type": machine_type,
        "Shift": shift,
        "Operator ID": operator,
        "Technician": technician,
        "Downtime Category": category,
        "Downtime Reason": reason,
        "Planned or Unplanned": planned,
        "Root Cause": root_cause,
        "Downtime Minutes": minutes,
        "Downtime Hours": hours,
        "Repair Cost EURO": repair_cost,
        "Cost per Minute": cost_per_minute,
        "Production Units Lost": units_lost,
        "Product Type": product_type,
        "Status": status,
        "Resolution Time": resolution_time,
        "Maintenance Type": maintenance_type,
    })

df = pd.DataFrame(records)
df.sort_values("Date", inplace=True)
df.reset_index(drop=True, inplace=True)
df.insert(0, "Event ID", [f"DT-{i+1:05d}" for i in range(len(df))])

# ---------------------------------------------------------------------
# Dim_Date: one row per calendar day across the full date range
# ---------------------------------------------------------------------
dim_date_rows = []
for d in all_dates:
    ts = pd.Timestamp(d)
    dim_date_rows.append({
        "Date": ts.strftime("%Y-%m-%d"),
        "Year": ts.year,
        "Month Number": ts.month,
        "Month": ts.strftime("%B"),
        "Month Short": ts.strftime("%b"),
        "Year-Month": ts.strftime("%Y-%m"),
        "Week": int(ts.isocalendar()[1]),
        "Day Name": ts.strftime("%A"),
        "Day Number": ts.day,
        "Quarter": f"Q{(ts.month - 1) // 3 + 1}",
        "Is Weekend": ts.day_of_week >= 5,
    })
dim_date = pd.DataFrame(dim_date_rows)

# ---------------------------------------------------------------------
# Dim_Machine: the fixed machine registry built above, ordered by each
# machine's first appearance in the fact table (matches how the shipped
# reference dataset orders this dimension).
# ---------------------------------------------------------------------
machine_lookup = machine_df.set_index("Machine ID")[["Plant", "Production Line", "Machine Type"]]
first_seen_order = df.drop_duplicates("Machine ID", keep="first")["Machine ID"].tolist()
remaining = [m for m in machine_lookup.index if m not in first_seen_order]
dim_machine = machine_lookup.loc[first_seen_order + remaining].reset_index()

# Save flat fact table + standalone dimension CSVs
df.to_csv(os.path.join(DATA_DIR, "manufacturing_downtime_data.csv"), index=False)
dim_date.to_csv(os.path.join(DATA_DIR, "dim_date.csv"), index=False)
dim_machine.to_csv(os.path.join(DATA_DIR, "dim_machine.csv"), index=False)

# Save the 3-sheet star-schema workbook (Fact_Downtime, Dim_Date, Dim_Machine)
xlsx_path = os.path.join(DATA_DIR, "manufacturing_downtime_data.xlsx")
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Fact_Downtime")
    dim_date.to_excel(writer, index=False, sheet_name="Dim_Date")
    dim_machine.to_excel(writer, index=False, sheet_name="Dim_Machine")

print("Rows generated:", len(df))
print(df.head(3).to_string())
print("\nStatus distribution:\n", df["Status"].value_counts())
print("\nPlanned/Unplanned:\n", df["Planned or Unplanned"].value_counts())
print(f"\nSaved fact table + Dim_Date ({len(dim_date)} rows) + Dim_Machine ({len(dim_machine)} rows) to {DATA_DIR}")
