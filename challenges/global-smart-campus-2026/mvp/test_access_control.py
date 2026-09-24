import unittest

from access_control import authorize_action, validate_tenant_id


class AccessControlTests(unittest.TestCase):
    def test_valid_short_tenant_ids_are_accepted(self):
        for tenant_id in ("a", "ab", "campus-1"):
            self.assertEqual(validate_tenant_id(tenant_id), tenant_id)

    def test_max_length_tenant_id_is_accepted(self):
        tenant_id = "a" * 64
        self.assertEqual(validate_tenant_id(tenant_id), tenant_id)

    def test_overlength_tenant_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid tenant_id"):
            validate_tenant_id("a" * 65)

    def test_invalid_tenant_boundaries_and_characters_are_rejected(self):
        for tenant_id in ("", "-campus", "campus-", "Campus", "campus/other"):
            with self.subTest(tenant_id=tenant_id):
                with self.assertRaisesRegex(ValueError, "invalid tenant_id"):
                    validate_tenant_id(tenant_id)

    def test_unknown_role_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "unknown actor role"):
            authorize_action(
                actor_role="administrator",
                action="case:read",
                actor_tenant_id="campus-a",
                resource_tenant_id="campus-a",
            )

    def test_analyst_cannot_read_audit(self):
        with self.assertRaisesRegex(PermissionError, "not authorized"):
            authorize_action(
                actor_role="analyst",
                action="audit:read",
                actor_tenant_id="campus-a",
                resource_tenant_id="campus-a",
            )

    def test_reviewer_can_close_review(self):
        authorize_action(
            actor_role="reviewer",
            action="review:close",
            actor_tenant_id="campus-a",
            resource_tenant_id="campus-a",
        )

    def test_matching_tenant_scope_allows_authorized_action(self):
        authorize_action(
            actor_role="auditor",
            action="audit:read",
            actor_tenant_id="campus-a",
            resource_tenant_id="campus-a",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
