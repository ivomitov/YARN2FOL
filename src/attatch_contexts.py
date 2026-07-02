import re
import copy

def s_sort_key(s_id):
    m = re.search(r'\d+', s_id)
    return (int(m.group()) if m else float('inf'), s_id)


def dedupe_edges_by_target(edges):
    edges_by_tar = {}
    for e in edges:
        edges_by_tar.setdefault(e['tar'], []).append(e)

    deduped = []
    for tar, group in edges_by_tar.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            # keep only the edge from the latest src; the earlier src(s)
            # will still get this child indirectly if a path connects them
            best = max(group, key=lambda e: s_sort_key(e['src']))
            deduped.append(best)

    return deduped


def get_leaves(context):
    if not context['children']:
        return [context]
    leaves = []
    for child in context['children']:
        leaves.extend(get_leaves(child))
    return leaves

def attatch_contexts(parent_context, child_context, label):
    """Returns a list of new, independent parent trees with child_context attached."""
    results = []

    if label == 'vertical':
        new_parent = copy.deepcopy(parent_context)
        leaves = get_leaves(new_parent)
        t_leaves = [leaf for leaf in leaves if leaf['type'].startswith("T_")]
        if len(t_leaves) != 1:
            print(
                    f"WARNING: Expected exactly one T_ leaf under {parent_context.get('id')} "
                    f"for vertical attach, found {len(t_leaves)} — skipping this parent_context"
                )
            return results
        t_leaves[0]['children'].append(copy.deepcopy(child_context))
        results.append(new_parent)

    elif label == 'horizontal':
        leaves = get_leaves(parent_context)
        if not leaves:
            raise ValueError(
                f"No leaf found under {parent_context.get('id')} for horizontal attach"
            )
        for i in range(len(leaves)):
            new_parent = copy.deepcopy(parent_context)
            new_leaf = get_leaves(new_parent)[i]  # same position, fresh copy
            new_leaf['children'].append(copy.deepcopy(child_context))
            results.append(new_parent)

    return results


def pick_next_edge(edges):
    srcs_remaining = {e['src'] for e in edges}
    for edge in edges:
        if edge['tar'] not in srcs_remaining:
            return edge
    raise ValueError("No processable edge found — possible cycle in discourse edges")