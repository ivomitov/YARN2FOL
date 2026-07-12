# Gets the children of nodes that don't introduce variables
def get_children_no_var(graph):
    children_no_var_dict = {}
    for edge in graph['edges']:
        src = edge['src']
        tar = edge['tar']
        if graph['nodes'][src].get('outgoing') and not graph['nodes'][src]['variable']: #restrict to elements from F
            children_no_var_dict[src] = children_no_var_dict.get(src, []) + [tar]
        
    return children_no_var_dict

# Get all children
def get_children(graph):
    children_dict = {}
    for edge in graph['edges']:
        src = edge['src']
        tar = edge['tar']
        children_dict[src] = children_dict.get(src, []) + [tar]
    return children_dict

# Extend children to descendants
def get_descendants(node, children_dict, visited=None):
    if visited is None:
        visited = set()
    descendants = []
    for child in children_dict.get(node, []):
        if child not in visited:
            visited.add(child)
            descendants.append(child)
            descendants.extend(get_descendants(child, children_dict, visited))
    return descendants

def get_all_descendants(graph):
    children_dict = get_children(graph)
    descendants_dict = {}
    for node in children_dict:
        descendants_dict[node] = get_descendants(node, children_dict)

    return descendants_dict

def check_compatibility_of_scopes(tree, forest):
    descendants_tree = get_all_descendants(tree)
    descendants_forest = get_all_descendants(forest)

    for k, v in descendants_forest.items():
        if not v:
            continue
        if k not in descendants_tree:
            return False
        for descendant in v:
            if descendant not in descendants_tree[k]:
                return False
    return True

def check_locality_of_features(tree, forest):
    children_tree = get_children(tree)
    children_no_var_forest = get_children_no_var(forest)
    
    for k, v in children_no_var_forest.items():
        if not v:
            continue
        if k not in children_tree:
            return False
        for child in v:
            if child not in children_tree[k]:
                return False
    return True

def check_events_are_always_leaves(tree, forest):
    children_tree = get_children(tree)
    # print(children_tree)

    for node in children_tree.keys():
        if forest['nodes'][node]['type'].startswith("T_"):
            # print(node)
            return False
    return True
