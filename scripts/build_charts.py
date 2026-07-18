import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRIPT_DIR, "..", "charts")
DASHBOARD_DIR = os.path.join(SCRIPT_DIR, "..", "dashboard")
os.makedirs(OUT, exist_ok=True)
os.makedirs(DASHBOARD_DIR, exist_ok=True)

df = pd.read_csv(os.path.join(SCRIPT_DIR, "..", "data", "manufacturing_downtime_data.csv"), parse_dates=["Date"])

# ---------------- Dark industrial theme ----------------
BG = "#12161c"
PANEL = "#181d26"
GRID = "#2a313d"
TEXT = "#e7ebf0"
MUTED = "#9aa5b1"
AMBER = "#f2a93b"
TEAL = "#2ec4b6"
RED = "#e5484d"
BLUE = "#4c8bf5"
PURPLE = "#9d6bd6"
GREEN = "#5fd382"
PALETTE = [AMBER, TEAL, BLUE, PURPLE, RED, GREEN, "#e0a15c", "#6bd6c4"]

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": TEXT,
    "axes.labelcolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": GRID,
    "grid.color": GRID,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titlecolor": TEXT,
    "axes.titleweight": "bold",
})

def style_ax(ax, grid_axis="y"):
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis=grid_axis, alpha=0.35, linewidth=0.6)
    ax.set_axisbelow(True)

def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{OUT}/{name}.png", dpi=150, transparent=False)
    plt.close(fig)

# ---------------- KPI CALCULATIONS ----------------
kpi = {}
kpi["total_events"] = int(len(df))
kpi["total_downtime_hours"] = round(df["Downtime Hours"].sum(), 1)
kpi["total_repair_cost"] = round(df["Repair Cost EURO"].sum(), 2)
kpi["total_units_lost"] = int(df["Production Units Lost"].sum())
kpi["avg_downtime_hours"] = round(df["Downtime Hours"].mean(), 2)
kpi["avg_repair_cost"] = round(df["Repair Cost EURO"].mean(), 2)
kpi["pending_events"] = int((df["Status"] == "Pending").sum())
kpi["resolved_events"] = int((df["Status"] == "Resolved").sum())
kpi["unplanned_pct"] = round((df["Planned or Unplanned"] == "Unplanned").mean() * 100, 1)
kpi["planned_pct"] = round((df["Planned or Unplanned"] == "Planned").mean() * 100, 1)
kpi["cost_per_hour"] = round(df["Repair Cost EURO"].sum() / df["Downtime Hours"].sum(), 2)
kpi["avg_resolution_time"] = round(df["Resolution Time"].dropna().mean(), 2)

with open(os.path.join(DASHBOARD_DIR, "kpis.json"), "w") as f:
    json.dump(kpi, f, indent=2)
print("KPIs:", kpi)

# ---------------- 1. Monthly downtime trend (line) ----------------
monthly = df.groupby(df["Date"].dt.to_period("M")).agg(hours=("Downtime Hours", "sum")).reset_index()
monthly["Date"] = monthly["Date"].dt.to_timestamp()
fig, ax = plt.subplots(figsize=(9.5, 4))
ax.plot(monthly["Date"], monthly["hours"], color=AMBER, linewidth=2.4, marker="o", markersize=4)
ax.fill_between(monthly["Date"], monthly["hours"], color=AMBER, alpha=0.12)
ax.set_title("Monthly downtime trend (hours)")
style_ax(ax)
save(fig, "01_monthly_downtime_trend")

