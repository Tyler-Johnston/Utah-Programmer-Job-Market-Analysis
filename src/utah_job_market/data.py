"""Load and validate the project source datasets."""

from pathlib import Path

import pandas as pd


COUNTY_MAPPING = {
    "Cache": "Cache County",
    "Central Southwest Utah": "Beaver County",
    "Eastern Utah": "Carbon County",
    "Ogden-Clearfield Metro": "Weber County",
    "Provo-Orem Metro": "Utah County",
    "Salt Lake Metro": "Salt Lake County",
    "St George Metro": "Washington County",
}
EXCLUDED_AREAS = {"United States", "Statewide"}
BASELINE_HOUSEHOLD = "1p0c"


def _path(data_dir: Path | str, name: str) -> Path:
    path = Path(data_dir) / name
    if not path.exists():
        raise FileNotFoundError(f"Expected source file was not found: {path}")
    return path


def add_county(frame: pd.DataFrame, area_column: str) -> pd.DataFrame:
    """Map workforce reporting areas to the county used for cost data."""
    result = frame.copy()
    result["county"] = result[area_column].map(COUNTY_MAPPING)
    unmatched = result.loc[
        ~result[area_column].isin(EXCLUDED_AREAS) & result["county"].isna(), area_column
    ].dropna().unique()
    if len(unmatched):
        raise ValueError(f"Unmapped workforce areas: {', '.join(sorted(unmatched))}")
    return result


def load_salary_data(data_dir: Path | str = ".") -> pd.DataFrame:
    """Load usable wage observations from the consolidated 2024 workbook."""
    salaries = pd.read_excel(_path(data_dir, "wages.xlsx"))
    required = {"Job Title", "Area Name", "Annual Inexperienced", "Annual Median"}
    missing = required.difference(salaries.columns)
    if missing:
        raise ValueError(f"wages.xlsx is missing columns: {', '.join(sorted(missing))}")

    salaries = salaries.loc[~salaries["Area Name"].isin(EXCLUDED_AREAS)].copy()
    salaries = salaries.dropna(subset=["Annual Median"])
    salaries = add_county(salaries, "Area Name")
    return salaries.rename(
        columns={
            "Job Title": "job_title",
            "Area Name": "workforce_area",
            "Annual Inexperienced": "annual_inexperienced",
            "Annual Median": "annual_median",
        }
    )


def load_cost_of_living(
    data_dir: Path | str = ".", household: str = BASELINE_HOUSEHOLD
) -> pd.DataFrame:
    """Load Utah annual household costs for one explicitly named household type."""
    costs = pd.read_excel(_path(data_dir, "fbc_data_2024.xlsx"), sheet_name="County", header=1)
    costs = costs.loc[
        (costs["State abv."] == "UT") & (costs["Family"] == household),
        ["County", "Family", "Total.1"],
    ].copy()
    costs = costs.rename(
        columns={"County": "county", "Family": "household", "Total.1": "annual_cost"}
    )
    if costs.empty:
        raise ValueError(f"No Utah cost-of-living records found for household '{household}'.")
    if costs["county"].duplicated().any():
        raise ValueError("Cost-of-living data has more than one row per county and household.")
    return costs


def load_projection_data(data_dir: Path | str = ".") -> pd.DataFrame:
    """Load projections only for detailed occupations represented in the wage source.

    The projections workbook includes roll-up categories such as ``Computer
    Occupations``. Joining it to the detailed wage workbook removes those
    aggregates and prevents counting a roll-up and its component occupations.
    """
    wage_reference = pd.read_excel(
        _path(data_dir, "Wage.xlsx"),
        names=[
            "job_title",
            "workforce_area",
            "hourly_inexperienced",
            "hourly_median",
            "annual_inexperienced",
            "annual_median",
            "training",
            "education",
            "experience",
        ],
        skiprows=1,
    )
    projections = pd.read_excel(_path(data_dir, "projection.xlsx"))
    projections = projections.rename(
        columns={
            "Job Title": "job_title",
            "Area Name": "workforce_area",
            "Current Employment": "current_employment",
            "Projected Employment": "projected_employment",
            "Annual %Change": "annual_percent_change",
            "Total Annual Openings": "annual_openings",
        }
    )
    required = {"workforce_area", "current_employment", "projected_employment"}
    missing = required.difference(projections.columns)
    if missing:
        raise ValueError(f"projection.xlsx is missing columns: {', '.join(sorted(missing))}")

    projections = projections.merge(
        wage_reference[["job_title", "workforce_area"]].dropna().drop_duplicates(),
        on=["job_title", "workforce_area"],
        how="inner",
        validate="one_to_one",
    )
    projections = projections.loc[~projections["workforce_area"].isin(EXCLUDED_AREAS)].copy()
    projections = add_county(projections, "workforce_area")
    projections["new_jobs"] = (
        projections["projected_employment"] - projections["current_employment"]
    ).clip(lower=0)
    return projections
