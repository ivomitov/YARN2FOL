import re
import json
from pathlib import Path
import copy
from yarn_utils import YARNGraph

from src.preprocessing.preprocessing import reify_he, get_S_descendants, propagate_s_node_information
from src.scope_forest import build_F, build_R, build_scope_forests, add_participants_before_event_principle, add_s_node_scope, events_before_events_principle, rewrite_conseq
from src.constraints import check_compatibility_of_scopes, check_locality_of_features
from src.attatch_contexts import dedupe_edges_by_target, pick_next_edge, attatch_contexts
from src.T_all import get_all_possible_trees, build_T_all
from src.interpretation.standard import interpret_std, clean_formula_std
from src.interpretation.tptp import interpret_tptp, clean_formula_tptp

import traceback
import multiprocessing as mp

grs_path = "src/preprocessing/grs/main.grs"
FOLDER_PATH = "annotations/"
FILE = "1.yarn.json"
TIMEOUT = 10

def extract_number(path):

    match = re.match(r"(\d+)", path.name)
    return int(match.group(1)) if match else float("inf")

# SKIP_IDS = {1, 59, 107, 108, 172, 191, 193, 195, 216, 229, 230, 233, 236, 237, 239, 244, 245, 249, 250, 307, 315, 320, 322, 324} | set(range(258))
SKIP_IDS = {1, 59, 107, 108, 172, 191, 193, 195, 216, 229, 230, 233, 236, 237, 239, 244, 245, 249, 250, 307, 315, 320, 322, 324}

def load_yarn(input_path, recursive=False):
    if isinstance(input_path, (str, Path)):
        input_path = [input_path]

    all_files = []

    for path in input_path:
        path = Path(path)

        if path.is_file():
            if path.name.endswith(".yarn.json"):
                all_files.append(path)

        elif path.is_dir():
            files = path.rglob("*.yarn.json") if recursive else path.glob("*.yarn.json")
            all_files.extend(files)

        else:
            raise FileNotFoundError(f"{path} does not exist")

    all_files = sorted(all_files, key=extract_number)
    all_files = [f for f in all_files if extract_number(f) not in SKIP_IDS]

    graphs = []
    for file_path in all_files:
        with open(file_path, "r", encoding="utf-8") as f:
            graph = json.load(f)
            if graph.get('labels'):
                graphs.append((file_path, graph))

    return graphs

def process_one(path, yarn_json, output_queue, mode):
    try:
        id2var = {}
        variables = set()
        c_registry = {}

        yarn_graph = YARNGraph(yarn_json)
        # print(yarn_graph)
        yarn_grew = yarn_graph.grew()
        yarn_grew = reify_he(yarn_grew, grs_path)
        
        s_descendants = get_S_descendants(yarn_grew)
        # print(s_descendants)
        yarn_grew = propagate_s_node_information(yarn_grew, s_descendants)
        
        # print(json.dumps(yarn_grew, indent=2, default=str))

        # save as json
        # with open('output.json', 'w') as f:
        #     json.dump(yarn_grew, f)

        discourse = build_F(yarn_grew, id2var, variables)
        discourse = build_R(yarn_grew, id2var, discourse, c_registry)
        discourse = build_scope_forests(discourse)
        # print(json.dumps(discourse, indent=2, default=str))

        for key, context in discourse['nodes'].items():
            forest = context['forest']
            R = context['R']
            # print(json.dumps(forest['nodes'], indent=2, default=str))
            forest = add_participants_before_event_principle(forest, yarn_grew, R)
            # print(forest['edges'])
            forest = add_s_node_scope(forest, s_descendants)
            # print(forest['edges'])
            forest = events_before_events_principle(forest, yarn_grew)
            # print(forest['edges'])
            forest = rewrite_conseq(forest)
            # print(json.dumps(forest['nodes'], indent=2, default=str))
            # print(forest['edges'])
            all_possible_trees = get_all_possible_trees(forest)

            valid_tree_edges = [tree for tree in all_possible_trees if check_locality_of_features(tree, forest)]
            # print()
            # print(valid_tree_edges)

            valid_tree_edges = [tree for tree in valid_tree_edges if check_compatibility_of_scopes(tree, forest)]
            # print()
            # print(valid_tree_edges)
            T_all = build_T_all(forest, valid_tree_edges)
            # print()
            # print(T_all)
            discourse['nodes'][key] = T_all

        # print(json.dumps(discourse, indent=2, default=str))

        discourse['edges'] = dedupe_edges_by_target(discourse['edges'])

        remaining_edges = discourse['edges'][:]

        while remaining_edges:
            edge = pick_next_edge(remaining_edges)
            src = edge['src']
            label = edge['label']
            tar = edge['tar']

            new_versions = []
            for parent_context in discourse['nodes'][src]:
                for child_context in discourse['nodes'][tar]:
                    new_versions.extend(attatch_contexts(parent_context, child_context, label))

            discourse['nodes'][src] = new_versions

            del discourse['nodes'][tar]
            remaining_edges.remove(edge)
            discourse['edges'].remove(edge)

        # print(json.dumps(discourse, indent=2, default=str))

        assert len(discourse['nodes']) == 1, f"Expected 1 remaining node, got {len(discourse['nodes'])}"
        T_all = next(iter(discourse['nodes'].values()))
        # print(T_all)

        results = []
        for T in T_all:
            if mode == 'std':
                results.append(clean_formula_std(interpret_std(T, 'NOW', id2var)))
            elif mode == 'tptp':
                results.append(clean_formula_tptp(interpret_tptp(T, 'now', 'now', id2var)))

        output_queue.put({
            "path": str(path),
            "meta": yarn_json.get("meta", {}),
            "results": results,
            "error": None
        })

    except Exception as e:
        output_queue.put({
            "path": str(path),
            "meta": yarn_json.get("meta", {}),
            "results": None,
            "error": traceback.format_exc()
        })

def yarn2fol(yarn_graphs, mode, verbose=False):
    all_results = []
    
    for path, yarn_json in yarn_graphs:

        print("\nProcessing:", path)

        output_queue = mp.Queue()
        p = mp.Process(target=process_one, args=(path, yarn_json, output_queue, mode))

        p.start()
        p.join(TIMEOUT)

        if p.is_alive():
            p.terminate()
            p.join()
            print(path)
            print("TIMEOUT after", TIMEOUT, "seconds")
            all_results.append(None)
            continue

        if output_queue.empty():
            print(path)
            print("No output returned")
            all_results.append(None)
            continue

        result = output_queue.get()

        if result["error"]:
            print(path)
            print("ERROR:")
            print(result["error"])
            all_results.append(None)
            continue
        
        if verbose:
            print(result["meta"].get("type"), ":", result["meta"].get("text"))

            for r in result["results"]:
                print(r)
                print("---")

        all_results.append(result["results"])

    return all_results