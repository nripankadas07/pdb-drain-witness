import copy
import unittest
from pdb_drain_witness import analyze, selected


def pod(name, labels=None, node='n', namespace='default'):
    return {'apiVersion':'v1','kind':'Pod','metadata':{'name':name,'namespace':namespace,'labels':labels or {'app':'web'}},'spec':{'nodeName':node},'status':{'phase':'Running','conditions':[{'type':'Ready','status':'True'}]}}


def budget(name='b', cap=1, namespace='default'):
    return {'apiVersion':'policy/v1','kind':'PodDisruptionBudget','metadata':{'name':name,'namespace':namespace,'generation':2},'spec':{'selector':{'matchLabels':{'app':'web'}}},'status':{'observedGeneration':2,'disruptionsAllowed':cap}}


def snapshot(pods=None, budgets=None):
    return {'node':'n','pods':{'kind':'PodList','items':pods if pods is not None else [pod('b'),pod('a')]},'budgets':{'kind':'PodDisruptionBudgetList','items':budgets if budgets is not None else [budget()]}}


class Tests(unittest.TestCase):
    def test_capacity_consumption_and_deterministic_wave(self):
        r=analyze(snapshot());self.assertEqual(r['wave'],['default/a']);self.assertEqual(r['pods'][1]['reason'],'stale-or-exhausted-budget')
    def test_zero_capacity(self):
        self.assertEqual(analyze(snapshot(budgets=[budget(cap=0)]))['wave'],[])
    def test_no_budget_and_other_node(self):
        self.assertEqual(analyze(snapshot([pod('a'),pod('away',node='other')],[]))['wave'],['default/a'])
    def test_namespace_scope(self):
        self.assertEqual(analyze(snapshot([pod('x',namespace='other')],[budget(cap=0)]))['wave'],['other/x'])
    def test_stale_generation_conservative_hold(self):
        b=budget(cap=8);b['status']['observedGeneration']=1;self.assertEqual(analyze(snapshot(budgets=[b]))['wave'],[])
    def test_overlap_not_a_multi_budget_approximation(self):
        r=analyze(snapshot(budgets=[budget(),budget('second')]));self.assertTrue(all(p['reason']=='overlapping-budgets-unsupported' for p in r['pods']))
    def test_unhealthy_daemonset_terminal_and_mirror(self):
        ps=[pod(str(i)) for i in range(4)];ps[0]['status']['conditions']=[];ps[1]['metadata']['ownerReferences']=[{'kind':'DaemonSet'}];ps[2]['status']['phase']='Succeeded';ps[3]['metadata']['annotations']={'kubernetes.io/config.mirror':'x'}
        self.assertEqual([p['reason'] for p in analyze(snapshot(ps,[]))['pods']],['not-ready-unsupported','daemonset-pod','terminal-pod','mirror-pod'])
    def test_policy_v1_empty_vs_null_selector(self):
        self.assertTrue(selected({},{}));self.assertFalse(selected(None,{}))
    def test_expression_operators_and_missing_label(self):
        for op,vals,expected in [('In',['a'],False),('NotIn',['a'],True),('Exists',[],False),('DoesNotExist',[],True)]:
            self.assertEqual(selected({'matchExpressions':[{'key':'x','operator':op,'values':vals}]},{}),expected)
    def test_invalid_selector_and_boolean_capacity(self):
        with self.assertRaises(ValueError):selected({'matchExpressions':[{'key':'x','operator':'Gt','values':['2']}]},{})
        with self.assertRaises(ValueError):analyze(snapshot(budgets=[budget(cap=True)]))
    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):analyze(snapshot([pod('a'),pod('a')]))
    def test_input_not_mutated_and_digest_changes(self):
        s=snapshot();saved=copy.deepcopy(s);one=analyze(s);self.assertEqual(s,saved);s['node']='other';self.assertNotEqual(one['snapshot_sha256'],analyze(s)['snapshot_sha256'])


if __name__=='__main__':unittest.main()
