"""Exercise the complete trusted worker against an in-memory GitHub API, never the network."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import process_submission as worker


class SubmissionFlow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('tools', 'scenarios'):
            shutil.copytree(ROOT / folder, self.root / folder)
        package = json.loads((ROOT / 'scenarios/qscenario.daily_opsec.json').read_text(encoding='utf-8'))
        package['id'] = package['scenario']['id'] = 'fixture.submission'
        body = 'Q-P1NG marketplace submission. Manual maintainer review required.\n\n```json\n' + json.dumps(package) + '\n```\n'
        self.event = {'action': 'labeled', 'label': {'name': 'marketplace-submission'},
                      'issue': {'number': 7, 'body': body}, 'repository': {'default_branch': 'main'}}
        self.event_path = self.root / 'event.json'
        self.event_path.write_text(json.dumps(self.event), encoding='utf-8')
        self.base = 'a' * 40
        self.tree = 'b' * 40
        self.commit = 'c' * 40
        self.branch = None
        self.pr = None
        self.fail_pr = False
        self.foreign_branch = False
        self.mutations = []

    def api(self, request, timeout):
        self.assertEqual(timeout, 30)
        self.assertTrue(request.full_url.startswith('https://api.github.com/repos/fixture/catalog/'))
        path = request.full_url.removeprefix('https://api.github.com/repos/fixture/catalog')
        data = json.loads(request.data) if request.data else None
        if data is not None:
            self.mutations.append((path, data))
        if path == '/issues/7':
            value = dict(self.event['issue'], labels=[{'name': 'marketplace-submission'}])
        elif path.startswith('/pulls?'):
            value = [self.pr] if self.pr else []
        elif path == '/git/commits/' + self.base:
            value = {'tree': {'sha': 'd' * 40}}
        elif path == '/git/trees':
            self.assertEqual({x['path'] for x in data['tree']}, {'index.json', 'scenarios/fixture.submission.json'})
            value = {'sha': self.tree}
        elif path.startswith('/git/ref/heads/'):
            if self.branch is None:
                raise urllib.error.HTTPError(request.full_url, 404, 'Not found', {}, None)
            value = {'object': {'sha': self.commit}}
        elif path == '/git/commits/' + self.commit:
            value = {'tree': {'sha': 'e' * 40 if self.foreign_branch else self.tree}, 'parents': [{'sha': self.base}]}
        elif path == '/git/commits':
            value = {'sha': self.commit}
        elif path == '/git/refs':
            self.assertIsNone(self.branch)
            self.branch = data['ref']
            value = {'ref': self.branch}
        elif path == '/pulls':
            if self.fail_pr:
                raise urllib.error.HTTPError(request.full_url, 403, 'Not allowed', {}, None)
            self.assertTrue(data['draft'])
            self.assertEqual(data['base'], 'main')
            self.pr = {'number': 8}
            value = self.pr
        else:
            self.fail('Unexpected API operation: ' + path)
        return io.BytesIO(json.dumps(value).encode())

    def run_worker(self):
        # Each GitHub retry checks out the unchanged default branch in a fresh runner.
        (self.root / 'scenarios/fixture.submission.json').unlink(missing_ok=True)
        env = {'GITHUB_EVENT_PATH': str(self.event_path), 'GITHUB_REPOSITORY': 'fixture/catalog', 'GITHUB_TOKEN': 'synthetic-token'}
        with patch.dict(os.environ, env), patch.object(worker, '__file__', str(self.root / 'scripts/process_submission.py')), \
             patch.object(worker.subprocess, 'check_output', return_value=self.base), \
             patch.object(worker.urllib.request, 'urlopen', side_effect=self.api), contextlib.redirect_stdout(io.StringIO()):
            worker.main()

    def test_creates_only_data_and_draft_pr_then_deduplicates(self):
        self.run_worker()
        count = len(self.mutations)
        self.run_worker()
        self.assertEqual(len(self.mutations), count)
        self.assertIsNotNone(self.pr)

    def test_recovers_if_pr_permission_failed_after_branch_creation(self):
        self.fail_pr = True
        with self.assertRaises(RuntimeError):
            self.run_worker()
        self.fail_pr = False
        self.run_worker()
        self.assertEqual(sum(path == '/git/refs' for path, _ in self.mutations), 1)
        self.assertIsNotNone(self.pr)

    def test_never_reuses_or_overwrites_a_different_branch(self):
        self.branch = 'refs/heads/existing'
        self.foreign_branch = True
        with self.assertRaises(ValueError):
            self.run_worker()
        self.assertFalse(any(path in ('/pulls', '/git/refs') for path, _ in self.mutations))


if __name__ == '__main__':
    unittest.main()
