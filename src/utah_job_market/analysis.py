"""Core calculations for affordability, opportunity, and salary-model evaluation."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def build_affordability_table(salaries: pd.DataFrame, costs: pd.DataFrame) -> pd.DataFrame:
    """Join each salary observation to one county-level household-cost baseline."""
    affordability = salaries.merge(costs, on="county", how="inner", validate="many_to_one")
    if len(affordability) != len(salaries):
        raise ValueError("Some salary observations have no matching county cost-of-living record.")
    affordability["affordability_ratio"] = (
        affordability["annual_median"] / affordability["annual_cost"]
    )
    return affordability.sort_values("affordability_ratio", ascending=False).reset_index(drop=True)


def evaluate_salary_model(salaries: pd.DataFrame, folds: int = 5) -> tuple[pd.DataFrame, dict[str, float]]:
    """Evaluate an additive county-and-role salary baseline with out-of-fold predictions."""
    features = salaries[["county", "job_title"]]
    target = salaries["annual_median"]
    pipeline = Pipeline(
        [
            (
                "encode_categories",
                ColumnTransformer(
                    [("categories", OneHotEncoder(handle_unknown="ignore"), features.columns)]
                ),
            ),
            ("model", LinearRegression()),
        ]
    )
    cv = KFold(n_splits=folds, shuffle=True, random_state=42)
    predictions = cross_val_predict(pipeline, features, target, cv=cv)
    results = salaries[["job_title", "county", "annual_median"]].copy()
    results["predicted_annual_median"] = predictions
    metrics = {
        "mae": float(mean_absolute_error(target, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(target, predictions))),
        "r2": float(r2_score(target, predictions)),
        "observations": float(len(results)),
    }
    return results, metrics
