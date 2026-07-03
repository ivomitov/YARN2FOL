from collections import defaultdict
import copy

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

    discourse = {'nodes':{},
                 'edges':[]}
    
    nodes = yarn_grew_graph['nodes']
    edges = yarn_grew_graph['edges']

    src_to_tars = defaultdict(list)
    tar_to_srcs = defaultdict(list)
    for edge in edges:
        src_to_tars[edge['src']].append(edge['tar'])
        tar_to_srcs[edge['tar']].append(edge['src'])

    for node, feats in nodes.items():

        if feats['type'] == 'S':
            context = feats['var']
            id2var[node] = feats['var']
            variables.add(feats['var']) 
            srcs = tar_to_srcs[node]

            discourse['nodes'][context] = {'F':[], 'R':{}}

            if not srcs:

                discourse['nodes'][context]['F'].append({
                            'id': node,
                            'scope': None, # None
                            'incoming': None,
                            'outgoing': None,
                            'S': context,
                            'type': 'S',
                            'variable': id2var[node],
                            'tar_label': 'S',
                        })
            else:
                for src in srcs:
                    src_feats = nodes.get(src)

                    if src_feats['type'] == 'C':
                        scope = tar_to_srcs[src][0]
                        scope = nodes[scope]['event']

                        existing_ids = {f['id'] for f in discourse['nodes'][context]['F']}

                        if node not in existing_ids:

                            discourse['nodes'][context]['F'].append({
                                    'id': node,
                                    'scope': scope, # the src pred
                                    'incoming': None,
                                    'outgoing': None,
                                    'S': context,
                                    'type': 'S_c',
                                    'variable': id2var[node],
                                    'tar_label': 'S',
                                })
                        
                        discourse['edges'].append({'src':scope, 'label':'vertical', 'tar':context})
                        
                    elif src_feats['type'] == 'D' and src_feats['disc'] in ['BEFORE', 'AFTER', 'COORDINATION', 'RESULT', 'CONSEQUENCE']:
                        scope = tar_to_srcs[src][0]if tar_to_srcs[src] else None 

                        discourse['nodes'][context]['F'].append({
                                'id': node, #node
                                'scope': scope, # the src S node
                                'incoming': None, #not necessary?
                                'outgoing': None,
                                'S': context,
                                'type': "S_" + src_feats['disc'].lower(),
                                'variable': id2var[node],
                                'tar_label': 'S',
                            })
                        
                        discourse['edges'].append({'src':scope, 'label':'horizontal', 'tar':context})

        if (feats['type'] in ['L', 'H']) and feats['feat'] in ['quant', 'temp'] and feats['value']:
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    context = feats['event']
                    edge_label = feats['value']
                    src = next((s for s in tar_to_srcs[node] if nodes[s]['type'] in ['L', 'H'] and nodes[s]['feat'] == 'quant'), None)

                    if feats['feat'] == 'quant':
                        if edge_label == 'exists':
                            q_type = 'Q_exists'
                        elif edge_label == 'forall':
                            q_type = 'Q_forall'
                        else:
                            q_type = f'Q_{edge_label}'
                    else:
                        q_type = f'T_{edge_label}'

                    tar_label = nodes[tar].get('pred', nodes[tar].get('concept'))

                    if tar not in id2var:
                        id2var[tar] = fresh_variable(base=tar_label[0])
                    else:
                        raise AssertionError(f"Double quantification. Variable for {tar} already exists in id2var.")

                    discourse['nodes'][context]['F'].append({
                        'id': tar,
                        'scope': src if feats['type'] == "H" else None,
                        'incoming': node, # node
                        'outgoing': None,
                        'S': context,
                        'type': q_type,
                        'variable': id2var[tar],
                        'tar_label': tar_label,
                    })

        if (feats['type'] in ['L', 'H']) and feats['feat'] in ['neg', 'modal']: # no modal?
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] in ['V', 'L', 'H']:
                    context = feats['event']
                    edge_label = feats['value'] if feats['value'] else feats['feat']
                    src = tar_to_srcs[node][0] if tar_to_srcs[node] else None

                    discourse['nodes'][context]['F'].append({
                        'id': node,
                        'scope': src,
                        'incoming': None,
                        'outgoing': tar,
                        'S': context,
                        'type': edge_label,
                        'variable': None,
                        'tar_label': None,
                    })

    for node, feats in nodes.items():
        if feats['type'] == 'V' and node not in id2var:
            id2var[node] = feats.get('pred', feats.get('concept', '')).upper()

    return discourse

