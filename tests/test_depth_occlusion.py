import pytest

from hal_studio.depth_occlusion import GeometryObservation, evaluate_depth_occlusion


def obs(frame, depth=.90, occ=.91, contact=None, flips=.01):
    return GeometryObservation(frame, depth, occ, contact, flips)


def test_accepts_coherent_geometry():
    result = evaluate_depth_occlusion([obs(0), obs(12), obs(24)], evaluator="geometry-v1")
    assert result.accepted
    assert result.failures == ()


def test_rejects_occlusion_contradiction():
    result = evaluate_depth_occlusion([obs(0), obs(12, occ=.41)], evaluator="geometry-v1")
    assert not result.accepted
    assert any(x.startswith("occlusion_error") for x in result.failures)


def test_rejects_unmotivated_depth_order_flip():
    result = evaluate_depth_occlusion([obs(0), obs(12, flips=.22)], evaluator="geometry-v1")
    assert not result.accepted
    assert any(x.startswith("depth_order_flip") for x in result.failures)


def test_contact_shot_requires_contact_depth_evidence():
    result = evaluate_depth_occlusion([obs(0), obs(12)], evaluator="geometry-v1", require_contact=True)
    assert not result.accepted
    assert "missing_contact_depth_evidence" in result.failures


def test_contact_shot_rejects_bad_contact_plane():
    result = evaluate_depth_occlusion([obs(0, contact=.88), obs(12, contact=.44)], evaluator="geometry-v1", require_contact=True)
    assert not result.accepted
    assert any(x.startswith("contact_depth_error") for x in result.failures)


def test_missing_depth_fails_closed():
    result = evaluate_depth_occlusion([obs(0, depth=None)], evaluator="geometry-v1")
    assert not result.accepted
    assert any(x.startswith("missing_depth_evidence") for x in result.failures)


def test_rejects_non_normalized_metric():
    with pytest.raises(ValueError):
        evaluate_depth_occlusion([obs(0, depth=1.2)], evaluator="geometry-v1")
