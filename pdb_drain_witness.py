"""Read-only witnesses for a Ready-pod disruption wave from captured API JSON."""
import argparse
import hashlib
import json
import sys


def integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name + ' must be a nonnegative integer')
    return value


def selected(selector, labels):
    if selector is None:
        return False
    if not isinstance(selector, dict) or not isinstance(labels, dict):
        raise ValueError('selector and labels must be objects')
    if set(selector) - {'matchLabels', 'matchExpressions'}:
        raise ValueError('unsupported selector keys')
    pairs = selector.get('matchLabels', {})
    if not isinstance(pairs, dict) or any(not isinstance(v, str) for v in pairs.values()):
        raise ValueError('matchLabels must map keys to strings')
    answer = all(labels.get(k) == v for k, v in pairs.items())
    expressions = selector.get('matchExpressions', [])
    if not isinstance(expressions, list):
        raise ValueError('matchExpressions must be an array')
    for expr in expressions:
        if not isinstance(expr, dict) or set(expr) - {'key', 'operator', 'values'}:
            raise ValueError('invalid selector expression')
        key, op, vals = expr.get('key'), expr.get('operator'), expr.get('values', [])
        if not isinstance(key, str) or not key or not isinstance(vals, list) or any(not isinstance(v, str) for v in vals):
            raise ValueError('invalid selector expression fields')
        if op in ('In', 'NotIn') and not vals:
            raise ValueError('In/NotIn requires values')
        if op in ('Exists', 'DoesNotExist') and vals:
            raise ValueError('Exists/DoesNotExist forbids values')
        if op == 'In':
            match = key in labels and labels[key] in vals
        elif op == 'NotIn':
            match = key not in labels or labels[key] not in vals
        elif op == 'Exists':
            match = key in labels
        elif op == 'DoesNotExist':
            match = key not in labels
        else:
            raise ValueError('unsupported selector operator')
        answer = answer and match
    return answer


def items(value, kind):
    if not isinstance(value, dict) or value.get('kind') not in ('List', kind + 'List') or not isinstance(value.get('items'), list):
        raise ValueError('expected Kubernetes ' + kind + 'List')
    if len(value['items']) > 10000:
        raise ValueError('snapshot exceeds 10000 objects')
    return value['items']


def identity(obj):
    meta = obj.get('metadata', {})
    if not isinstance(meta, dict) or not isinstance(meta.get('name'), str) or not meta['name']:
        raise ValueError('object requires metadata.name')
    ns = meta.get('namespace', 'default')
    if not isinstance(ns, str) or not ns:
        raise ValueError('invalid namespace')
    return ns + '/' + meta['name']


def analyze(snapshot):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get('node'), str) or not snapshot['node']:
        raise ValueError('node must be a nonempty string')
    pods = items(snapshot.get('pods'), 'Pod')
    budgets = items(snapshot.get('budgets'), 'PodDisruptionBudget')
    seen = set()
    caps, budget_rows = {}, []
    for b in budgets:
        if not isinstance(b, dict) or b.get('apiVersion') != 'policy/v1' or b.get('kind') != 'PodDisruptionBudget':
            raise ValueError('only policy/v1 PodDisruptionBudget is supported')
        ident = identity(b)
        if ident in seen:
            raise ValueError('duplicate budget identity')
        seen.add(ident)
        spec, status = b.get('spec', {}), b.get('status', {})
        selected(spec.get('selector'), {})
        generation = integer(b['metadata'].get('generation'), 'generation')
        observed = status.get('observedGeneration')
        stale = observed != generation or type(observed) is not int
        allowed = integer(status.get('disruptionsAllowed', 0), 'disruptionsAllowed')
        caps[ident] = 0 if stale else allowed
        budget_rows.append({'budget': ident, 'captured_capacity': allowed, 'usable_capacity': caps[ident], 'stale': stale})
    rows, wave = [], []
    seen = set()
    for p in sorted(pods, key=identity):
        if not isinstance(p, dict) or p.get('kind') != 'Pod' or p.get('apiVersion') != 'v1':
            raise ValueError('only v1 Pod is supported')
        ident = identity(p)
        if ident in seen:
            raise ValueError('duplicate pod identity')
        seen.add(ident)
        if p.get('spec', {}).get('nodeName') != snapshot['node']:
            continue
        meta, status = p['metadata'], p.get('status', {})
        reason = None
        if meta.get('deletionTimestamp'):
            reason = 'already-terminating'
        elif status.get('phase') in ('Succeeded', 'Failed'):
            reason = 'terminal-pod'
        elif 'kubernetes.io/config.mirror' in meta.get('annotations', {}):
            reason = 'mirror-pod'
        elif any(o.get('kind') == 'DaemonSet' for o in meta.get('ownerReferences', [])):
            reason = 'daemonset-pod'
        elif not any(c.get('type') == 'Ready' and c.get('status') == 'True' for c in status.get('conditions', [])):
            reason = 'not-ready-unsupported'
        matching = [identity(b) for b in budgets if identity(b).split('/')[0] == ident.split('/')[0] and selected(b.get('spec', {}).get('selector'), meta.get('labels', {}))]
        if reason is None and len(matching) > 1:
            reason = 'overlapping-budgets-unsupported'
        if reason is None and matching and caps[matching[0]] == 0:
            reason = 'stale-or-exhausted-budget'
        if reason is None:
            wave.append(ident)
            if matching:
                caps[matching[0]] -= 1
        rows.append({'pod': ident, 'budgets': matching, 'decision': 'include' if reason is None else 'hold', 'reason': reason or ('captured-budget-allows' if matching else 'no-matching-budget')})
    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema': 'pdb-drain-witness/v1', 'snapshot_sha256': digest, 'node': snapshot['node'], 'wave': wave, 'pods': rows, 'budgets': budget_rows,
            'limits': 'Ready pods only; captured single wave, no replacement readiness, live admission, RBAC, local-storage or safe-to-evict guarantees; no eviction performed.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot')
    args = parser.parse_args()
    try:
        with open(args.snapshot, encoding='utf-8') as f:
            result = analyze(json.load(f))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
        print('error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
