# pdb-drain-witness

Explain a captured Kubernetes Ready-pod disruption wave and budget blockers.

**Alpha, offline diagnostic.** Built for an SRE preparing a maintenance wave from saved kubectl API output.
Original implementation with AI assistance; no competitor code or prose copied.
No production impact, adoption or performance advantage is claimed.

## Install and get a useful result

Python 3.10+. Clone this repository, then:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
pdb-drain-witness example.json
```

The bundled fixture is synthetic. `example.py` only creates its own temporary
fixture when present. Exit 0 means a report was produced with no CLI-level failure;
exit 2 reports invalid or unsupported input.
A zero exit is not an eviction or scheduler safety guarantee.

## Input

`pdb-drain-witness snapshot.json` accepts one JSON object with `node`, `pods`
(a `v1 PodList` or `List`), and `budgets` (a `policy/v1 PodDisruptionBudgetList`
or `List`). The bundled [snapshot](example.json) uses native Kubernetes objects.
Use captured `kubectl get pods -A -o json` and `kubectl get pdb -A -o json`
outputs for the two lists; record your capture time and inspect freshness. Separate
API reads are not an atomic cluster snapshot. Namespace/name identities must be
unique. Every PDB requires metadata.generation; missing/stale observedGeneration
holds its matching pods. Invalid/unsupported selector operators are errors.

## Capability and limits

Ready pods with zero or one matching policy/v1 PDB only. Reads disruptionsAllowed and observedGeneration from a captured snapshot. Empty policy/v1 selector selects all; null selects none. Not-ready pods and overlapping PDBs are held with reasons. DaemonSet, mirror, terminal and terminating pods are excluded. This is the maximum cardinality single wave under these captured independent capacities; lexicographic pod identity breaks ties. It does not predict replacement readiness or guarantee an eviction: live admission, RBAC, local storage, safe-to-evict annotations, concurrent actors and API changes are not modeled. No cluster connection or eviction occurs.

## Acceptance criteria

Two Ready pods and capacity one include only the lexicographically first pod, with an exhausted-budget reason for the other; stale generation and overlapping selectors hold pods; invalid selector operators fail; namespaces and input immutability are tested.

## Checks and evidence

```bash
python -m unittest -v
python -m compileall -q .
```

[Validation](VALIDATION.md) documents the prepared checks and failure cases.
[Research and alternatives](RESEARCH.md) records dated observations, competing
workflows and a bounded inferred need. The [CI workflow](.github/workflows/test.yml)
builds wheels and tests installed commands outside the checkout on Linux Python
3.10/3.12/3.14. Check the actual current Actions result before relying on it.

[Contributing](CONTRIBUTING.md) · [Support](SUPPORT.md) ·
[Security](SECURITY.md) · [MIT license](LICENSE)
