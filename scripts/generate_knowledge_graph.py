#!/usr/bin/env python3
"""
Neo4j Knowledge Graph Snapshot Generator
Generates JSON snapshot of Neo4j graph for visualization
Run daily via cron to show Soo Edu's growing second brain
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import requests

# Neo4j proxy configuration
NEO4J_PROXY_URL = "http://127.0.0.1:3939/query"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "data"

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
    
    # Query for nodes
    nodes_query = """
    // Get all nodes: Students, Curriculum, Interests, Levels
    MATCH (n)
    WHERE n:Student OR n:Curriculum OR n:Interest OR n:Level
    RETURN 
        id(n) as id,
        labels(n) as labels,
        properties(n) as properties
    LIMIT 200
    """
    
    # Query for relationships
    relationships_query = """
    // Get all relationships
    MATCH (a)-[r]->(b)
    WHERE (a:Student OR a:Curriculum OR a:Interest OR a:Level)
      AND (b:Student OR b:Curriculum OR b:Interest OR b:Level)
    RETURN 
        id(a) as from,
        id(b) as to,
        type(r) as type,
        properties(r) as properties
    LIMIT 300
    """
    
    print("📊 Querying Neo4j for graph data...")
    
    nodes_data = query_neo4j(nodes_query)
    relationships_data = query_neo4j(relationships_query)
    
    print(f"  ✅ Nodes: {len(nodes_data)}")
    print(f"  ✅ Relationships: {len(relationships_data)}")
    
    # Transform to vis.js format
    nodes = []
    for node in nodes_data:
        node_id = node.get("id")
        labels = node.get("labels", [])
        props = node.get("properties", {})
        
        # Determine node type and styling
        label_type = labels[0] if labels else "Unknown"
        
        # Color coding by type
        color_map = {
            "Student": "#4CAF50",      # Green
            "Curriculum": "#2196F3",   # Blue
            "Interest": "#FF9800",     # Orange
            "Level": "#9C27B0"         # Purple
        }
        
        # Icon/shape by type
        shape_map = {
            "Student": "dot",
            "Curriculum": "box",
            "Interest": "diamond",
            "Level": "star"
        }
        
        # Label text
        label_text = props.get("name") or props.get("title") or f"{label_type} {node_id}"
        
        nodes.append({
            "id": node_id,
            "label": label_text,
            "title": f"{label_type}: {label_text}",  # Tooltip
            "group": label_type,
            "color": color_map.get(label_type, "#757575"),
            "shape": shape_map.get(label_type, "dot"),
            "size": 20 if label_type == "Student" else 15,
            "properties": props
        })
    
    edges = []
    for rel in relationships_data:
        rel_type = rel.get("type", "CONNECTED")
        props = rel.get("properties", {})
        
        edges.append({
            "from": rel.get("from"),
            "to": rel.get("to"),
            "label": rel_type,
            "title": rel_type,  # Tooltip
            "arrows": "to",
            "properties": props
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "description": "Soo Edu Knowledge Graph - Student Learning Network"
        }
    }

def save_snapshot(graph_data: dict):
    """Save graph snapshot to JSON file"""
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save as latest.json (always current)
    latest_file = OUTPUT_DIR / "knowledge-graph-latest.json"
    
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
    
    return latest_file

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
    
    # Check Neo4j proxy availability
    try:
        response = requests.get("http://127.0.0.1:3939/health", timeout=2)
        if not response.ok:
            print("❌ Neo4j proxy is not healthy")
            print("   Start proxy: python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to Neo4j proxy: {e}")
        print("   Start proxy: python3 /Users/tjaypark/sooedubot_workspace/scripts/neo4j_read_proxy.py")
        return 1
    
    # Generate snapshot
    graph_data = get_graph_snapshot()
    
    if not graph_data["nodes"]:
        print("⚠️  No nodes found in Neo4j. Graph might be empty.")
        return 1
    
    # Save snapshot
    output_file = save_snapshot(graph_data)
    
    print()
    print("=" * 60)
    print(f"✅ Knowledge graph snapshot generated!")
    print(f"   Nodes: {graph_data['metadata']['node_count']}")
    print(f"   Edges: {graph_data['metadata']['edge_count']}")
    print(f"   File: {output_file}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