# ---------------- 2. Monthly repair cost trend ----------------
monthly_cost = df.groupby(df["Date"].dt.to_period("M")).agg(cost=("Repair Cost EURO", "sum")).reset_index()
monthly_cost["Date"] = monthly_cost["Date"].dt.to_timestamp()
fig, ax = plt.subplots(figsize=(9.5, 4))
ax.plot(monthly_cost["Date"], monthly_cost["cost"], color=TEAL, linewidth=2.4, marker="o", markersize=4)
ax.fill_between(monthly_cost["Date"], monthly_cost["cost"], color=TEAL, alpha=0.12)
ax.set_title("Monthly repair cost trend (EUR)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
style_ax(ax)
save(fig, "02_monthly_cost_trend")

# ---------------- 3. Downtime by plant (bar) ----------------
by_plant = df.groupby("Plant")["Downtime Hours"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(6, 4))
ax.barh(by_plant.index, by_plant.values, color=AMBER)
ax.set_title("Downtime hours by plant")
style_ax(ax, grid_axis="x")
save(fig, "03_downtime_by_plant")

# ---------------- 4. Downtime by machine (top 10) ----------------
by_machine = df.groupby("Machine ID")["Downtime Hours"].sum().sort_values(ascending=False).head(10).sort_values()
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.barh(by_machine.index, by_machine.values, color=TEAL)
ax.set_title("Top 10 machines by downtime hours")
style_ax(ax, grid_axis="x")
save(fig, "04_downtime_by_machine")

# ---------------- 5. Downtime by production line ----------------
by_line = df.groupby("Production Line")["Downtime Hours"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(6, 5))
ax.barh(by_line.index, by_line.values, color=BLUE)
ax.set_title("Downtime hours by production line")
style_ax(ax, grid_axis="x")
save(fig, "05_downtime_by_line")

# ---------------- 6. Downtime by shift ----------------
by_shift = df.groupby("Shift")["Downtime Hours"].sum()
fig, ax = plt.subplots(figsize=(5.5, 4))
ax.bar(by_shift.index, by_shift.values, color=[AMBER, TEAL, PURPLE])
ax.set_title("Downtime hours by shift")
style_ax(ax)
plt.setp(ax.get_xticklabels(), rotation=10, ha="right")
save(fig, "06_downtime_by_shift")

# ---------------- 7. Downtime by reason (top 10) ----------------
by_reason = df.groupby("Downtime Reason")["Downtime Hours"].sum().sort_values(ascending=False).head(10).sort_values()
fig, ax = plt.subplots(figsize=(7, 5))
ax.barh(by_reason.index, by_reason.values, color=RED)
ax.set_title("Downtime hours by reason (top 10)")
style_ax(ax, grid_axis="x")
save(fig, "07_downtime_by_reason")

# ---------------- 8. Downtime by machine type ----------------
by_type = df.groupby("Machine Type")["Downtime Hours"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(6.5, 5))
ax.barh(by_type.index, by_type.values, color=GREEN)
ax.set_title("Downtime hours by machine type")
style_ax(ax, grid_axis="x")
save(fig, "08_downtime_by_machine_type")

# ---------------- 9. Planned vs Unplanned donut ----------------
counts = df["Planned or Unplanned"].value_counts()
fig, ax = plt.subplots(figsize=(5, 5))
wedges, texts, autotexts = ax.pie(
    counts.values, labels=counts.index, autopct="%1.1f%%",
    colors=[RED, TEAL], startangle=90, pctdistance=0.8,
    wedgeprops=dict(width=0.42, edgecolor=BG, linewidth=2),
    textprops={"color": TEXT}
)
for a in autotexts:
    a.set_color(BG)
    a.set_fontweight("bold")
ax.set_title("Planned vs unplanned downtime")
save(fig, "09_planned_vs_unplanned")

# ---------------- 10. Repair cost by machine (top 15) ----------------
cost_machine = df.groupby("Machine ID")["Repair Cost EURO"].sum().sort_values(ascending=False).head(15).sort_values()
fig, ax = plt.subplots(figsize=(7, 6))
ax.barh(cost_machine.index, cost_machine.values, color=AMBER)
ax.set_title("Repair cost by machine (top 15)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x/1000:.0f}k"))
style_ax(ax, grid_axis="x")
save(fig, "10_repair_cost_by_machine")

