import unittest

from hal_studio.identity_tracking import IdentityObservation, evaluate_identity


class IdentityTrackingTests(unittest.TestCase):
    def test_accepts_consistent_identity(self):
        rows = [
            IdentityObservation(0, .78, .70, .74),
            IdentityObservation(12, .73, .68, .72),
            IdentityObservation(24, .75, .66, .71),
        ]
        self.assertTrue(evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1").accepted)

    def test_rejects_single_frame_face_drift(self):
        rows = [IdentityObservation(0, .76, .70, .70), IdentityObservation(12, .42, .69, .70)]
        decision = evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1")
        self.assertFalse(decision.accepted)
        self.assertTrue(any(x.startswith("face_identity_drift") for x in decision.failures))

    def test_rejects_temporal_face_drift_even_when_frames_clear_minimum(self):
        rows = [IdentityObservation(0, .80, .70, .70), IdentityObservation(12, .60, .70, .70)]
        decision = evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1")
        self.assertFalse(decision.accepted)
        self.assertTrue(any(x.startswith("temporal_face_drift") for x in decision.failures))

    def test_profile_shot_can_use_body_and_wardrobe_when_face_not_required(self):
        rows = [IdentityObservation(0, None, .72, .77), IdentityObservation(12, None, .69, .73)]
        self.assertTrue(evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1", require_face=False).accepted)

    def test_missing_face_fails_closed_when_required(self):
        rows = [IdentityObservation(0, None, .72, .77)]
        decision = evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1")
        self.assertFalse(decision.accepted)
        self.assertIn("missing_face_identity_evidence", decision.failures)

    def test_rejects_wardrobe_drift(self):
        rows = [IdentityObservation(0, .75, .70, .31)]
        decision = evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1")
        self.assertFalse(decision.accepted)
        self.assertTrue(any(x.startswith("wardrobe_drift") for x in decision.failures))

    def test_invalid_normalized_metric_raises(self):
        rows = [IdentityObservation(0, 1.2, .70, .70)]
        with self.assertRaises(ValueError):
            evaluate_identity(rows, reference_id="tommy-v1", evaluator="fixture-v1")


if __name__ == "__main__":
    unittest.main()
