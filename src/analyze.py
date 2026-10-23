"""Join Olist order, customer, and review tables; rebuild a small dashboard."""

from __future__ import annotations

import csv
import html
import json
import re
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "outputs"
REPORT = ROOT / "reports" / "dashboard.html"
TEAL = "#12B8A6"
BLUE = "#1496D4"
RED = "#E45756"
GRID = "#E8EBEF"

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Federal District", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}. Run python src/download_data.py first.")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def horizontal_bars(
    labels: list[str], values: list[float], colors: list[str], value_format,
    *, width: int = 1400, label_width: int = 420, row_height: int = 38,
    axis_max: float | None = None, intervals: int = 4,
) -> str:
    top, bottom, right = 28, 36, 88
    height = top + row_height * len(labels) + bottom
    plot_width = width - label_width - right
    high = axis_max if axis_max is not None else max(values, default=1) * 1.08
    high = high or 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="horizontal bar chart">']
    for index in range(intervals + 1):
        value = high * index / intervals
        x = label_width + plot_width * value / high
        label = value_format(value)
        out.append(f'<line x1="{x:.1f}" y1="{top-6}" x2="{x:.1f}" y2="{height-bottom}" stroke="{GRID}"/>')
        out.append(f'<text x="{x:.1f}" y="{height-8}" text-anchor="middle" fill="#75808a" font-size="13">{esc(label)}</text>')
    for index, (label, value, color) in enumerate(zip(labels, values, colors)):
        y = top + index * row_height
        x_end = label_width + plot_width * value / high
        out.append(f'<text x="{label_width-14}" y="{y+19}" text-anchor="end" fill="#56616c" font-size="14">{esc(label)}</text>')
        out.append(f'<rect x="{label_width}" y="{y+2}" width="{max(x_end-label_width, 1):.1f}" height="22" rx="2" fill="{color}"/>')
        out.append(f'<text x="{x_end+8:.1f}" y="{y+19}" text-anchor="start" fill="#44505b" font-size="14">{esc(value_format(value))}</text>')
    out.append("</svg>")
    return "".join(out)


