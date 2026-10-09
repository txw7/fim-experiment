"""Create a readable, provenance-linked normal form view from an offline S3 run.

This is a bounded projection, not a proof of semantic equivalence or native
admission. The expanded candidate remains the authoritative evidence record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re



def parse_sexpr(text):
    """Parse the small parenthesized source notation used by S3 topology."""
    tokens = [(m.group(), m.start(), m.end()) for m in re.finditer(r"[()]|[^\s()]+", text)]
    index = 0

    def one():
        nonlocal index
        token, start, end = tokens[index]
        index += 1
        if token != "(":
            if token == ")":
                raise ValueError("unexpected close parenthesis")
            return {"atom": token, "start": start, "end": end}
        children = []
        while index < len(tokens) and tokens[index][0] != ")":
            children.append(one())
        if index >= len(tokens):
            raise ValueError("unclosed parenthesis")
        close = tokens[index]
        index += 1
        if len(children) < 2 or "atom" not in children[0]:
            raise ValueError("operator expression requires operands")
        return {"head": children[0], "children": children[1:],
                "start": start, "end": close[2]}

    if not tokens:
        raise ValueError("empty expression")
    root = one()
    if index != len(tokens):
        raise ValueError("trailing expression data")
    return root


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree(node):
    if "atom" in node:
        return node["atom"]
    return (node["head"]["atom"], *(_tree(child) for child in node["children"]))


def _render_tree(node):
    if "atom" in node:
        return node["atom"]
    return "(" + " ".join([node["head"]["atom"], *(_render_tree(c) for c in node["children"])]) + ")"


def normalize(run_dir: Path, out_dir: Path) -> dict:
    run_dir, out_dir = Path(run_dir).resolve(), Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {out_dir}")
    graph = json.loads((run_dir / "expanded.json").read_text())
    coverage = json.loads((run_dir / "requirement-coverage.json").read_text())
    web = json.loads((run_dir / "semantic-web.json").read_text())
    qwen = json.loads((run_dir / "qwen-checks.json").read_text())[-1]
    qwen_request = json.loads((run_dir / "qwen/semantic-web/request.json").read_text())
    qwen_packet = json.loads(qwen_request["messages"][1]["content"])
    source = (run_dir / "raw.txt").read_bytes()
    source_hash = sha(source)
    if source_hash != graph["source_sha256"]:
        raise ValueError("source snapshot does not match candidate graph")

    clauses = {row["id"]: row for row in coverage["clauses"]}
    by_id = {row["id"]: row for row in graph["nodes"]}
    relations = {row["id"]: row for row in graph["relations"]}

    # Select the dependency closure of the higher-order web, plus the explicit
    # project-stage dependency. Keep the original source clauses addressable.
    selected_clause_ids = set()
    for domain in web["domains"].values():
        node = by_id[domain]
        for member in node["data"].get("members", []):
            match = re.fullmatch(r"req/(clause-\d+)", member)
            if match:
                selected_clause_ids.add(match.group(1))
    selected_clause_ids.add("clause-012")  # explicit S3 -> S2.5 stage dependency
    for row in web["obligations"]:
        selected_clause_ids.add(row["source_clause"])
        selected_clause_ids.update(slot["source_clause"] for slot in row["slots"])
    missing = selected_clause_ids - clauses.keys()
    if missing:
        raise ValueError(f"selected source clauses absent: {sorted(missing)}")
    selected_clause_ids = sorted(selected_clause_ids, key=lambda x: int(x.split("-")[1]))

    # Rebuild the nested topology from the graph's ordered child incidences.
    tree_root = web["topology_tree"]["root"]

    def graph_tree(identity):
        node = by_id[identity]
        if node["type"] == "Entity":
            return {"atom": node["data"]["label"]}
        child_rows = []
        for relation in graph["relations"]:
            if relation["law"] != "topology-child.v1":
                continue
            roles = {item["role"]: item["target"] for item in relation["incidences"]}
            if roles["parent"] == identity:
                child_rows.append((int(by_id[roles["position"]]["data"]["label"]), graph_tree(roles["child"])))
        child_rows.sort(key=lambda item: item[0])
        head_relation = next(r for r in graph["relations"] if r["law"] == "topology-head.v1" and
            {i["role"]: i["target"] for i in r["incidences"]}["expression"] == identity)
        head_id = next(i["target"] for i in head_relation["incidences"] if i["role"] == "head")
        return {"head": {"atom": by_id[head_id]["data"]["label"]},
                "children": [child for _, child in child_rows]}

    candidate_tree = graph_tree(tree_root)
    topology_clause = clauses["clause-007"]["source"]["text"]
    literal = re.search(r"\(SUPERVISE\b.*", topology_clause)
    if not literal:
        raise ValueError("source topology literal is missing")
    depth, end = 0, None
    for index, char in enumerate(literal.group()):
        if char == "(": depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    source_tree = parse_sexpr(literal.group()[:end])
    if _tree(source_tree) != _tree(candidate_tree):
        raise ValueError("reduced topology does not reconstruct candidate/source tree")
    rendered_tree = _render_tree(candidate_tree)

    # Model judgments remain diagnostic uncertainty, never normalized facts.
    observations = qwen.get("observation", {})
    expected_keys = {f"c{i}" for i in range(1, 6)}
    candidate_rows = {row["candidate_key"]: row for row in qwen_packet["cross_network_candidates"]}
    if set(observations) != expected_keys or set(candidate_rows) != expected_keys or \
            any(v.get("status") != "unresolved" for v in observations.values()):
        raise ValueError("expected five retained unresolved Qwen observations")
    law_labels = {
        "scope-constrains.v1": "scope-constrains execution",
        "guard-constrains.v1": "guard-constrains execution",
        "execution-evidence.v1": "execution-witnessed-by evidence",
        "gate-requires-evidence.v1": "gate-requires evidence",
        "gate-checks-execution.v1": "gate-checks execution",
    }
    cross_names = {}
    for key, candidate in candidate_rows.items():
        relation = relations.get(candidate["id"])
        if relation is None or relation["law"] != candidate["law"] or candidate["law"] not in law_labels:
            raise ValueError(f"Qwen candidate does not match graph relation: {key}")
        cross_names[key] = law_labels[candidate["law"]]

    alias_lines = []
    for row in web["topology_tree"].get("alias_correspondences", []):
        relation = relations.get(row["relation"])
        if relation is None:
            raise ValueError("alias correspondence relation is missing from graph")
        roles = {item["role"]: item["target"] for item in relation["incidences"]}
        alias = by_id[roles["source_node"]]["data"]["label"]
        original = by_id[roles["target"]]["data"]["source"]["text"]
        alias_lines.append(f"{alias}→{original}")
    if sorted(alias_lines) != ["B1→A", "C1→B"]:
        raise ValueError("candidate graph alias correspondences do not match source declaration")

    out_dir.mkdir(mode=0o700, parents=True)
    lines = [
        "S3_LIVE_AB — REDUCED SOURCE-GROUNDED VIEW",
        "status: candidate; provider execution NOT RUN; native admission NOT RUN",
        f"source: S3 raw-spec.txt sha256 {source_hash}",
        "",
        "S2.5 topology (nested form retained)",
        "  " + rendered_tree,
        "",
        "Identity and scope",
        "  B1 → original A; C1 → original B (source-declared alias mapping)",
        "  B2 and C2 are new agents; the two PAIR nodes remain distinct",
        "  S3 scope: original A→B provider handoff, within pair-1 B1→C1",
        "  S3 depends on S2.5 in stages.json",
        "",
        "Required handoff (requirement, not an observed execution)",
        "  " + clauses["clause-013"]["source"]["text"],
        "",
        "Explicit bounds and evidence",
        "  " + clauses["clause-020"]["source"]["text"],
        "  " + clauses["clause-022"]["source"]["text"],
        "  " + clauses["clause-023"]["source"]["text"],
        "  " + clauses["clause-026"]["source"]["text"],
        "",
        "Higher-order candidate links — Qwen marked each unresolved",
    ]
    lines.extend(f"  {key}: {name} — UNRESOLVED" for key, name in cross_names.items())
    lines += ["", "Feedback obligations"]
    for obligation in web["obligations"]:
        lines.append(f"  {obligation['id'].split('/')[-1]} — OPEN")
        for slot in obligation["slots"]:
            lines.append(f"    {slot['status']}: {slot['id'].split('/')[-1]} [{slot['source_clause']}]")
    lines += [
        "",
        "Interpretation boundary",
        "  The readable view is a projection of the retained candidate graph, not a proof that the",
        "  source clauses entail the five cross-links. Open obligations and the full evidence graph",
        "  remain addressable in expanded.json and semantic-web.json.",
        "",
        "Source clauses included in this view: " + ", ".join(selected_clause_ids),
    ]
    compact_lines = [
        "S3_LIVE_AB  [OPEN CANDIDATE]",
        f"  source sha256: {source_hash}",
        "  depends-on S2.5  [clause-012]",
        "  topology " + rendered_tree + "  [clause-007]",
        "  aliases " + ", ".join(alias_lines) + "  [clause-008]",
        "  fresh independent pair B2,C2  [clause-009]",
        "  live scope A→B within pair-1 B1→C1  [clause-010]",
        "",
        "  provider requirement (not observed execution)  [clause-013]",
    ]
    flow = clauses["clause-013"]["source"]["text"].split(" → ")
    compact_lines.extend("    " + ("→ " if i else "") + step for i, step in enumerate(flow))
    compact_lines += [
        "",
        "  bounds: one invocation; no uncertain retry; no duplicate send  [clause-020]",
        "  receipt: evidence/live_ab.json with provider turn, addresses, IDs, generation, transport, commit  [clause-022]",
        "  negative tests: stale, correlation mismatch, wrong target/type, private access, double commit, unavailable, uncertain retry, restart  [clause-023]",
        "  unavailable provider ⇒ remain OPEN; no fabricated success  [clause-026]",
        "  forbid flattening, pair-2-live claims, background runner, second dispatcher  [clause-011]",
        "  no mocks/replay, thread hijack, fabricated provider IDs/receipts  [clauses-015:017]",
        "  gates: check-s3; check-s3-live; package-s3; promote only on accepted evidence  [clause-021]",
        "  preserve prior tests/digests; no S4+  [clauses-024,027]",
        "",
        "  higher-order links (Qwen observations):",
    ]
    compact_lines.extend(f"    {key}: {name} — UNRESOLVED" for key, name in cross_names.items())
    compact_lines += ["", "  feedback obligations:"]
    for obligation in web["obligations"]:
        compact_lines.append(f"    {obligation['id'].split('/')[-1]} — OPEN")
        for slot in obligation["slots"]:
            compact_lines.append(f"      {slot['status']}: {slot['id'].split('/')[-1]} [{slot['source_clause']}]")
    compact_lines += [
        "",
        "  semantic equivalence to all of S3: NOT ESTABLISHED",
        "  provider execution: NOT RUN · native admission: NOT RUN",
        "  selected clause text and anchors: provenance.txt",
    ]
    lines = compact_lines
    normal_text = "\n".join(lines) + "\n"
    (out_dir / "normal-form.txt").write_text(normal_text)

    provenance = [
        "REDUCED VIEW PROVENANCE",
        f"input_run: {run_dir.name}",
        f"source_sha256: {source_hash}",
        "source clause references are exact; ranges use half-open UTF-8 byte offsets",
        "",
    ]
    for clause_id in selected_clause_ids:
        src = clauses[clause_id]["source"]
        actual = source[src["byte_start"]:src["byte_end"]].decode("utf-8")
        if actual != src["text"]:
            raise ValueError(f"source anchor mismatch: {clause_id}")
        provenance.append(f"{clause_id} bytes[{src['byte_start']}:{src['byte_end']}] chars[{src['char_start']}:{src['char_end']}]")
        provenance.append("  " + actual)
    provenance += ["", "Qwen request/response under the --run directory: qwen/semantic-web/request.json and response.json",
                   "Qwen output was observation-only; all five statuses are unresolved."]
    (out_dir / "provenance.txt").write_text("\n".join(provenance) + "\n")

    raw_size = len(source)
    output_size = len(normal_text.encode("utf-8"))
    exact_covered = sum(clauses[c]["source"]["byte_end"] - clauses[c]["source"]["byte_start"]
                        for c in selected_clause_ids)
    receipt = [
        "REDUCTION RECEIPT",
        "mode: readable candidate projection; semantic rewrite count: 0",
        f"input_graph_objects: {len(graph['nodes']) + len(graph['relations'])}",
        f"selected_source_clauses: {len(selected_clause_ids)} / {len(clauses)}",
        f"selected_source_bytes: {exact_covered} / {raw_size} (clause spans may be adjacent; no semantic coverage claim)",
        f"normal_form_bytes_utf8: {output_size}",
        f"raw_source_to_view_size_ratio: {raw_size / max(output_size, 1):.3f} (size only; not a semantic compression proof)",
        f"topology_reconstruction: PASS ({rendered_tree})",
        f"source_anchor_verification: PASS ({len(selected_clause_ids)} clauses)",
        f"open_feedback_slots_preserved: {sum(s['status'] == 'OPEN' for o in web['obligations'] for s in o['slots'])}",
        f"source_form_only_slots_preserved: {sum(s['status'] == 'PARSED_SOURCE_FORM' for o in web['obligations'] for s in o['slots'])}",
        "qwen_unresolved_relations_preserved: 5 / 5",
        "semantic_equivalence_to_entire_S3: NOT_ESTABLISHED",
        "native_admission: NOT_RUN",
        "selected source clause text and byte/character anchors remain in provenance.txt; input graph remains unchanged.",
    ]
    (out_dir / "reduction-receipt.txt").write_text("\n".join(receipt) + "\n")
    return {"normal_form": str(out_dir / "normal-form.txt"), "source_clauses": selected_clause_ids,
            "topology_roundtrip": True, "qwen_unresolved": len(expected_keys),
            "open_slots": sum(s["status"] == "OPEN" for o in web["obligations"] for s in o["slots"]),
            "native_admission": "NOT_RUN"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(normalize(args.run, args.out), indent=2))
