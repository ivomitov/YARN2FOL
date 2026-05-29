from collections import defaultdict

def build_F(yarn_grew_graph, id2var, variables):

    def fresh_variable(base='e'):
        i = 0
        while True:
            variable = base if i == 0 else f"{base}{i}"
            if variable not in variables:
                variables.add(variable)
                break
            i += 1
        return variable

    F = []
    nodes = yarn_grew_graph['nodes']
    edges = yarn_grew_graph['edges']

    src_to_tars = defaultdict(list)
    tar_to_srcs = defaultdict(list)
    for edge in edges:
        src_to_tars[edge['src']].append(edge['tar'])
        tar_to_srcs[edge['tar']].append(edge['src'])

    for node, feats in nodes.items():

        if feats['type'] == 'S':
            id2var[node] = feats['var']
            variables.add(feats['var'])

            scope = None
            for src in tar_to_srcs[node]:
                if nodes[src]['type'] == 'C':
                    scope = tar_to_srcs[src][0] if tar_to_srcs[src] else None

            F.append({
                'id': node,
                'scope': scope,
                'incoming': None,
                'outgoing': None,
                'S': feats['event'],
                'type': '∃',
                'variable': id2var[node],
                'tar_label': 'S',
            })

        if (feats['type'] in ['L', 'H']) and feats['feat'] in ['quant', 'temp']:
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    edge_label = feats['value'] if feats['value'] else feats['feat']
                    src = next((s for s in tar_to_srcs[node] if nodes[s]['type'] in ['L', 'H'] and nodes[s]['feat'] == 'quant'), None)

                    if feats['feat'] == 'quant':
                        if edge_label == 'exists':
                            q_type = '∃'
                        elif edge_label == 'forall':
                            q_type = '∀'
                        else:
                            q_type = f'Q_{edge_label}'
                    else:
                        q_type = f'T_{edge_label}'

                    tar_label = nodes[tar].get('pred', nodes[tar].get('concept'))

                    if tar not in id2var:
                        id2var[tar] = fresh_variable(base=tar_label[0])
                    else:
                        raise AssertionError(f"Double quantification. Variable for {tar} already exists in id2var.")

                    F.append({
                        'id': tar,
                        'scope': src if feats['type'] == "H" else None,
                        'incoming': node, # node
                        'outgoing': None,
                        'S': feats['event'],
                        'type': q_type,
                        'variable': id2var[tar],
                        'tar_label': tar_label,
                    })

        if (feats['type'] in ['L', 'H']) and feats['feat'] in ['neg', 'modal', 'aspect']:
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] in ['V', 'L', 'H']:
                    edge_label = feats['value'] if feats['value'] else feats['feat']
                    src = tar_to_srcs[node][0] if tar_to_srcs[node] else None

                    F.append({
                        'id': node,
                        'scope': src,
                        'incoming': None,
                        'outgoing': tar,
                        'S': feats['event'],
                        'type': edge_label,
                        'variable': None,
                        'tar_label': None,
                    })

    for node, feats in nodes.items():
        if feats['type'] == 'V' and node not in id2var:
            id2var[node] = feats.get('pred', feats.get('concept', '')).upper()

    F = [f for f in F if f['type'] not in ['perfective', 'state', 'habitual']]

    return F

