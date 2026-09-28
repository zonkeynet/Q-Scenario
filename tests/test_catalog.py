import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from catalog import load,encoded,validate,build_index,package_path
from process_submission import extract

class CatalogTests(unittest.TestCase):
    def package(self):
        return load((ROOT/'tools/starter.sha256_text.json').read_bytes())
    def test_complete_catalog(self):
        self.assertGreaterEqual(len(build_index(ROOT)['entries']),37)
    def test_index_matches_payloads(self):
        self.assertEqual(encoded(build_index(ROOT)),(ROOT/'index.json').read_bytes())
    def test_path_traversal_and_non_data_files(self):
        for bad in ('../secret','a/b','a..b','a\\b','a\x00b'):
            pkg=self.package();pkg['id']=bad
            with self.assertRaises(ValueError):package_path(pkg)
        pkg=self.package();pkg['files']['.github/workflows/evil.yml']={}
        with self.assertRaises(ValueError):validate(pkg)
    def test_duplicates_nan_depth_size(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}', b'['*33+b']'*33,b' '*262145):
            with self.assertRaises(ValueError):load(raw)
    def test_label_control_and_risk_mismatch(self):
        for change in ({'name':'hidden\u202ename'},{'risk':'LOWER'}):
            pkg=self.package();pkg.update(change)
            with self.assertRaises(ValueError):validate(pkg)
        pkg=self.package();pkg['risk']='HIGH'
        with self.assertRaises(ValueError):validate(pkg)
    def test_scripts_are_never_executed(self):
        pkg=self.package();pkg['files']['actions.json']['nodes'][0]['config']={'script':'raise Exception("must never execute")'}
        self.assertEqual(pkg,validate(pkg))
    def test_issue_roundtrip_with_fences_and_shell_metacharacters(self):
        pkg=self.package();pkg['files']['actions.json']['nodes'][0]['config']={'script':'``` $(touch /tmp/never) ${{ secrets.TOKEN }}'}
        body='Q-P1NG marketplace submission. Manual maintainer review required.\n\n```json\n'+encoded(pkg).decode()+'\n```\n'
        self.assertEqual(pkg,extract(body))
    def test_invalid_issue(self):
        for body in ('','```json\n{}\n```','x'*60001):
            with self.assertRaises(ValueError):extract(body)
    def test_network_does_not_auto_enable(self):
        pkg=self.package();pkg['files']['manifest.json']['policy']['networkDefault']=True
        with self.assertRaises(ValueError):validate(pkg)
    def test_scenario_must_be_disabled(self):
        pkg=load((ROOT/'scenarios/qscenario.daily_opsec.json').read_bytes());pkg['scenario']['enabled']=True
        with self.assertRaises(ValueError):validate(pkg)

if __name__=='__main__':unittest.main()
