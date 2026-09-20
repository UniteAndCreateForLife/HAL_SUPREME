from hal_studio.shot_quality import evaluate_shot


def good_metrics():
    return {
        "imaging_quality": 0.90,
        "subject_consistency": 0.96,
        "background_consistency": 0.95,
        "motion_smoothness": 0.94,
        "dynamic_degree": 0.55,
        "contact_integrity": 0.91,
        "depth_occlusion": 0.92,
    }


def test_accepts_measured_good_shot():
    result = evaluate_shot(good_metrics(), contact_required=True)
    assert result.accepted
    assert not result.failures


def test_rejects_identity_drift():
    metrics = good_metrics()
    metrics["subject_consistency"] = 0.62
    result = evaluate_shot(metrics)
    assert not result.accepted
    assert any("subject_consistency" in failure for failure in result.failures)


def test_rejects_frozen_motion():
    metrics = good_metrics()
    metrics["dynamic_degree"] = 0.03
    result = evaluate_shot(metrics, motion_required=True)
    assert not result.accepted
    assert any("dynamic_degree" in failure for failure in result.failures)


def test_missing_measurement_fails_closed():
    metrics = good_metrics()
    del metrics["depth_occlusion"]
    result = evaluate_shot(metrics)
    assert not result.accepted
    assert "missing:depth_occlusion" in result.failures


def test_contact_metric_only_required_for_contact_shots():
    metrics = good_metrics()
    del metrics["contact_integrity"]
    assert evaluate_shot(metrics, contact_required=False).accepted
    assert not evaluate_shot(metrics, contact_required=True).accepted