def dashboard(kpis: list[tuple[str, str]], charts: list[tuple[str, str]]) -> str:
    kpi_html = "".join(
        f'<section class="kpi"><div class="label">{esc(label)}</div><div class="value">{esc(value)}</div></section>'
        for label, value in kpis
    )
    chart_html = "".join(
        f'<section class="panel"><h2>{esc(title)}</h2>{svg}</section>'
        for title, svg in charts
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>E-commerce delivery and reviews</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f1f2f4;color:#26313a;font-family:Arial,Helvetica,sans-serif}}
header{{height:46px;background:#fff;border-bottom:1px solid #dfe2e6;display:flex;align-items:center;padding:0 18px;font-size:15px;font-weight:600}}
main{{max-width:1500px;margin:auto;padding:8px}}.kpis{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:8px}}
.kpi,.panel{{background:#fff;border:1px solid #e0e3e7}}.kpi{{height:76px;padding:11px 14px}}
.label{{font-size:10px;color:#67717b;font-weight:600;letter-spacing:.04em;text-transform:uppercase}}
.value{{font-size:23px;margin-top:7px;font-weight:400;color:#303941}}.panel{{margin-bottom:8px;padding:10px 12px 8px}}
h2{{margin:0 0 4px;font-weight:600;font-size:12px;color:#3b454e}}.panel svg{{display:block;width:100%;height:auto}}
@media(max-width:700px){{.kpis{{grid-template-columns:repeat(2,minmax(0,1fr))}}main{{padding:7px}}}}
</style></head><body><header>Delivery performance</header><main>
<section class="kpis">{kpi_html}</section>{chart_html}</main></body></html>'''


def save_chart_svgs(charts: list[tuple[str, str]]) -> None:
    chart_dir = REPORT.parent / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    for old_chart in chart_dir.glob("*.svg"):
        old_chart.unlink()
    for title, svg in charts:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        (chart_dir / f"{slug}.svg").write_text(svg, encoding="utf-8")


def run() -> None:
    orders = read_csv(RAW / "olist_orders_dataset.csv")
    customers = read_csv(RAW / "olist_customers_dataset.csv")
    reviews = read_csv(RAW / "olist_order_reviews_dataset.csv")

    state_by_customer = {row["customer_id"]: row["customer_state"] for row in customers}
    review_scores: dict[str, list[float]] = defaultdict(list)
    for review in reviews:
        try:
            review_scores[review["order_id"]].append(float(review["review_score"]))
        except (KeyError, ValueError):
            continue

    deliveries: list[dict[str, object]] = []
    for order in orders:
        if order.get("order_status") != "delivered":
            continue
        delivered_at = parse_date(order.get("order_delivered_customer_date", ""))
        expected_at = parse_date(order.get("order_estimated_delivery_date", ""))
        if delivered_at is None or expected_at is None:
            continue
        days_late = (delivered_at - expected_at).total_seconds() / 86400
        timing = "On time" if days_late <= 0 else "1–7 days late" if days_late <= 7 else "8+ days late"
        scores = review_scores.get(order["order_id"], [])
        deliveries.append({
            "order_id": order["order_id"],
            "state": state_by_customer.get(order["customer_id"], ""),
            "days_late": days_late,
            "timing": timing,
            "review_score": statistics.mean(scores) if scores else None,
        })

    timing_order = ["On time", "1–7 days late", "8+ days late"]
    review_by_timing: dict[str, list[float]] = {group: [] for group in timing_order}
    state_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    late_deliveries = 0
    for delivery in deliveries:
        if delivery["review_score"] is not None:
            review_by_timing[str(delivery["timing"])].append(float(delivery["review_score"]))
        is_late = float(delivery["days_late"]) > 0
        late_deliveries += int(is_late)
        state = str(delivery["state"])
        if state:
            state_totals[state][0] += 1
            state_totals[state][1] += int(is_late)

    review_summary = [
        {
            "timing": group,
            "reviewed_orders": len(review_by_timing[group]),
            "average_review_score": round(statistics.mean(review_by_timing[group]), 2) if review_by_timing[group] else None,
        }
        for group in timing_order
    ]
    state_summary = sorted(
        [
            {
                "state": state,
                "state_name": STATE_NAMES.get(state, state),
                "delivered_orders": totals[0],
                "late_deliveries": totals[1],
            }
            for state, totals in state_totals.items()
        ],
        key=lambda row: row["late_deliveries"],
        reverse=True,
    )
    avg_review = statistics.mean(
        float(delivery["review_score"]) for delivery in deliveries if delivery["review_score"] is not None
    )

    metrics = {
        "orders_in_file": len(orders),
        "delivered_orders_with_dates": len(deliveries),
        "reviewed_delivered_orders": sum(len(scores) for scores in review_by_timing.values()),
        "late_deliveries": late_deliveries,
        "late_delivery_rate": round(late_deliveries / len(deliveries), 4) if deliveries else 0,
        "average_review_score": round(avg_review, 2),
        "reviews_by_delivery_timing": review_summary,
        "late_deliveries_by_state": state_summary,
    }
    review_labels = [
        f"{row['timing']}  ·  n={row['reviewed_orders']:,} orders"
        for row in review_summary
    ]
    review_values = [float(row["average_review_score"] or 0) for row in review_summary]
    review_colors = [TEAL, RED, RED]
    state_rows = state_summary[:10]
    state_labels = [f"{row['state_name']} ({row['state']})" for row in state_rows]
    late_values = [float(row["late_deliveries"]) for row in state_rows]
    charts = [
        (
            "Average review score by delivery timing",
            horizontal_bars(review_labels, review_values, review_colors, lambda value: f"{value:.1f}", label_width=560, row_height=46, axis_max=5, intervals=5),
        ),
        (
            "Late deliveries by customer state · top 10",
            horizontal_bars(state_labels, late_values, [BLUE] * len(state_rows), lambda value: f"{value:,.0f}", label_width=390, row_height=34),
        ),
    ]
    kpis = [
        ("Orders", f"{len(orders):,}"),
        ("Delivered orders analyzed", f"{len(deliveries):,}"),
        ("Late deliveries", f"{late_deliveries:,}  ·  {late_deliveries / len(deliveries):.1%}"),
        ("Average review", f"{avg_review:.2f} / 5"),
    ]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(dashboard(kpis, charts), encoding="utf-8")
    save_chart_svgs(charts)
    print(
        f"Orders: {len(orders):,} | Delivered analyzed: {len(deliveries):,} | "
        f"Late: {late_deliveries:,} ({late_deliveries / len(deliveries):.1%}) | Dashboard: {REPORT}"
    )


if __name__ == "__main__":
    run()
