import itertools
import networkx as nx

def get_prufer_sequences(n):
    nodes = list(range(n))
    for seq in itertools.product(nodes, repeat=n-2):
        yield nx.from_prufer_sequence(seq)

def get_all_possible_trees(forest): # no need for 'rooted'

    nodes = list(forest['nodes'].keys())
    n_nodes = len(nodes)

    all_possible_tree_edges = []

    for tree in get_prufer_sequences(n_nodes):

        for root in nodes:

            visited = set([root])
            stack = [root]
            directed_edges = []

            while stack:
                current = stack.pop()

                for neighbor in tree.neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)

                        directed_edges.append({'src': current,'tar': neighbor})

            all_possible_tree_edges.append({'edges': directed_edges})
    
    return all_possible_tree_edges

def reformat(graph):
    all_targets = {edge["tar"] for edge in graph["edges"]}
    root_id = next(nid for nid in graph["nodes"] if nid not in all_targets)
    
    def build(node_id):
        node = dict(graph["nodes"][node_id])
        children_edges = sorted(
            [edge for edge in graph["edges"] if edge["src"] == node_id],
            key=lambda e: e.get("order", 0)
        )
        node["children"] = [build(edge["tar"]) for edge in children_edges]
        return node
    
    return build(root_id)

def build_T_all(forest, valid_tree_edges):

    T_all = []
    for tree in valid_tree_edges:
        new_tree = forest.copy()
        new_tree['edges'] = tree['edges']

        for node1, feats1 in new_tree['nodes'].items():
            if feats1['type'] in ['conj']: #, 'cause', 'after', 'before'
                incoming_id = feats1['incoming']
                outgoing_id = feats1['outgoing']

                for node2, feats2 in new_tree['nodes'].items():
                    if feats2['id'] == incoming_id:
                        incoming = node2
                    elif feats2['id'] == outgoing_id:
                        outgoing = node2

                for edge in new_tree['edges']:
                    if edge['src'] == node1 and edge['tar'] == incoming:
                        edge['order'] = 1
                    elif edge['src'] == node1 and edge['tar'] == outgoing:
                        edge['order'] = 2
        
        T_all.append(reformat(new_tree))
    
    return T_all