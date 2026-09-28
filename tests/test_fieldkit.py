"""Validate reviewed examples as data; CI never executes a downloaded shell script."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from catalog import load, validate, build_index, minimum_app_code


class FieldKitTests(unittest.TestCase):
    def packages(self, folder):
        return [validate(load(p.read_bytes())) for p in (ROOT/folder).glob('*fieldkit.*.json')]

    def test_tool_prerequisites_and_finite_execution(self):
        specs = json.loads((ROOT/'docs/fieldkit-requirements.json').read_text())['tools']
        tools = self.packages('tools')
        self.assertEqual(set(specs), {p['id'] for p in tools})
        self.assertEqual(14, len(tools))
        for p in tools:
            m = p['files']['manifest.json']
            self.assertEqual('OFF', m['policy']['executionMode'])
            self.assertFalse(m['policy']['networkDefault'])
            self.assertFalse(m['permissions']['workspaceWrite'])
            self.assertIn('/workspace/fieldkit', m['description'])
            self.assertLessEqual(len(m['name']), 48)
            for package in specs[p['id']]['packages']:
                self.assertIn(package, m['description'])
            nodes = p['files']['actions.json']['nodes']
            processes = [n for n in nodes if n['type']=='process.bash']
            self.assertEqual(1, len(processes))
            config = processes[0]['config']
            self.assertEqual(specs[p['id']]['timeoutSeconds'], config['timeout'])
            self.assertTrue(1 <= config['timeout'] <= 60)
            self.assertLess(len(config['command']), 4096)
            # Inputs are fixed local filenames, not shell interpolation of chat text or QVars.
            self.assertNotIn('{{', config['command'])
            self.assertNotIn('eval ', config['command'])
            self.assertIn('check_file()', config['command'])
            ids = {n['id'] for n in nodes}
            for n in nodes:
                for output in n.get('outputs',[]):
                    for target in output['targets']:
                        self.assertIn(target.split(':')[0], ids)

    def test_scenario_references_are_available_and_manual(self):
        tools = {p['id']:p for p in self.packages('tools')}
        scenarios = self.packages('scenarios')
        self.assertEqual(12, len(scenarios))
        for p in scenarios:
            s=p['scenario']
            self.assertFalse(s['enabled'])
            self.assertEqual(0,s['runCount'])
            for a in s['actions']:
                self.assertFalse(a.get('storeResultIn'))
                if a['type']=='RUN_ACTION_FORGE_TOOL':
                    self.assertIn(a['toolId'],tools)
                    self.assertEqual('MANUAL',s['trigger']['type'])
                    if tools[a['toolId']]['risk']=='HIGH':self.assertEqual('HIGH',p['risk'])
                if a['type']=='SHOW_NOTIFICATION':
                    self.assertNotIn('%Q_',a['text'])
            if s['trigger']['type']!='MANUAL':
                self.assertTrue(all(a['type'] in ('SHOW_NOTIFICATION','CLEAR_QVAR') for a in s['actions']))

    def test_only_explicit_loopback_lab_declares_network(self):
        for p in self.packages('tools'):
            m=p['files']['manifest.json']
            is_lab=p['id']=='fieldkit.ffuf_loopback'
            self.assertEqual(is_lab,m['permissions']['network'])
            self.assertEqual(is_lab,m['permissions']['securityLab'])
            if is_lab:
                self.assertEqual(['127.0.0.1:8080'],m['network']['allowedHosts'])
                code=p['files']['actions.json']['nodes'][1]['config']['command']
                for bound in ('-t 1','-rate 2','-maxtime 20','-timeout 2'):
                    self.assertIn(bound,code)

    def test_minimum_app_version_keeps_existing_examples_compatible(self):
        entries=build_index(ROOT)['entries']
        new=[e for e in entries if e['id'].startswith(('fieldkit.','qscenario.fieldkit.'))]
        old=[e for e in entries if e not in new]
        self.assertEqual(26,len(new))
        self.assertEqual(37,len(old))
        self.assertTrue(all(e['minAppCode']==175 for e in new))
        self.assertTrue(all(e['minAppCode']==172 for e in old))

    def test_scenario_limits_match_android(self):
        p=self.packages('scenarios')[0]
        bad=copy.deepcopy(p);bad['scenario']['actions']*=21
        with self.assertRaises(ValueError):validate(bad)
        bad=copy.deepcopy(p);bad['scenario']['conditions']=[{'type':'IS_CHARGING'}]*6
        with self.assertRaises(ValueError):validate(bad)

    def test_no_destructive_or_distributing_scenario_actions(self):
        for p in self.packages('scenarios'):
            for action in p['scenario']['actions']:
                self.assertIn(action['type'], ('RUN_ACTION_FORGE_TOOL','SET_QVAR','CLEAR_QVAR','SHOW_NOTIFICATION'))


if __name__=='__main__':unittest.main()
