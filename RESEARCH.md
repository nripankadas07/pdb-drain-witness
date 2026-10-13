# Research — pdb-drain-witness

Observed 13 October 2026 on live GitHub. Demand is inferred from documented workflows and public issues, not a verified request for this product. Only the first page of each star-sorted problem search was reviewed; this is not an exhaustive global ranking. Broad unrelated results were excluded. Stars are discovery signals, not technical performance evidence.

## User and acceptance

An SRE preparing a maintenance wave from saved kubectl API output.

Pain: Explain a captured Kubernetes Ready-pod disruption wave and budget blockers.

Smallest useful capability and acceptance: Two Ready pods and capacity one include only the lexicographically first pod, with an exhausted-budget reason for the other; stale generation and overlapping selectors hold pods; invalid selector operators fail; namespaces and input immutability are tested.

## Observed alternatives

| Repository | Stars | Last push (UTC) | Status / detected license |
| --- | ---: | --- | --- |
| [planetlabs/draino](https://github.com/planetlabs/draino) | 689 | 2024-03-26T15:33:02Z | active repository / Apache-2.0 |
| [atlassian/escalator](https://github.com/atlassian/escalator) | 688 | 2026-09-11T07:08:02Z | active repository / Apache-2.0 |
| [strimzi/drain-cleaner](https://github.com/strimzi/drain-cleaner) | 66 | 2026-10-10T23:14:31Z | active repository / Apache-2.0 |

Query: `kubernetes drain`; [GitHub search, Most stars](https://github.com/search?q=kubernetes%20drain&type=repositories&s=stars&o=desc). Exact observed queries, stars and push dates are recorded above. Highest-star relevant result on that page: planetlabs/draino. Other established workflow alternatives were reviewed even if they were not on that first page.

Draino performs live cordon/drain and retries eviction API failures; its README explicitly describes restrictive PDB drain failures. Escalator is a live autoscaler. Strimzi Drain Cleaner delegates Kafka rolling restarts to its operator. Those tools require cluster deployment or access; this tool instead explains captured Ready-pod capacity and holds unsupported cases. It is not a live admission simulator or replacement for them.

## Differentiation and discovery

No existing owned repository models captured PDB selectors/capacity. Distinct from simulation and systemd-order tools. Discover through Kubernetes/SRE maintenance examples and reproducible budget fixtures.

## Fair comparison boundary

Docs, relevant source and accessible issue collections were inspected. No comparator was installed or timed on equivalent workloads; therefore no install-speed, reliability or performance superiority is claimed. A passing example proves our documented behavior only. No external code was reused; comparator licenses above are API-detected labels, not a legal determination. Support and licensing follow each upstream repository; this alpha offers MIT source and best-effort issue support.