# ---------------- 11. Top 10 most expensive machines (table-like bar w/ labels) ----------------
top10 = df.groupby("Machine ID").agg(cost=("Repair Cost EURO", "sum"),
                                      events=("Repair Cost EURO", "count")).sort_values("cost", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.barh(top10.index[::-1], top10["cost"][::-1], color=TEAL)
for b, (idx, row) in zip(bars, top10[::-1].iterrows()):
    ax.text(b.get_width() + max(top10["cost"])*0.01, b.get_y() + b.get_height()/2,
            f"€{row['cost']:,.0f}  ({int(row['events'])} events)", va="center", fontsize=9, color=MUTED)
ax.set_title("Top 10 most expensive machines")
ax.set_xlim(0, top10["cost"].max()*1.35)
style_ax(ax, grid_axis="x")
save(fig, "11_top10_expensive_machines")

# ---------------- 12. Production units lost by plant ----------------
units_plant = df.groupby("Plant")["Production Units Lost"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(6, 4))
ax.barh(units_plant.index, units_plant.values, color=PURPLE)
ax.set_title("Production units lost by plant")
style_ax(ax, grid_axis="x")
save(fig, "12_units_lost_by_plant")

# ---------------- 13. Pareto chart for downtime reasons ----------------
reason_hours = df.groupby("Downtime Reason")["Downtime Hours"].sum().sort_values(ascending=False)
cum_pct = reason_hours.cumsum() / reason_hours.sum() * 100
fig, ax1 = plt.subplots(figsize=(9, 5))
ax1.bar(reason_hours.index, reason_hours.values, color=AMBER)
ax1.set_title("Pareto analysis — downtime reasons")
style_ax(ax1)
plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax2 = ax1.twinx()
ax2.plot(reason_hours.index, cum_pct.values, color=TEAL, marker="o", markersize=4, linewidth=2)
ax2.axhline(80, color=RED, linestyle="--", linewidth=1, alpha=0.7)
ax2.set_ylim(0, 110)
ax2.tick_params(colors=MUTED)
ax2.spines[:].set_visible(False)
ax2.set_ylabel("Cumulative %", color=MUTED)
save(fig, "13_pareto_downtime_reasons")

# ---------------- 14. Heatmap downtime by day-of-week and shift ----------------
df["DayName"] = df["Date"].dt.day_name()
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
heat = df.pivot_table(index="Shift", columns="DayName", values="Downtime Hours", aggfunc="sum").reindex(columns=day_order)
fig, ax = plt.subplots(figsize=(9, 3.5))
im = ax.imshow(heat.values, cmap="inferno", aspect="auto")
ax.set_xticks(range(len(day_order)))
ax.set_xticklabels(day_order, rotation=0, fontsize=9)
ax.set_yticks(range(len(heat.index)))
ax.set_yticklabels(heat.index, fontsize=9)
for i in range(heat.shape[0]):
    for j in range(heat.shape[1]):
        ax.text(j, i, f"{heat.values[i,j]:.0f}", ha="center", va="center", color="white", fontsize=8)
ax.set_title("Downtime heatmap — day of week vs shift (hours)")
for spine in ax.spines.values():
    spine.set_visible(False)
cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.ax.yaxis.set_tick_params(color=MUTED)
plt.setp(cbar.ax.get_yticklabels(), color=MUTED)
save(fig, "14_heatmap_day_shift")

# ---------------- 15. Waterfall chart for repair costs by category ----------------
cat_cost = df.groupby("Downtime Category")["Repair Cost EURO"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(9.5, 5))
cum = 0
colors_wf = []
lefts = []
for v in cat_cost.values:
    lefts.append(cum)
    cum += v
total = cum
bars = ax.bar(list(cat_cost.index) + ["Total"], list(cat_cost.values) + [total],
              bottom=lefts + [0], color=[AMBER]*len(cat_cost) + [TEAL])
ax.set_title("Repair cost waterfall by downtime category (EUR)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
style_ax(ax)
plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
save(fig, "15_waterfall_repair_cost")

# ---------------- 16. Scatter: downtime hours vs repair cost ----------------
sample = df.sample(min(1200, len(df)), random_state=1)
fig, ax = plt.subplots(figsize=(7, 5.5))
colors_map = {"Planned": TEAL, "Unplanned": RED}
for k, g in sample.groupby("Planned or Unplanned"):
    ax.scatter(g["Downtime Hours"], g["Repair Cost EURO"], s=14, alpha=0.55,
               color=colors_map[k], label=k)
ax.set_xlabel("Downtime hours")
ax.set_ylabel("Repair cost (EUR)")
ax.set_title("Downtime hours vs repair cost")
ax.legend(frameon=False, labelcolor=TEXT)
style_ax(ax)
save(fig, "16_scatter_downtime_vs_cost")

# ---------------- 17. Treemap of downtime categories (approx via squarify-free manual) ----------------
import matplotlib.patches as patches
cat_hours = df.groupby("Downtime Category")["Downtime Hours"].sum().sort_values(ascending=False)
def simple_treemap(values, labels, colors, width=100, height=60):
    # simple slice-and-dice treemap
    total = sum(values)
    rects = []
    x, y, w, h = 0, 0, width, height
    horizontal = True
    remaining = list(zip(values, labels, colors))
    rem_total = total
    for v, l, c in remaining:
        if horizontal:
            rw = w * (v / rem_total)
            rects.append((x, y, rw, h, l, v, c))
            x += rw
            w -= rw
        rem_total -= v
    return rects

colors_tm = PALETTE * 2
rects = simple_treemap(cat_hours.values, cat_hours.index, colors_tm[:len(cat_hours)])
fig, ax = plt.subplots(figsize=(9.5, 5))
for (x, y, w, h, label, v, c) in rects:
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=c, edgecolor=BG, linewidth=2))
    if w > 4:
        ax.text(x + w/2, y + h/2, f"{label}\n{v:.0f}h", ha="center", va="center",
                fontsize=8.5, color=BG, fontweight="bold")
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.axis("off")
ax.set_title("Treemap — downtime hours by category")
save(fig, "17_treemap_categories")

print("All charts saved to", OUT)
print("Files:", sorted(os.listdir(OUT)))
