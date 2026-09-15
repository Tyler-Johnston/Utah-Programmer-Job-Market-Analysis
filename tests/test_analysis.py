from pathlib import Path
import unittest

from utah_job_market.analysis import build_affordability_table, evaluate_salary_model
from utah_job_market.data import BASELINE_HOUSEHOLD, load_cost_of_living, load_projection_data, load_salary_data


ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_affordability_has_one_cost_baseline_per_salary_observation(self):
        salaries = load_salary_data(ROOT)
        costs = load_cost_of_living(ROOT, BASELINE_HOUSEHOLD)
        affordability = build_affordability_table(salaries, costs)

        self.assertEqual(len(affordability), len(salaries))
        self.assertTrue(affordability["household"].eq(BASELINE_HOUSEHOLD).all())
        self.assertTrue(affordability["affordability_ratio"].notna().all())

    def test_projection_rows_have_counties_and_nonnegative_new_jobs(self):
        projections = load_projection_data(ROOT)

        self.assertTrue(projections["county"].notna().all())
        self.assertTrue((projections["new_jobs"] >= 0).all())

    def test_salary_model_returns_one_out_of_fold_prediction_per_salary(self):
        salaries = load_salary_data(ROOT)
        results, metrics = evaluate_salary_model(salaries)

        self.assertEqual(len(results), len(salaries))
        self.assertTrue(results["predicted_annual_median"].notna().all())
        self.assertEqual(metrics["observations"], len(salaries))
