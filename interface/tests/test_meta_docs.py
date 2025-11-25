from pathlib import Path


def test_artifacts_doc_exists_and_lists_outputs():
    path = Path(__file__).resolve().parents[1] / "ARTIFACTS.md"
    assert path.exists()
    text = path.read_text().lower()
    for keyword in ["anonymize", "to_image", "transcode", "volume", "nifti"]:
        assert keyword in text


def test_tasks_doc_has_no_pending_markers():
    path = Path(__file__).resolve().parents[1] / "TASKS.md"
    if not path.exists():
        pytest.skip("TASKS.md ausente")
    text = path.read_text()
    # Basic guard to flag if placeholders remain
    assert "(Pend.)" not in text
