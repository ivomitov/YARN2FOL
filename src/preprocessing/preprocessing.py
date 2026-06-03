from grewpy import Graph, GRS

def reify_he(yarn_grew, grs_path):
    grs = GRS(grs_path)
    yarn_grew = grs.apply(Graph(yarn_grew), strat='main').json_data()

    return yarn_grew

def get_S_descendants(yarn_grew):
    nodes = yarn_grew["nodes"]
    edges = yarn_grew["edges"]

    adj = {}
    for e in edges:
        adj.setdefault(e["src"], []).append(e["tar"])

    result = {}

    for node_id, node_data in nodes.items():
        if node_data.get("type") != "S":
            continue

        visited = set()
        stack = [node_id]
        reachable = []

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            current_type = nodes[current].get("type")

            if current_type in ["L", "H", "V"]:
                reachable.append(current)

            if current_type in ["C", "D"]:
                continue

            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        result[node_id] = list(reachable)

    return result

def propagate_s_node_information(yarn_grew, s_descendants):

    for s_node, descendants in s_descendants.items():
        for descendant in descendants:
            for node, feats in yarn_grew['nodes'].items():
                if node == descendant:
                    feats['event'] = s_node
    
    return yarn_grew