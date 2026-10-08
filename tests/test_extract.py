from datetime import datetime, timezone
import extract_issues as ex

def test_fara_watermark_porneste_de_la_backfill():
    assert ex.compute_since(None) == datetime(2008, 1, 1, tzinfo=timezone.utc)

def test_look_back_scade_48_de_ore():
    wm = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    assert ex.compute_since(wm) == datetime(2026, 10, 4, 12, tzinfo=timezone.utc)

def test_payload_ramane_complet():
    issue = {"id": 1, "updated_at": "2026-10-01T10:00:00Z", "title": "x"}
    row = ex.build_row(issue, "a/b", "r1", "2026-10-06T00:00:00+00:00", "gs://b/p")
    assert row["issue_id"] == 1 and row["payload"] == issue