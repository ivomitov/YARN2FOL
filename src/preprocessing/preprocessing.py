import re
from grewpy import Graph, GRS

def reify_he(yarn_grew, grs_path):
    grs = GRS(grs_path)
    yarn_grew = grs.apply(Graph(yarn_grew), strat='main').json_data()

    return yarn_grew

def get_S_descendants(yarn_grew):
    nodes = yarn_grew["nodes"]
    edges = yarn_grew["edges"]

    adj = {}
    radj = {}
    for e in edges:
        adj.setdefault(e["src"], []).append(e["tar"])
        radj.setdefault(e["tar"], []).append(e["src"])

    LISTED_TYPES = {"L", "H", "V", "E", "F"}

    def s_sort_key(s_id):
        m = re.search(r'\d+', s_id)
        return (int(m.group()) if m else float('inf'), s_id)

    s_ids = sorted(
        (n for n, d in nodes.items() if d.get("type") == "S"),
        key=s_sort_key
    )

    # --- Phase 1: forward-only reachability, establishes true ownership ---
    forward_reachable = {}
    for s_id in s_ids:
        visited = set()
        stack = [s_id]
        reach = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            t = nodes[current].get("type")
            if t in LISTED_TYPES:
                reach.add(current)
            if t in ("C", "D"):
                continue
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        forward_reachable[s_id] = reach

    owner = {}
    for s_id in s_ids:  # earliest S processed first -> wins ties
        for n in forward_reachable[s_id]:
            owner.setdefault(n, s_id)

    # --- Phase 2: full forward+reverse traversal, gated by ownership ---
    result = {}
    for s_id in s_ids:
        visited = set()
        stack = [s_id]
        reachable = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            t = nodes[current].get("type")

            if t in LISTED_TYPES and owner.get(current, s_id) == s_id:
                reachable.append(current)

            if t in ("C", "D"):
                continue

            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)

            for neighbor in radj.get(current, []):
                if (
                    neighbor not in visited
                    and nodes[neighbor].get("type") in ("V", "E")
                    and owner.get(neighbor, s_id) == s_id
                ):
                    stack.append(neighbor)

        result[s_id] = reachable

    return result

def propagate_s_node_information(yarn_grew, s_descendants):

    for s_node, descendants in s_descendants.items():
        for descendant in descendants:
            for node, feats in yarn_grew['nodes'].items():
                if node == descendant:
                    feats['event'] = s_node
    
    return yarn_grew
