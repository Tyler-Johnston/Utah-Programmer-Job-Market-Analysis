"""Run the reproducible Utah programmer job-market analysis and write figures."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utah_job_market.analysis import build_affordability_table, evaluate_salary_model
from utah_job_market.data import BASELINE_HOUSEHOLD, load_cost_of_living, load_projection_data, load_salary_data
from utah_job_market.visuals import generate_all_figures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT, help="Directory containing the source workbooks.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "figures", help="Directory for generated charts.")
    args = parser.parse_args()

    salaries = load_salary_data(args.data_dir)
    costs = load_cost_of_living(args.data_dir, household=BASELINE_HOUSEHOLD)
    affordability = build_affordability_table(salaries, costs)
    projections = load_projection_data(args.data_dir)
    model_results, metrics = evaluate_salary_model(salaries)
    generate_all_figures(salaries, affordability, projections, model_results, metrics, args.output_dir)

    print(f"Generated 6 figures in {args.output_dir}")
    print(f"Affordability household baseline: {BASELINE_HOUSEHOLD} (one adult, no children)")
    print(f"Salary model: MAE ${metrics['mae']:,.0f}; RMSE ${metrics['rmse']:,.0f}; R² {metrics['r2']:.2f}")


if __name__ == "__main__":
    main()
