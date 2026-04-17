#!/usr/bin/env python3
"""
Neo4j Knowledge Graph Snapshot Generator
Generates JSON snapshot of Neo4j graph for visualization
Run daily via cron to show Soo Edu's growing second brain
"""

import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import requests

# Neo4j proxy configuration
NEO4J_PROXY_URL = "http://127.0.0.1:3939/query"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "data"


def normalize_graph_data(graph_data: dict) -> dict:
    """Return a semantic snapshot for stable equality checks."""
    normalized = deepcopy(graph_data)
    normalized.setdefault("metadata", {}).pop("generated_at", None)
    normalized["nodes"] = sorted(normalized.get("nodes", []), key=lambda n: n.get("id", 0))
    normalized["edges"] = sorted(
        normalized.get("edges", []),
        key=lambda e: (e.get("from"), e.get("to"), e.get("title", ""))
    )
    return normalized


def load_existing_graph(path: Path):
    """Load an existing graph snapshot if present."""
    if not path.exists():
        return None

    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            print(f"Warning: corrupted snapshot at {path}, will regenerate", file=sys.stderr)
            return None

def query_neo4j(query: str, params: dict = None):
    """Query Neo4j through the read-only proxy"""
    try:
        response = requests.post(
            NEO4J_PROXY_URL,
            json={
                "query": query,
                "params": params or {},
                "max_records": 500
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            return data.get("records", [])
        else:
            print(f"❌ Neo4j query failed: {response.status_code}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"❌ Error querying Neo4j: {e}", file=sys.stderr)
        return []

def get_graph_snapshot():
    """Get complete graph snapshot from Neo4j"""
    
    # Query for nodes - Students active in last 30 days
    nodes_query = """
    // Get students who had lessons in the last 30 days
    // Date is stored as string, so calculate 30 days ago
    WITH date() - duration({days: 30}) as cutoffDate
    MATCH (s:Student)-[:HAS_LESSON]->(lesson:Lesson)
    WHERE lesson.date >= toString(cutoffDate)
    WITH DISTINCT s
    ORDER BY id(s)
    LIMIT 80

    // Get their connected nodes
    MATCH (s)-[r]-(connected)
    WHERE connected:Word OR connected:Book OR connected:Interest OR connected:Level
    WITH s, collect(DISTINCT connected) as related
    UNWIND [s] + related as nodes
    WITH DISTINCT nodes
    RETURN
        id(nodes) as id,
        labels(nodes) as labels,
        properties(nodes) as properties
    ORDER BY id(nodes)
    """

    # Query for relationships - only for active students
    relationships_query = """
    // Get students who had lessons in the last 30 days
    WITH date() - duration({days: 30}) as cutoffDate
    MATCH (s:Student)-[:HAS_LESSON]->(lesson:Lesson)
    WHERE lesson.date >= toString(cutoffDate)
    WITH DISTINCT s
    ORDER BY id(s)
    LIMIT 80

    // Get their relationships with learning materials
    MATCH (s)-[r]-(other)
    WHERE other:Word OR other:Book OR other:Interest OR other:Level
    RETURN DISTINCT
        id(s) as from,
        id(other) as to,
        type(r) as type,
        properties(r) as properties
    ORDER BY id(s), id(other), type(r)
    LIMIT 500
    """
    
    print("📊 Querying Neo4j for graph data...")
    
    nodes_data = query_neo4j(nodes_query)
    relationships_data = query_neo4j(relationships_query)
    
    print(f"  ✅ Nodes: {len(nodes_data)}")
    print(f"  ✅ Relationships: {len(relationships_data)}")
    
    # Transform to vis.js format
    color_map = {
        "Student": "#4CAF50",      # Green
        "Word": "#9C27B0",         # Purple
        "Book": "#F44336",         # Red
        "Interest": "#FF9800",     # Orange
        "Level": "#2196F3"         # Blue
    }

    shape_map = {
        "Student": "dot",
        "Word": "diamond",
        "Book": "star",
        "Interest": "box",
        "Level": "triangle"
    }

    # Build stable student_id → counter mapping sorted by node id
    # nodes_data is already ORDER BY id(nodes) from the query, but sort
    # defensively here to guarantee stable numbering regardless of proxy order.
    student_nodes_sorted = sorted(
        [n for n in nodes_data if "Student" in n.get("labels", [])],
        key=lambda n: n.get("id", 0)
    )
    student_id_to_number = {
        n.get("id"): idx + 1
        for idx, n in enumerate(student_nodes_sorted)
    }

    nodes = []

    for node in nodes_data:
        node_id = node.get("id")
        labels = node.get("labels", [])
        props = node.get("properties", {})

        label_type = labels[0] if labels else "Unknown"

        # Anonymize student names
        if label_type == "Student":
            student_number = student_id_to_number.get(node_id, 0)
            label_text = f"Student {student_number}"
            # Remove sensitive properties
            props = {"student_number": student_number}
        elif label_type == "Word":
            label_text = props.get("name", "Word")
        elif label_type == "Book":
            book_name = props.get("name", "Book")
            label_text = book_name[:25] + "..." if len(book_name) > 25 else book_name
        elif label_type == "Interest":
            label_text = props.get("name", "Interest")
        elif label_type == "Level":
            label_text = props.get("name", "Level")
        else:
            label_text = props.get("name") or props.get("title") or f"{label_type} {node_id}"

        nodes.append({
            "id": node_id,
            "label": label_text,
            "title": f"{label_type}: {label_text}",  # Tooltip
            "group": label_type,
            "color": color_map.get(label_type, "#757575"),
            "shape": shape_map.get(label_type, "dot"),
            "size": 20 if label_type == "Student" else 12,
            "properties": props
        })

    # Sort final lists by id for stable JSON output
    nodes.sort(key=lambda n: n["id"])
    
    edges = []
    for rel in relationships_data:
        rel_type = rel.get("type", "CONNECTED")
        props = rel.get("properties", {})

        # Friendly relationship labels
        label_map = {
            "LEARNED_WORD": "단어",
            "USED_BOOK": "교재",
            "INTERESTED_IN": "관심",
            "AT_LEVEL": "레벨",
            "HAS_INTEREST": "관심",
            "HAS_LEVEL": "레벨"
        }

        edges.append({
            "from": rel.get("from"),
            "to": rel.get("to"),
            "label": label_map.get(rel_type, ""),
            "title": rel_type,  # Tooltip
            "arrows": "to",
            "properties": props
        })

    # Sort edges for stable JSON output
    edges.sort(key=lambda e: (e["from"], e["to"], e["title"]))
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "description": "Soo Edu Knowledge Graph - Student Learning Network (익명화됨)"
        }
    }

def save_snapshot(graph_data: dict):
    """Save graph snapshot to JSON file"""
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save as latest.json (always current)
    latest_file = OUTPUT_DIR / "knowledge-graph-latest.json"
    existing_latest = load_existing_graph(latest_file)
    if existing_latest and normalize_graph_data(existing_latest) == normalize_graph_data(graph_data):
        print("ℹ️  No semantic graph changes detected. Existing snapshot kept.")
        return latest_file, False
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved: {latest_file}")
    
    # Also save dated snapshot for history
    date_str = datetime.now().strftime("%Y-%m-%d")
    dated_file = OUTPUT_DIR / f"knowledge-graph-{date_str}.json"
    
    with open(dated_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved: {dated_file}")
    
    # Clean up old snapshots (keep last 7 days)
    cleanup_old_snapshots()
    
    return latest_file, True

def cleanup_old_snapshots():
    """Remove snapshots older than 7 days"""
    import time
    
    current_time = time.time()
    max_age = 7 * 24 * 60 * 60  # 7 days in seconds
    
    for file in OUTPUT_DIR.glob("knowledge-graph-*.json"):
        if file.name == "knowledge-graph-latest.json":
            continue
        
        file_age = current_time - file.stat().st_mtime
        if file_age > max_age:
            file.unlink()
            print(f"🗑️  Cleaned up old snapshot: {file.name}")

def main():
    """Main execution"""
    print("=" * 60)
    print("Soo Edu Knowledge Graph Snapshot Generator")
    print("=" * 60)
    print()
    
    # Check Neo4j proxy availability (retry once on timeout)
    import time as _time
    _health_ok = False
    for _attempt in range(2):
        try:
            response = requests.get("http://127.0.0.1:3939/health", timeout=5)
            if response.ok:
                _health_ok = True
                break
            print(f"❌ Neo4j proxy is not healthy (attempt {_attempt+1})")
        except Exception as e:
            print(f"❌ Cannot connect to Neo4j proxy (attempt {_attempt+1}): {e}")
            if _attempt == 0:
                _time.sleep(3)
    if not _health_ok:
        print("   Start proxy: python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py")
        return 1
    
    # Generate snapshot
    graph_data = get_graph_snapshot()
    
    if not graph_data["nodes"]:
        print("⚠️  No nodes found in Neo4j. Graph might be empty.")
        return 1
    
    # Save snapshot
    output_file, did_write = save_snapshot(graph_data)

    print()
    print("=" * 60)
    print(f"✅ Knowledge graph snapshot generated!")
    print(f"   Nodes: {graph_data['metadata']['node_count']}")
    print(f"   Edges: {graph_data['metadata']['edge_count']}")
    print(f"   File: {output_file}")
    print(f"   Snapshot updated: {'yes' if did_write else 'no'}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