def build_R(yarn_grew, id2var, c_registry):

    def add_to_R(R, key, connective, relations):
        if key not in R:
            R[key] = {'and': [], 'or': []}
        R[key][connective].extend(relations)

    nodes = yarn_grew['nodes']
    edges = yarn_grew['edges']

    src_to_tars = defaultdict(list)
    tar_to_srcs = defaultdict(list)
    for edge in edges:
        src_to_tars[edge['src']].append(edge['tar'])
        tar_to_srcs[edge['tar']].append(edge['src'])
    
    R = {}
    for node, feats in nodes.items():
        if feats['type'] == "E":
            if feats['rel'].startswith('op'):
                continue

            edge_label = feats['rel']
            for src in tar_to_srcs[node]:
                for tar in src_to_tars[node]:
                    key = tar if id2var[src].isupper() else src
                    if nodes[tar]['concept'] == 'or':
                        grandchildren = [src_to_tars[e][0] for e in src_to_tars[tar]]
                        add_to_R(R, key, 'or', [(edge_label, src, t) for t in grandchildren])
                    elif nodes[tar]['concept'] == 'and':
                        grandchildren = [src_to_tars[e][0] for e in src_to_tars[tar]]
                        add_to_R(R, key, 'and', [(edge_label, src, t) for t in grandchildren])
                    else:
                        add_to_R(R, key, 'and', [(edge_label, src, tar)])

        if feats['type'] == "L" and feats['feat'] == 'num' and feats['value'] == 'plural':
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    add_to_R(R, tar, 'and', [('plural', tar)])

        if feats['type'] == "L" and feats['feat'] == 'def' and feats['value'] == 'definite':
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    c_index = len(c_registry) + 1
                    if tar not in c_registry:
                        c_registry[tar] = f'C{c_index}'
                    add_to_R(R, tar, 'and', [(c_registry[tar], tar)])

        if feats['type'] == "C":
            edge_label = feats['rel']
            for src in tar_to_srcs[node]:
                for tar in src_to_tars[node]:
                    add_to_R(R, tar, 'and', [(edge_label, src, tar)])

        if feats['type'] == "L" and feats['feat'] in ['manner', 'loc', 'dir', 'duration', 'mod', 'freq']:
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    edge_label = feats['value'] if feats['value'] else feats['feat']
                    for src in tar_to_srcs[node]:
                        src = src.split('-')[0]
                        key = src if id2var[tar].isupper() else tar
                        add_to_R(R, key, 'and', [(edge_label, src, tar)])
    return R

def build_scope_forest(F, R):

    forest = {'nodes':{}, 'edges':[]}

    for i, f in enumerate(F):
        forest['nodes'][i] = {
            'id': f['id'],
            'scope': f['scope'],
            'incoming': f['incoming'],
            'outgoing': f['outgoing'],
            'S': f['S'],
            'type': f['type'],
            'variable': f['variable'],
            'tar_label': f['tar_label'],
            'relations': R.get(f['id'], {'and': [], 'or': []}),
        }

    for k1, v1 in forest['nodes'].items():
        for k2, v2 in forest['nodes'].items():
            if v1['incoming'] and v2['scope'] and v1['incoming'] == v2['scope']:
                forest['edges'].append({'src':k1, 'tar':k2})
            if v1['id'] and v2['outgoing'] and v1['id'] == v2['outgoing']:
                forest['edges'].append({'src':k2, 'rel':'', 'tar':k1})
            if v1['outgoing'] and v2['incoming'] and v1['outgoing'] == v2['incoming']:
                forest['edges'].append({'src':k1, 'rel':'', 'tar':k2})

    return forest

# Predicates are introduced after their arguments (E relations)
# Arguments are introduced after their predicates (C relations)
#! These should be rewritten as constraints, rather than adding scope in the scope forest.

def add_participants_before_event_principle(forest, yarn_grew, R): # maybe change the name?

    for _, rels in R.items():
        for rel in rels['and'] + rels['or']:
            if len(rel) == 3:
                src = rel[1]
                tar = rel[2]

                for k1, v1 in forest['nodes'].items():
                    for k2, v2 in forest['nodes'].items():
                        if v1['id'] == src and v2['id'] == tar and \
                            yarn_grew['nodes'][src]['type'] == 'V' and \
                            yarn_grew['nodes'][tar]['type'] == 'V':
                            
                            forest['edges'].append({'src':k2, 'tar':k1})

                        if v1['id'] == src and v2['id'] == tar and \
                            yarn_grew['nodes'][src]['type'] == 'V' and \
                            yarn_grew['nodes'][tar]['type'] == 'S':
                            
                            forest['edges'].append({'src':k1, 'tar':k2}) # participant after event in the case of C edges
    
    return forest

def add_s_node_scope(forest, s_descendants):
    for k1, v1 in forest['nodes'].items():
        if v1['id'] in s_descendants:
            for k2, v2 in forest['nodes'].items():
                if v2['id'] in s_descendants[v1['id']]:
                    forest['edges'].append({'src':k1, 'tar':k2})
                    
    return forest