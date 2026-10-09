#!/usr/bin/env python3
"""Verify pinned source grounding and scope-candidate graph endpoints."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "S25": "475626d949cf9fac967ccd5b879f150cf520ca1ad0c74fbd0324028e2577c140",
    "S3": "c1c5c9ed7b35fa7da68c94b737517cc27b0202606094cb5d2b129e7c18711fe3",
}
SCOPE = "S3 exercises only original A→B real provider handoff within pair-1 B1→C1 boundary"


def verify():
    graph = json.loads((ROOT / "lowered.json").read_text())
    receipt = json.loads((ROOT / "symbolic-scope-check.json").read_text())
    snapshot = json.loads((ROOT / "graph-snapshot.json").read_text())
    anchor_artifact = json.loads((ROOT / "source-anchors.json").read_text())
    for doc, expected in PINS.items():
        assert graph["source_pins"][doc]["sha256"] == expected
        assert anchor_artifact["source_pins"][doc]["sha256"] == expected

    nodes = {node["id"]: node for node in graph["nodes"]}
    assert len(nodes) == len(graph["nodes"]), "duplicate node ID"
    anchors = {}
    anchor_count = 0
    for node in graph["nodes"]:
        p = node.get("payload", {})
        if p.get("sort") != "SourceAnchor":
            continue
        anchor_count += 1
        doc = p["document"]
        assert p["source_sha256"] == PINS[doc]
        assert p["char_end"] - p["char_start"] == len(p["text"])
        assert p["byte_end"] - p["byte_start"] == len(p["text"].encode("utf-8"))
        anchors[p["text"]] = node["id"]
    retained = anchor_artifact["anchors"]
    assert len(retained) == anchor_count
    retained_by_id = {a["id"]: a for a in retained}
    assert set(retained_by_id) == {n["payload"]["id"] for n in graph["nodes"] if n.get("payload", {}).get("sort") == "SourceAnchor"}
    assert SCOPE in anchors, "exact S3 scope anchor missing"

    relations = {row["semantic_id"]: row for row in graph["hyperrelations"]}
    expected = {
        "candidate-placement-s3-within-pair1": "network:PAIR1",
        "candidate-placement-s3-within-pair2": "network:PAIR2",
    }
    by_label = {row["label"]: row["id"] for row in graph["nodes"]}
    flow_id = by_label["import:S3:flow-82af4083b1"]
    anchor_id = anchors[SCOPE]
    assert "network:PAIR1" in by_label and "network:PAIR2" in by_label
    for relation_name, pair_label in expected.items():
        rel = relations[relation_name]
        roles = {part["role"]: part["target"] for part in rel["participants"]}
        assert roles["parent_region"] == by_label[pair_label]
        assert roles["operand_network"] == flow_id
        assert roles["source_anchor"] == anchor_id
        assert roles["candidate"] in nodes

    # Every projected relation target must resolve to a projected object or relation.
    ids = set(nodes) | {row["id"] for row in graph["hyperrelations"]}
    for rel in graph["hyperrelations"]:
        for part in rel["participants"]:
            assert part["target"] in ids, (rel["semantic_id"], part["target"])

    # Confirm the archived check does not upgrade missing native registration.
    law = receipt["checks"]["registered_law"]
    assert law == {"constitution": "CandidateScopePlacement", "registered": False,
                   "result": "UNREGISTERED"}
    assert receipt["result"] == "SOURCE_AND_GRAPH_CHECKS_PASS_SCOPE_LAW_UNREGISTERED"

    stored_ids = {obj["id"] for obj in snapshot["objects"]}
    assert set(nodes) <= stored_ids
    assert all(row["id"] in stored_ids for row in graph["hyperrelations"])
    return {"result": receipt["result"], "anchors_checked": anchor_count,
            "scope_candidates_checked": len(expected), "projected_nodes": len(nodes),
            "projected_relations": len(graph["hyperrelations"]),
            "native_admission": graph["native_admission"]}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
