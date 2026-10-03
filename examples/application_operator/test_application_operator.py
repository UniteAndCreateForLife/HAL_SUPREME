import unittest

from examples.application_operator.application_operator import (
    approval_phrase,
    authorize_plan,
    build_application_plan,
    classify_field,
    mark_submitted,
)


class ApplicationOperatorTests(unittest.TestCase):
    def test_routine_identity_field_can_autofill_from_approved_profile(self):
        plan = build_application_plan(
            {"id": "demo", "provider": "Example", "title": "AI Evaluator"},
            [{"id": "email", "label": "Email address", "required": True}],
            {"email": "person@example.com"},
        )
        self.assertEqual(plan["fields"][0]["control"], "auto_fill")
        self.assertEqual(plan["fields"][0]["value"], "person@example.com")
        self.assertEqual(plan["blockers"], [])

    def test_legal_and_demographic_fields_require_confirmation(self):
        self.assertEqual(
            classify_field({"label": "Are you authorized to work in the United States?"}),
            "requires_confirmation",
        )
        self.assertEqual(
            classify_field({"label": "Voluntary disability status"}),
            "requires_confirmation",
        )

    def test_secrets_and_captcha_are_human_only(self):
        self.assertEqual(classify_field({"label": "One-time passcode"}), "human_only")
        self.assertEqual(classify_field({"label": "Complete CAPTCHA"}), "human_only")

    def test_open_text_response_is_draft_only(self):
        self.assertEqual(
            classify_field({"label": "Why would you be a good fit?", "type": "textarea"}),
            "draft_only",
        )

    def test_plan_cannot_be_authorized_with_unresolved_required_field(self):
        plan = build_application_plan(
            {"id": "demo"},
            [{"id": "portfolio", "label": "Portfolio link", "required": True}],
            {},
        )
        with self.assertRaises(ValueError):
            authorize_plan(plan, approval_phrase(plan))

    def test_exact_reviewed_plan_can_be_authorized(self):
        plan = build_application_plan(
            {"id": "demo"},
            [{"id": "portfolio", "label": "Portfolio link", "required": True}],
            {"portfolio": "https://example.com/work"},
        )
        approved = authorize_plan(plan, approval_phrase(plan))
        self.assertEqual(approved["stage"], "approved")
        self.assertTrue(approved["submission_authorized"])

    def test_submitted_requires_real_receipt(self):
        plan = build_application_plan(
            {"id": "demo"},
            [{"id": "portfolio", "label": "Portfolio link", "required": True}],
            {"portfolio": "https://example.com/work"},
        )
        approved = authorize_plan(plan, approval_phrase(plan))
        with self.assertRaises(ValueError):
            mark_submitted(approved, {})
        submitted = mark_submitted(approved, {"id": "receipt-123"})
        self.assertEqual(submitted["stage"], "submitted")


if __name__ == "__main__":
    unittest.main()
