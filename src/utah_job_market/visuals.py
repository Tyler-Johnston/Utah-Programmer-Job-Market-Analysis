"""Publication-quality charts for the Utah programmer job market analysis."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
import pandas as pd
import seaborn as sns


NAVY = "#173B57"
BLUE = "#2E6F95"
TEAL = "#2A9D8F"
GOLD = "#E9A03B"
RUST = "#C65D3B"
INK = "#1B2631"
MUTED = "#5B6B75"
GRID = "#D9E1E5"


def configure_style() -> None:
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    plt.rcParams.update(
        {
            "figure.facecolor": "#FBFCFC",
            "axes.facecolor": "#FBFCFC",
            "axes.edgecolor": "#AEBCC4",
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titleweight": "bold",
            "text.color": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.dpi": 220,
            "savefig.bbox": "tight",
        }
    )


def _save(fig: plt.Figure, output_dir: Path, filename: str) -> None:
    fig.savefig(output_dir / filename, facecolor=fig.get_facecolor())
    plt.close(fig)


def _currency(value: float, _position: int) -> str:
    return f"${value / 1000:,.0f}k"


def _add_bar_labels(axis: plt.Axes, values: pd.Series, currency: bool = False) -> None:
    maximum = values.max()
    for bar, value in zip(axis.patches, values):
        label = f"${value:,.0f}" if currency else f"{value:,.0f}"
        axis.text(
            bar.get_width() + maximum * 0.015,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            fontsize=9,
            color=INK,
        )


def plot_salary_by_county(salaries: pd.DataFrame, output_dir: Path) -> None:
    summary = salaries.groupby("county", as_index=False)["annual_median"].mean().sort_values("annual_median")
    fig, axis = plt.subplots(figsize=(9.2, 5.4))
    sns.barplot(data=summary, x="annual_median", y="county", color=BLUE, ax=axis)
    axis.set(title="Median programmer pay by county", xlabel="Average annual median wage", ylabel="")
    axis.xaxis.set_major_formatter(FuncFormatter(_currency))
    _add_bar_labels(axis, summary["annual_median"], currency=True)
    axis.set_xlim(0, summary["annual_median"].max() * 1.18)
    _save(fig, output_dir, "median_salary_by_county.png")


def plot_salary_by_role(salaries: pd.DataFrame, output_dir: Path) -> None:
    summary = salaries.groupby("job_title", as_index=False)["annual_median"].mean().sort_values("annual_median")
    fig, axis = plt.subplots(figsize=(10.2, 5.6))
    sns.barplot(data=summary, x="annual_median", y="job_title", color=TEAL, ax=axis)
    axis.set(title="Median programmer pay by role", xlabel="Average annual median wage", ylabel="")
    axis.xaxis.set_major_formatter(FuncFormatter(_currency))
    _add_bar_labels(axis, summary["annual_median"], currency=True)
    axis.set_xlim(0, summary["annual_median"].max() * 1.18)
    _save(fig, output_dir, "median_salary_by_role.png")


def plot_affordability(affordability: pd.DataFrame, output_dir: Path) -> None:
    selected = pd.concat(
        [affordability.nlargest(6, "affordability_ratio"), affordability.nsmallest(6, "affordability_ratio")]
    ).drop_duplicates().sort_values("affordability_ratio")
    selected = selected.assign(label=selected["job_title"] + " — " + selected["county"].str.replace(" County", "", regex=False))
    colors = [RUST if value < 1 else TEAL for value in selected["affordability_ratio"]]
    fig, axis = plt.subplots(figsize=(10.5, 6.6))
    axis.barh(selected["label"], selected["affordability_ratio"], color=colors)
    axis.axvline(1, color=NAVY, linewidth=1.4, linestyle="--")
    axis.text(1.02, len(selected) - 0.55, "annual pay equals annual baseline cost", color=NAVY, fontsize=8.5)
    axis.set(
        title="Best and worst affordability outcomes",
        xlabel="Annual median wage ÷ annual cost for one adult, no children",
        ylabel="",
    )
    for bar, value in zip(axis.patches, selected["affordability_ratio"]):
        axis.text(value + 0.025, bar.get_y() + bar.get_height() / 2, f"{value:.2f}×", va="center", fontsize=9)
    axis.set_xlim(0, selected["affordability_ratio"].max() * 1.22)
    _save(fig, output_dir, "affordability_by_job_and_county.png")


def plot_new_jobs(projections: pd.DataFrame, output_dir: Path) -> None:
    summary = projections.groupby("county", as_index=False)["new_jobs"].sum().sort_values("new_jobs")
    fig, axis = plt.subplots(figsize=(9.2, 5.4))
    sns.barplot(data=summary, x="new_jobs", y="county", color=GOLD, ax=axis)
    axis.set(title="Projected new computer-occupation jobs by county", xlabel="Projected new jobs", ylabel="")
    _add_bar_labels(axis, summary["new_jobs"])
    axis.set_xlim(0, summary["new_jobs"].max() * 1.18)
    _save(fig, output_dir, "new_jobs_by_county.png")


def plot_job_growth(projections: pd.DataFrame, output_dir: Path) -> None:
    candidates = projections.dropna(subset=["annual_percent_change", "job_title"]).copy()
    selected = pd.concat(
        [candidates.nlargest(5, "annual_percent_change"), candidates.nsmallest(5, "annual_percent_change")]
    ).drop_duplicates().sort_values("annual_percent_change")
    selected["label"] = selected["job_title"] + " — " + selected["county"].str.replace(" County", "", regex=False)
    colors = [RUST if value < 0 else BLUE for value in selected["annual_percent_change"]]
    fig, axis = plt.subplots(figsize=(10.5, 6.2))
    axis.barh(selected["label"], selected["annual_percent_change"], color=colors)
    axis.axvline(0, color=NAVY, linewidth=1.1)
    axis.set(title="Fastest and slowest projected job growth", xlabel="Annual employment growth", ylabel="")
    axis.xaxis.set_major_formatter(PercentFormatter(xmax=100))
    for bar, value in zip(axis.patches, selected["annual_percent_change"]):
        offset = 0.06 if value >= 0 else -0.06
        alignment = "left" if value >= 0 else "right"
        axis.text(value + offset, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", va="center", ha=alignment, fontsize=9)
    _save(fig, output_dir, "job_growth_extremes.png")


def plot_model_predictions(model_results: pd.DataFrame, metrics: dict[str, float], output_dir: Path) -> None:
    fig, axis = plt.subplots(figsize=(7.4, 6.2))
    lower = min(model_results["annual_median"].min(), model_results["predicted_annual_median"].min())
    upper = max(model_results["annual_median"].max(), model_results["predicted_annual_median"].max())
    padding = (upper - lower) * 0.08
    axis.scatter(
        model_results["annual_median"],
        model_results["predicted_annual_median"],
        s=54,
        color=BLUE,
        edgecolor="white",
        linewidth=0.7,
        alpha=0.9,
    )
    axis.plot([lower - padding, upper + padding], [lower - padding, upper + padding], color=RUST, linewidth=1.5, linestyle="--", label="Perfect prediction")
    axis.set(
        title="Salary baseline: out-of-fold predictions",
        xlabel="Observed annual median wage",
        ylabel="Predicted annual median wage",
        xlim=(lower - padding, upper + padding),
        ylim=(lower - padding, upper + padding),
        aspect="equal",
    )
    axis.xaxis.set_major_formatter(FuncFormatter(_currency))
    axis.yaxis.set_major_formatter(FuncFormatter(_currency))
    axis.legend(frameon=False, loc="lower right")
    axis.text(
        0.04,
        0.96,
        f"5-fold CV  •  MAE \\${metrics['mae']:,.0f}  •  RMSE \\${metrics['rmse']:,.0f}\nR² {metrics['r2']:.2f}  •  n = {int(metrics['observations'])}",
        transform=axis.transAxes,
        va="top",
        fontsize=9,
        color=INK,
        bbox={"facecolor": "#FBFCFC", "edgecolor": "none", "pad": 4},
    )
    _save(fig, output_dir, "model_cross_validated_predictions.png")


def generate_all_figures(
    salaries: pd.DataFrame,
    affordability: pd.DataFrame,
    projections: pd.DataFrame,
    model_results: pd.DataFrame,
    metrics: dict[str, float],
    output_dir: Path | str,
) -> None:
    """Create the figure set used by the README and project report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    configure_style()
    plot_salary_by_county(salaries, output_path)
    plot_salary_by_role(salaries, output_path)
    plot_affordability(affordability, output_path)
    plot_new_jobs(projections, output_path)
    plot_job_growth(projections, output_path)
    plot_model_predictions(model_results, metrics, output_path)
