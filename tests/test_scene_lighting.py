from hal_studio.scene_lighting import evaluate_scene_lighting


def good():
    return {
        "subject_scene_harmony": 0.88,
        "temporal_stability": 0.91,
        "key_direction_consistency": 0.86,
        "unmotivated_light_change": 0.04,
        "contact_shadow_consistency": 0.84,
    }


def test_accepts_coherent_lighting():
    assert evaluate_scene_lighting(good(), shot_id="011", evaluator_id="light-v1").accepted


def test_rejects_flicker():
    e = good(); e["temporal_stability"] = 0.40
    d = evaluate_scene_lighting(e, shot_id="011", evaluator_id="light-v1")
    assert not d.accepted and "flicker" in d.reasons[0]


def test_rejects_wrong_key_direction():
    e = good(); e["key_direction_consistency"] = 0.30
    assert not evaluate_scene_lighting(e, shot_id="011", evaluator_id="light-v1").accepted


def test_rejects_unmotivated_change():
    e = good(); e["unmotivated_light_change"] = 0.50
    assert not evaluate_scene_lighting(e, shot_id="011", evaluator_id="light-v1").accepted


def test_contact_shadows_required_for_contact_shot():
    e = good(); del e["contact_shadow_consistency"]
    assert not evaluate_scene_lighting(e, shot_id="020", evaluator_id="light-v1", contact_critical=True).accepted


def test_rejects_bad_contact_shadow():
    e = good(); e["contact_shadow_consistency"] = 0.20
    assert not evaluate_scene_lighting(e, shot_id="020", evaluator_id="light-v1", contact_critical=True).accepted


def test_invalid_metric_fails_closed():
    e = good(); e["subject_scene_harmony"] = 1.4
    assert not evaluate_scene_lighting(e, shot_id="011", evaluator_id="light-v1").accepted
