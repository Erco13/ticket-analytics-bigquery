import json, os, sys, tempfile, uuid
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery, storage
from config import (PROJECT_ID, LOCATION, BUCKET, RAW_TABLE, RUNS_TABLE,
                    REPOS, BACKFILL_START, LOOKBACK_HOURS)
from github_client import make_session, fetch_issues

def compute_since(watermark):
    if watermark is None:
        return datetime.fromisoformat(BACKFILL_START)
    return watermark - timedelta(hours=LOOKBACK_HOURS)

def get_watermark(bq, repo):
    job = bq.query(
        f"SELECT MAX(updated_at) AS wm FROM `{RAW_TABLE}` WHERE repo = @repo",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("repo", "STRING", repo)]),
        location=LOCATION)
    return next(iter(job.result())).wm

def build_row(issue, repo, run_id, ingested_at, uri):
    return {"repo": repo, "issue_id": issue["id"], "updated_at": issue["updated_at"],
            "payload": issue, "_run_id": run_id,
            "_ingested_at": ingested_at, "_source_uri": uri}

def run_repo(bq, gcs, session, repo):
    run_id = uuid.uuid4().hex
    started = datetime.now(timezone.utc)
    since = compute_since(get_watermark(bq, repo))
    path = (f"github/issues/repo={repo.replace('/', '__')}/"
            f"dt={started:%Y-%m-%d}/{run_id}.ndjson")
    uri = f"gs://{BUCKET}/{path}"
    n, max_updated = n + 1, max(max_updated or "", issue["updated_at"])
    with tempfile.NamedTemporaryFile("w", suffix=".ndjson", delete=False,
                                     encoding="utf-8") as f:
        for issue in fetch_issues(session, repo, since.strftime("%Y-%m-%dT%H:%M:%SZ")):
            row = build_row(issue, repo, run_id, started.isoformat(), uri)
            f.write(json.dumps(row) + "\n")
            n, max_updated = n + 1, issue["updated_at"]
        local_path = f.name
    if n:
        gcs.bucket(BUCKET).blob(path).upload_from_filename(local_path)
        bq.load_table_from_uri(uri, RAW_TABLE, location=LOCATION,
            job_config=bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND)).result()
    os.remove(local_path)
    return {"run_id": run_id, "repo": repo, "started_at": started.isoformat(),
            "since_param": since.isoformat(), "max_updated_at": max_updated,
            "rows_loaded": n}

def log_run(bq, record):
    bq.load_table_from_json([record], RUNS_TABLE, location=LOCATION,
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND)).result()

def main():
    bq, gcs = bigquery.Client(PROJECT_ID), storage.Client(PROJECT_ID)
    session, failed = make_session(), False
    for repo in REPOS:
        try:
            rec = run_repo(bq, gcs, session, repo)
            rec.update(status="success", error_message=None)
        except Exception as e:
            failed = True
            rec = {"run_id": uuid.uuid4().hex, "repo": repo,
                   "status": "failed", "error_message": str(e)[:1000]}
        rec["finished_at"] = datetime.now(timezone.utc).isoformat()
        log_run(bq, rec)
        print(rec)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()