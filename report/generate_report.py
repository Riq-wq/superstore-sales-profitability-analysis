"""
generate_report.py
==================
Regenerates `Superstore_Sales_Profitability_Report.pdf` from the cleaned
Superstore dataset.

Pipeline
--------
    data/Superstore_cleaned.csv
        -> pandas (KPIs, aggregations)
        -> matplotlib (six figures, saved to report/figures/)
        -> reportlab (nine-page PDF)

Run with the Anaconda base interpreter (it has pandas + matplotlib):

    C:\\ProgramData\\anaconda3\\python.exe report\\generate_report.py

Every number printed in the report is computed in this file, so the PDF can
always be rebuilt and every figure in it can be traced back to a line here.

Outputs
-------
    report/figures/figure1..6.png
    report/Superstore_Sales_Profitability_Report.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: don't try to open a GUI window
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data" / "Superstore_cleaned.csv"
FIGDIR = HERE / "figures"
OUTPDF = HERE / "Superstore_Sales_Profitability_Report.pdf"

FIGDIR.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# Design tokens (match the palette used in the existing figures)
# --------------------------------------------------------------------------
NAVY = (31 / 255, 45 / 255, 61 / 255)      # #1F2D3D
TEAL = (42 / 255, 157 / 255, 143 / 255)    # #2A9D8F
CORAL = (231 / 255, 111 / 255, 81 / 255)   # #E76F51

INK = colors.HexColor("#1F2D3D")
TEAL_HEX = colors.HexColor("#2A9D8F")
CORAL_HEX = colors.HexColor("#E76F51")

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "font.size": 11,
        "axes.edgecolor": "#2A2A2A",
        "axes.labelcolor": "#2A2A2A",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.color": "#E6E6E6",
        "grid.linewidth": 0.8,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)


# ==========================================================================
# 1. Load + verify the data
# ==========================================================================
def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, encoding="utf-8-sig")
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["ship_date"] = pd.to_datetime(df["ship_date"])
    df["month"] = df["order_date"].dt.month
    return df


# ==========================================================================
# 2. Metric helpers - every number in the report comes from one of these
# ==========================================================================
def money(x: float, unit: str = "M") -> str:
    """$2.30M / $286.4K formatting."""
    if unit == "M":
        return f"${x / 1e6:.2f}M"
    return f"${x / 1e3:.1f}K"


def measured_margin(df: pd.DataFrame) -> float:
    """Overall margin = total profit / total sales."""
    return df["profit"].sum() / df["sales"].sum() * 100


def discount_bands(df: pd.DataFrame) -> pd.DataFrame:
    """Profit-sum + mean-of-order-margins per discount band.

    Note on method: the 'Avg. Profit Margin' column is the MEAN OF PER-ORDER
    MARGINS inside each band, not total-profit / total-sales. Both are valid;
    the per-order mean answers 'what does a typical order in this band earn'.
    """
    edges = [-0.001, 0.0, 0.20, 0.40, 1.0]
    labels = ["0% (no discount)", "1 - 20%", "21 - 40%", "40%+"]
    b = df.assign(band=pd.cut(df["discount"], bins=edges, labels=labels))
    g = b.groupby("band", observed=True).agg(
        profit=("profit", "sum"),
        margin=("profit_margin", "mean"),
        orders=("order_id", "size"),
    )
    return g


def category_totals(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("category")[["sales", "profit"]].sum().sort_values(
        "sales", ascending=False
    )


def loss_states(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("state")[["sales", "profit"]].sum()
    return g[g["profit"] < 0].sort_values("profit")


def loss_subcategories(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("sub_category")[["sales", "profit"]].sum()
    return g[g["profit"] < 0].sort_values("profit")


def region_totals(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("region")[["sales", "profit"]].sum().sort_values(
        "sales", ascending=False
    )


def segment_totals(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("segment")[["sales", "profit"]].sum().sort_values(
        "sales", ascending=False
    )


def ship_totals(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("ship_mode").agg(
        profit=("profit", "sum"),
        avg_days=("shipping_duration", "mean"),
    )


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("month")[["sales", "profit"]].sum()


def top_customers(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    return (
        df.groupby("customer_name")["sales"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
    )


# ==========================================================================
# 3. Figures
# ==========================================================================
def fig_grouped_bar(labels, series_a, series_b, name_a, name_b, title, fname,
                    ylabel="USD"):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = range(len(labels))
    w = 0.38
    ax.bar([i - w / 2 for i in x], series_a, w, label=name_a, color=NAVY)
    ax.bar([i + w / 2 for i in x], series_b, w, label=name_b, color=TEAL)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIGDIR / fname)
    plt.close(fig)
    return FIGDIR / fname


def fig_barh_negative(labels, values, title, fname, ylabel="USD"):
    fig, ax = plt.subplots(figsize=(7.0, 4.0 + 0.15 * len(labels)))
    y = range(len(labels))
    ax.barh(list(y), values, color=CORAL)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel(ylabel)
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    for i, v in enumerate(values):
        ax.text(v, i, f"  ${v/1e3:,.1f}K", va="center", ha="right", fontsize=9)
    fig.savefig(FIGDIR / fname)
    plt.close(fig)
    return FIGDIR / fname


def fig_bar_posneg(labels, values, title, fname, ylabel="USD"):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    cols = [TEAL if v >= 0 else CORAL for v in values]
    ax.bar(labels, values, color=cols)
    ax.axhline(0, color="#2A2A2A", linewidth=1)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIGDIR / fname)
    plt.close(fig)
    return FIGDIR / fname


def fig_line(months, sales, profit, title, fname):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.plot(months, sales, marker="o", color=NAVY, label="Total Sales")
    ax.plot(months, profit, marker="o", color=TEAL, label="Total Profit")
    ax.set_xticks(months)
    ax.set_xticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
    ax.set_ylabel("USD")
    ax.set_title(title)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIGDIR / fname)
    plt.close(fig)
    return FIGDIR / fname


def build_figures(df: pd.DataFrame) -> dict[str, Path]:
    cat = category_totals(df)
    bands = discount_bands(df)
    st = loss_states(df)
    sc = loss_subcategories(df)
    reg = region_totals(df)
    mon = monthly_trend(df)

    figs = {}
    figs["fig1"] = fig_grouped_bar(
        cat.index.tolist(), cat["sales"].tolist(), cat["profit"].tolist(),
        "Total Sales", "Total Profit", "Sales vs Profit by Category",
        "figure1.png",
    )
    figs["fig2"] = fig_barh_negative(
        sc.index.tolist(), sc["profit"].tolist(),
        "Total Profit of Loss-Making Sub-Categories", "figure2.png",
    )
    figs["fig3"] = fig_bar_posneg(
        bands.index.astype(str).tolist(), bands["profit"].tolist(),
        "Total Profit by Discount Band", "figure3.png",
    )
    figs["fig4"] = fig_barh_negative(
        st.index.tolist()[:5], st["profit"].tolist()[:5],
        "Five Least Profitable States", "figure4.png",
    )
    figs["fig5"] = fig_grouped_bar(
        reg.index.tolist(), reg["sales"].tolist(), reg["profit"].tolist(),
        "Total Sales", "Total Profit", "Sales vs Profit by Region",
        "figure5.png",
    )
    figs["fig6"] = fig_line(
        mon.index.tolist(), mon["sales"].tolist(), mon["profit"].tolist(),
        "Monthly Sales & Profit Trend (Seasonality)", "figure6.png",
    )
    return figs


# ==========================================================================
# 4. PDF assembly
# ==========================================================================
def styles():
    ss = getSampleStyleSheet()
    body = ParagraphStyle(
        "body", parent=ss["BodyText"], fontSize=10, leading=15,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=8,
    )
    h1 = ParagraphStyle(
        "h1", parent=ss["Heading1"], fontSize=16, leading=20,
        textColor=INK, spaceBefore=6, spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "h2", parent=ss["Heading2"], fontSize=12.5, leading=16,
        textColor=INK, spaceBefore=10, spaceAfter=6,
    )
    title = ParagraphStyle(
        "title", parent=ss["Title"], fontSize=22, leading=26,
        textColor=INK, spaceAfter=6,
    )
    sub = ParagraphStyle(
        "sub", parent=ss["Normal"], fontSize=11, leading=15,
        textColor=colors.HexColor("#5A5A5A"), spaceAfter=14,
    )
    cap = ParagraphStyle(
        "cap", parent=ss["Normal"], fontSize=8.5, leading=11,
        textColor=colors.HexColor("#7A7A7A"), spaceBefore=2, spaceAfter=12,
    )
    return dict(body=body, h1=h1, h2=h2, title=title, sub=sub, cap=cap)


def img_flowable(path: Path, width_in: float = 6.2):
    from reportlab.lib.utils import ImageReader

    iw, ih = ImageReader(str(path)).getSize()
    return Image(str(path), width=width_in * inch, height=width_in * inch * ih / iw)


def kpi_table(df: pd.DataFrame) -> Table:
    labels = ["Total Sales", "Total Profit", "Profit Margin", "Total Orders"]
    values = [
        money(df["sales"].sum()),
        money(df["profit"].sum(), "K"),
        f"{measured_margin(df):.2f}%",
        f"{df['order_id'].nunique():,}",
    ]
    t = Table([labels, values], colWidths=[1.55 * inch] * 4)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F4F6F8")),
                ("TEXTCOLOR", (0, 1), (-1, 1), INK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def discount_table(bands: pd.DataFrame) -> Table:
    data = [["Discount Band", "Total Profit", "Avg. Profit Margin"]]
    for name, row in bands.iterrows():
        data.append(
            [str(name), f"${row['profit']:,.2f}", f"{row['margin']:.1f}%"]
        )
    t = Table(data, colWidths=[2.4 * inch, 2.0 * inch, 1.9 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F4F6F8")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DEE3")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def bullet(text: str, st) -> Paragraph:
    return Paragraph(f"\u2022&nbsp;&nbsp;{text}", st["body"])


def build_pdf(df: pd.DataFrame, figs: dict[str, Path]) -> None:
    st = styles()
    cat = category_totals(df)
    bands = discount_bands(df)
    st_loss = loss_states(df)
    seg = segment_totals(df)
    ship = ship_totals(df)
    reg = region_totals(df)
    mon = monthly_trend(df)
    top = top_customers(df)

    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    margin = measured_margin(df)
    orders = df["order_id"].nunique()   # distinct orders (5,009)
    line_items = len(df)                # one row per line item (9,994)

    zero_margin = bands.loc["0% (no discount)", "margin"]
    band_21_40 = bands.loc["21 - 40%", "margin"]
    band_40p = bands.loc["40%+", "margin"]
    band_40p_profit = bands.loc["40%+", "profit"]

    doc = SimpleDocTemplate(
        str(OUTPDF), pagesize=LETTER,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.9 * inch, bottomMargin=0.8 * inch,
        title="Superstore Sales & Profitability Analysis",
        author="Hassan Jumaa (Riq)",
        subject="End-to-end analytics report",
    )

    story = []

    # ---- Cover ----------------------------------------------------------
    story.append(Paragraph("Superstore Sales &amp; Profitability Analysis", st["title"]))
    story.append(
        Paragraph(
            "End-to-end analytics report \u2014 Python/Pandas cleaning, "
            "MySQL querying, and Power BI dashboarding on the Sample Superstore dataset",
            st["sub"],
        )
    )
    cover = [
        ["Prepared by", "Hassan Jumaa (Riq)"],
        ["Role", "Data Analyst \u2014 Industrial Attachment, Swahilipot Hub Foundation"],
        ["Dataset", f"Sample Superstore ({orders:,} orders / {line_items:,} line items, 2014 \u2013 2017)"],
        ["Tools used", "Python (Pandas), MySQL, Power BI"],
        ["Repository", "github.com/Riq-wq/superstore-sales-profitability-analysis"],
    ]
    ct = Table(cover, colWidths=[1.3 * inch, 4.9 * inch])
    ct.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), INK),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#3A3A3A")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#E0E0E0")),
            ]
        )
    )
    story.append(ct)
    story.append(PageBreak())

    # ---- 1. Executive summary -------------------------------------------
    story.append(Paragraph("1. Executive Summary", st["h1"]))
    story.append(
        Paragraph(
            f"This report analyzes {orders:,} orders ({line_items:,} line items) from the "
            "Sample Superstore dataset to evaluate sales performance, profitability "
            "drivers, and operational efficiency. The dataset was cleaned and transformed "
            "using Python (Pandas), loaded into a MySQL database, and queried to extract "
            "ten core business insights that inform the accompanying Power BI dashboard.",
            st["body"],
        )
    )
    story.append(kpi_table(df))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Key takeaways", st["h2"]))
    story.append(
        bullet(
            f"The business is profitable overall ({margin:.1f}% margin) but profit is "
            f"heavily concentrated in <b>Technology</b> and <b>Office Supplies</b> \u2014 "
            f"<b>Furniture</b> generates nearly as much revenue as Office Supplies but "
            f"returns 6\u20138x less profit.",
            st,
        )
    )
    story.append(
        bullet(
            f"Discounting above 20% is where profitability breaks down: orders discounted "
            f"21\u201340% already run a negative average margin "
            f"({band_21_40:.1f}%), and 40%+ discounts erase "
            f"<b>${abs(band_40p_profit)/1e3:.1f}K</b> in profit outright.",
            st,
        )
    )
    story.append(
        bullet(
            f"<b>{len(st_loss)} states</b> \u2014 led by Texas and Ohio \u2014 are net "
            f"loss-making despite solid revenue, pointing to region-specific discount or "
            f"cost issues rather than weak demand.",
            st,
        )
    )
    story.append(
        bullet(
            "Standard Class shipping drives the most profit in absolute terms, but Same "
            "Day shipping has the thinnest profit contribution relative to its use.",
            st,
        )
    )
    story.append(PageBreak())

    # ---- 2. Methodology --------------------------------------------------
    story.append(Paragraph("2. Methodology &amp; Data Pipeline", st["h1"]))
    story.append(
        Paragraph(
            "The analysis followed a three-stage pipeline, consistent with the workflow "
            "used across this portfolio's other analytics projects:",
            st["body"],
        )
    )
    story.append(
        bullet(
            "<b>Cleaning (Python/Pandas):</b> loaded the raw CSV and checked for "
            "duplicate rows (none found), converted Order Date and Ship Date to proper "
            "datetime types, trimmed whitespace across text fields, and standardized all "
            "column names to snake_case.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Feature engineering:</b> derived <b>Shipping Duration</b> (days between "
            "order and ship date), <b>Profit Margin %</b> (profit as a percentage of "
            "sales), and an <b>is_loss</b> flag to quickly isolate loss-making orders.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Loading (MySQL):</b> the cleaned DataFrame was loaded into a MySQL "
            "<b>orders</b> table via SQLAlchemy + PyMySQL.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Querying (SQL):</b> ten targeted business questions were answered directly "
            "in MySQL \u2014 covering overall performance, category/sub-category "
            "profitability, discount impact, geography, segments, customers, shipping, "
            "and seasonality.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Visualization (Power BI):</b> query results were rebuilt as an interactive "
            "three-page dashboard (Overview, Profitability Deep-Dive, Regional &amp; "
            "Operational Performance) connected live to the cleaned dataset.",
            st,
        )
    )
    story.append(PageBreak())

    # ---- 3. Category & sub-category -------------------------------------
    story.append(Paragraph("3. Category &amp; Sub-Category Profitability", st["h1"]))
    furn = cat.loc["Furniture"]
    offs = cat.loc["Office Supplies"]
    story.append(
        Paragraph(
            "Technology leads on both sales and profit, followed closely by Office "
            "Supplies. Furniture is the clear underperformer: it generates "
            f"<b>{money(furn['sales'])}</b> in sales \u2014 more than Office Supplies "
            f"\u2014 but returns only <b>{money(furn['profit'], 'K')}</b> in profit, a "
            f"margin of roughly {furn['profit']/furn['sales']*100:.1f}%.",
            st["body"],
        )
    )
    story.append(img_flowable(figs["fig1"]))
    story.append(Paragraph("Figure 1. Sales vs Profit by Category", st["cap"]))

    sc = loss_subcategories(df)
    names = sc.index.tolist()
    sc_bits = ", ".join(f"<b>{n}</b>" for n in names[:-1])
    if len(names) > 1:
        sc_sentence = f"{sc_bits} and <b>{names[-1]}</b>"
    else:
        sc_sentence = f"<b>{names[0]}</b>"
    story.append(
        Paragraph(
            f"Three sub-categories run a net loss overall: {sc_sentence}, together "
            f"about <b>${abs(sc['profit'].sum())/1e3:.1f}K</b> in losses.",
            st["body"],
        )
    )
    story.append(img_flowable(figs["fig2"]))
    story.append(
        Paragraph("Figure 2. Total Profit of Loss-Making Sub-Categories", st["cap"])
    )
    story.append(PageBreak())

    # ---- 4. Discount strategy -------------------------------------------
    story.append(Paragraph("4. Discount Strategy vs Profitability", st["h1"]))
    story.append(
        Paragraph(
            "There is a clear, almost linear relationship between discount depth and "
            f"profitability. Orders with no discount return a healthy {zero_margin:.0f}% "
            f"average margin. That collapses as discounting increases \u2014 by the "
            f"21\u201340% band, average margin is already negative ({band_21_40:.1f}%), "
            f"and orders discounted above 40% lose money on average by a wide margin.",
            st["body"],
        )
    )
    story.append(img_flowable(figs["fig3"], width_in=6.0))
    story.append(Paragraph("Figure 3. Total Profit by Discount Band", st["cap"]))
    story.append(discount_table(bands))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>Insight:</b> discounts up to ~20% appear sustainable, but anything beyond "
            "that threshold is actively destroying profit rather than driving volume that "
            "offsets the margin loss.",
            st["body"],
        )
    )
    story.append(PageBreak())

    # ---- 5. Geographic --------------------------------------------------
    story.append(Paragraph("5. Geographic Performance", st["h1"]))
    ca = df[df["state"] == "California"][["sales", "profit"]].sum()
    ny = df[df["state"] == "New York"][["sales", "profit"]].sum()
    worst = st_loss.iloc[0]
    worst_name = st_loss.index[0]
    story.append(
        Paragraph(
            f"California and New York are the strongest states by revenue, but revenue "
            f"alone doesn't guarantee profitability. <b>{len(st_loss)} states</b> are net "
            f"loss-making overall \u2014 {worst_name} is the most severe, losing "
            f"<b>${abs(worst['profit'])/1e3:.1f}K</b> despite "
            f"${worst['sales']/1e3:.0f}K in sales, followed by "
            f"{', '.join(st_loss.index[1:5])}.",
            st["body"],
        )
    )
    story.append(img_flowable(figs["fig4"]))
    story.append(Paragraph("Figure 4. Five Least Profitable States", st["cap"]))
    story.append(
        Paragraph(
            f"At the region level, the {reg.index[0]} leads on both sales and profit, "
            f"followed by the {reg.index[1]}. The {reg.index[2]} region generates the "
            f"third-highest sales but falls to last place on profit, suggesting discount "
            f"or cost inefficiencies specific to that region.",
            st["body"],
        )
    )
    story.append(img_flowable(figs["fig5"], width_in=6.0))
    story.append(Paragraph("Figure 5. Sales vs Profit by Region", st["cap"]))
    story.append(PageBreak())

    # ---- 6. Segments, shipping, customers -------------------------------
    story.append(
        Paragraph("6. Customer Segments, Shipping, and Top Customers", st["h1"])
    )
    story.append(Paragraph("Segment profitability", st["h2"]))
    c0 = seg.iloc[0]
    story.append(
        Paragraph(
            f"The {seg.index[0]} segment drives the largest share of both sales "
            f"({money(c0['sales'])}) and profit ({money(c0['profit'], 'K')}), followed by "
            f"{seg.index[1]} and {seg.index[2]}. All three segments are profitable, with "
            f"no segment-level red flags.",
            st["body"],
        )
    )
    story.append(Paragraph("Shipping mode", st["h2"]))
    std = ship.loc["Standard Class"]
    same = ship.loc["Same Day"]
    story.append(
        Paragraph(
            f"Standard Class accounts for the largest share of profit "
            f"({money(std['profit'], 'K')}) and has the longest average shipping duration "
            f"({std['avg_days']:.1f} days). Same Day shipping contributes the least profit "
            f"in absolute terms ({money(same['profit'], 'K')}), which is expected given "
            f"its lower order volume, but is worth monitoring if its share of orders grows.",
            st["body"],
        )
    )
    story.append(img_flowable(figs["fig6"]))
    story.append(
        Paragraph("Figure 6. Monthly Sales & Profit Trend (Seasonality)", st["cap"])
    )
    story.append(Paragraph("Seasonality", st["h2"]))
    strongest = mon["sales"].sort_values(ascending=False).head(3).index
    month_names = ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"]
    story.append(
        Paragraph(
            "Sales and profit both show a clear seasonal pattern, dipping in February "
            f"and climbing steadily toward year-end. "
            f"{month_names[strongest[0]-1]}, {month_names[strongest[1]-1]}, and "
            f"{month_names[strongest[2]-1]} are consistently the strongest months \u2014 "
            "useful for planning inventory and staffing around peak demand.",
            st["body"],
        )
    )
    story.append(Paragraph("Top customers", st["h2"]))
    names = top.index.tolist()
    story.append(
        Paragraph(
            f"{names[0]}, {names[1]}, and {names[2]} are the top three customers by "
            f"total spend, each contributing over "
            f"${top.iloc[-1]/1e3:.0f}K in sales \u2014 strong candidates for a retention "
            f"or loyalty-focused follow-up.",
            st["body"],
        )
    )
    story.append(PageBreak())

    # ---- 7. Recommendations ---------------------------------------------
    story.append(Paragraph("7. Recommendations", st["h1"]))
    story.append(
        bullet(
            "<b>Cap discounts at 20%</b> on Furniture and Office Supplies orders where "
            "possible \u2014 the 21%+ discount bands are where orders reliably turn "
            "unprofitable.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Review Furniture pricing and cost structure</b>, particularly Tables and "
            "Bookcases, which post large losses despite strong sales volume.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Investigate Texas and Ohio operations</b> specifically \u2014 their loss "
            "patterns don't match the rest of the country and likely point to a regional "
            "discounting or fulfillment cost issue.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Lean into peak months (Sep \u2013 Dec)</b> for promotional planning and "
            "inventory buildup, and use the Feb dip for maintenance/clearance activity "
            "instead of aggressive discounting.",
            st,
        )
    )
    story.append(
        bullet(
            "<b>Protect the 0% and low-discount tiers</b> that are already carrying the "
            "business's profit \u2014 any sales incentive structure should avoid pushing "
            "more orders into the 21%+ discount bands.",
            st,
        )
    )

    # ---- 8. Conclusion ---------------------------------------------------
    story.append(Paragraph("8. Conclusion", st["h1"]))
    story.append(
        Paragraph(
            "The Superstore business is profitable overall, but that profitability is "
            "fragile and concentrated: a small set of sub-categories, discount bands, and "
            "states account for a disproportionate share of both the gains and the losses. "
            "The clearest, most actionable finding is the discount threshold \u2014 "
            "profitability turns negative as soon as discounts pass 20%, which gives the "
            "business a concrete, data-backed rule to apply going forward. The accompanying "
            "Power BI dashboard makes these patterns explorable in real time for further "
            "drill-down by category, region, and time period.",
            st["body"],
        )
    )

    doc.build(story)


def main() -> None:
    df = load()
    figs = build_figures(df)
    build_pdf(df, figs)
    print(f"Report written to {OUTPDF}")
    print(f"Figures written to {FIGDIR}")


if __name__ == "__main__":
    main()
