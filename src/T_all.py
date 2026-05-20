import itertools
import networkx as nx

def get_all_possible_trees(n):
    nodes = list(range(n))
    for seq in itertools.product(nodes, repeat=n-2):
        yield nx.from_prufer_sequence(seq)


def get_all_possible_rooted_directed_trees(forest): # no need for 'rooted'

    nodes = list(forest['nodes'].keys())
    n_nodes = len(nodes)

    all_possible_rooted_directed_tree_edges = []

    for tree in get_all_possible_trees(n_nodes):

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

            all_possible_rooted_directed_tree_edges.append({'edges': directed_edges})
    
    return all_possible_rooted_directed_tree_edges

def get_all_possible_rooted_directed_trees(forest): # no need for 'rooted'

    nodes = list(forest['nodes'].keys())
    n_nodes = len(nodes)

    all_possible_rooted_directed_tree_edges = []

    for tree in get_all_possible_trees(n_nodes):

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

            all_possible_rooted_directed_tree_edges.append({'edges': directed_edges})
    
    return all_possible_rooted_directed_tree_edges

def reformat(graph):
    all_targets = {edge["tar"] for edge in graph["edges"]}
    root_id = next(nid for nid in graph["nodes"] if nid not in all_targets)
    
    def build(node_id):
        node = dict(graph["nodes"][node_id])
        node["children"] = [build(edge["tar"]) for edge in graph["edges"] if edge["src"] == node_id]
        return node
    
    return build(root_id)

def build_T_all(forest, valid_tree_edges):

    T_all = []
    for tree in valid_tree_edges:
        new_tree = forest.copy()
        new_tree['edges'] = tree['edges']
        T_all.append(reformat(new_tree))
    
    return T_all