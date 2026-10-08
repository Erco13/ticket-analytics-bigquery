import os
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = "EU"
BUCKET = f"{PROJECT_ID}-raw"
RAW_TABLE = f"{PROJECT_ID}.raw.github_issues"
RUNS_TABLE = f"{PROJECT_ID}.ops.pipeline_runs"
REPOS = ["streamlit/streamlit", "pandas-dev/pandas", "microsoft/PowerToys"]
BACKFILL_START = "2008-01-01T00:00:00Z"  # istoric complet, necesar pentru backlog
LOOKBACK_HOURS = 48