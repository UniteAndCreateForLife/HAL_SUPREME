import unittest
from examples.agent_world_arena.brain_bridge import BrainRequest, BrainResponse


class CredentialAliasTests(unittest.TestCase):
    def test_authorization_token_alias_rejected(self):
        req = BrainRequest('ep', 0, 'a', 100, {}, ('idle',), 'req')
        reply = BrainResponse('req', 'ep', 0, 'a', {'kind': 'idle'},
                              diagnostics={'authorization_token': 'synthetic-canary'})
        with self.assertRaises(ValueError):
            reply.validate_against(req)

    def test_normalized_auth_aliases_rejected_recursively(self):
        for name in ('authorization_token', 'auth_token', 'id_token', 'session_token',
                     'AUTHORIZATION-TOKEN'):
            with self.subTest(field=name), self.assertRaises(ValueError):
                BrainRequest('ep', 0, 'a', 100, {'nested': [{name: 'synthetic'}]},
                             ('idle',), 'req').validate()

    def test_game_tokens_remain_valid(self):
        BrainRequest('ep', 0, 'a', 100, {'token_count': 5, 'tokens': [{'entity_id': 't1'}]},
                     ('idle',), 'req').validate()