def build_R(yarn_grew, id2var, discourse, c_registry):

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
    
    for node, feats in nodes.items():
        if feats['type'] == "E":
            context = feats['event']
            R = discourse['nodes'][context]['R']
            edge_label = feats['rel']
            for src in tar_to_srcs[node]:
                if nodes[src].get('concept') in ['and', 'or'] and edge_label.startswith('op'):
                    continue

                for tar in src_to_tars[node]:
                    key = tar if id2var[src].isupper() else src
                    if nodes[tar].get('concept') == 'or':
                        grandchildren = [src_to_tars[e][0] for e in src_to_tars[tar]]
                        add_to_R(R, key, 'or', [(edge_label, src, t) for t in grandchildren])
                    elif nodes[tar].get('concept') == 'and':
                        grandchildren = [src_to_tars[e][0] for e in src_to_tars[tar]]
                        add_to_R(R, key, 'and', [(edge_label, src, t) for t in grandchildren])
                    else:
                        add_to_R(R, key, 'and', [(edge_label, src, tar)])

        if feats['type'] == "L" and feats['feat'] == 'num' and feats['value'] == 'plural':
            context = feats['event']
            R = discourse['nodes'][context]['R']
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    add_to_R(R, tar, 'and', [('plural', tar)])

        if feats['type'] == "L" and feats['feat'] == 'def' and feats['value'] == 'definite':
            context = feats['event']
            R = discourse['nodes'][context]['R']
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

                    context = yarn_grew['nodes'][tar]['event']
                    R = discourse['nodes'][context]['R']

                    add_to_R(R, tar, 'and', [(edge_label, src, tar)])
        
        if feats['type'] in ["L", "H"] and feats['feat'] == 'temp' and not feats['value']: #unlabeled temp
            context = feats['event']
            R = discourse['nodes'][context]['R']
            edge_label = 'include'
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    for src in tar_to_srcs[node]:
                        src = src.split('-')[0]
                        if id2var[tar].isupper():
                            add_to_R(R, src, 'and', [(edge_label, src, tar)])
                        else:
                            add_to_R(R, tar, 'and', [(edge_label, src, tar)])
        
        if feats['type'] in ["L", "H"] and feats['feat'] == 'duration': #duration
            context = feats['event']
            R = discourse['nodes'][context]['R']
            edge_label = 'total_overlap'
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    for src in tar_to_srcs[node]:
                        src = src.split('-')[0]
                        if id2var[tar].isupper():
                            add_to_R(R, src, 'and', [(edge_label, src, tar)])
                        else:
                            add_to_R(R, tar, 'and', [(edge_label, src, tar)])
        
        if feats['type'] in ["L", "H"] and feats['feat'] == 'aspect': #aspect
            context = feats['event']
            R = discourse['nodes'][context]['R']
            edge_label = 'aspect_' + feats['value']
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    add_to_R(R, tar, 'and', [(edge_label, tar)])


        if feats['type'] == "L" and feats['feat'] in ['manner', 'loc', 'dir', 'mod']:
            context = feats['event']
            R = discourse['nodes'][context]['R']
            for tar in src_to_tars[node]:
                if nodes[tar]['type'] == 'V':
                    edge_label = feats['value'] if feats['value'] else feats['feat']
                    for src in tar_to_srcs[node]:
                        src = src.split('-')[0]
                        key = src if id2var[tar].isupper() else tar
                        add_to_R(R, key, 'and', [(edge_label, src, tar)])

    return discourse

def build_scope_forests(discourse):

    for FR in discourse['nodes'].values():
        
        F = FR['F']
        R = FR['R']
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

                # C edges id - scope

                    if v2['scope'] and v1['id'] == v2['scope']: # quant, temp
                        forest['edges'].append({'src':k1, 'tar':k2})

                    if v1['incoming'] and v2['scope'] and v1['incoming'] == v2['scope']: # quant, temp
                        forest['edges'].append({'src':k1, 'tar':k2})

                    if v1['id'] and v2['outgoing'] and v1['id'] == v2['outgoing']: #neg L edge #and v2['type'] not in ["conj_coor", "conseq_sub", "before_sub", "after_sub"]:
                        forest['edges'].append({'src':k2, 'tar':k1})

                    if v1['outgoing'] and v2['incoming'] and v1['outgoing'] == v2['incoming']: # neg H edge
                        forest['edges'].append({'src':k1, 'tar':k2})
        
        FR['forest'] = forest

    return discourse

# Predicates are introduced after their arguments (E relations)
# Arguments are introduced after their predicates (C relations)
#! These should be rewritten as constraints, rather than adding scope in the scope forest.

def add_participants_before_event_principle(forest, yarn_grew, R): # maybe change the name?

    for _, rels in R.items():
        for rel in rels['and'] + rels['or']:
            if len(rel) == 3 and rel[0] != 'precede': #! a little sloppy maybe; precede is handled by other scope stuff
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

def rewrite_conseq(discourse):
    discourse_nodes = discourse['nodes']
    discourse_edges = discourse['edges']

    for disc_edge in discourse_edges:
        if disc_edge['label'] == 'horizontal':
            src_forest_id = disc_edge['src']
            tar_forest_id = disc_edge['tar']

            src_forest = discourse_nodes[src_forest_id]['forest']
            tar_forest = discourse_nodes[tar_forest_id]['forest']

            src_forest_nodes = src_forest['nodes']
            src_forest_edges = src_forest['edges']
            tar_forest_nodes = tar_forest['nodes']
            tar_forest_edges = tar_forest['edges']

            for k2,v2 in list(tar_forest_nodes.items()):
                if v2['id'] == tar_forest_id and v2['type'] == "S_consequence":
                    neg2_id = max(tar_forest_nodes.keys())+1
                    neg2_feats = {
                        'id':neg2_id,
                        'type':'neg',
                        'variable': None,
                        'tar_label': None,
                        'relations':{'and': [], 'or': []},
                    }
                    tar_forest_nodes[neg2_id] = neg2_feats
                    tar_forest_edges.append({'src':neg2_id, 'tar':k2})
            
                    for k1,v1 in list(src_forest_nodes.items()):
                        if v1['id'] == src_forest_id:
                            neg1_id = max(src_forest_nodes.keys())+1
                            neg1_feats = {
                                'id':neg1_id,
                                'type':'neg',
                                'variable': None,
                                'tar_label': None,
                                'relations':{'and': [], 'or': []},
                            }
                            src_forest_nodes[neg1_id] = neg1_feats
                            src_forest_edges.append({'src':neg1_id, 'tar':k1})

                            break

                    break

    return discourse