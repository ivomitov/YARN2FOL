import re
import json
from pathlib import Path
from yarn_utils import YARNGraph

from src.preprocessing.preprocessing import reify_he, get_S_descendants, propagate_s_node_information
from src.scope_forest import build_F, build_R, build_scope_forest, add_participants_before_event_principle, add_s_node_scope, events_before_events_principle
from src.constraints import check_compatibility_of_scopes, check_locality_of_features
from src.T_all import get_all_possible_trees, build_T_all
from src.interpretation.standard import interpret_std, clean_formula_std
from src.interpretation.tptp import interpret_tptp, clean_formula_tptp

import traceback
import multiprocessing as mp

grs_path = "src/preprocessing/grs/main.grs"
FOLDER_PATH = "annotations/"
FILE = "1.yarn.json"
TIMEOUT = 20

def extract_number(path):

    match = re.match(r"(\d+)", path.name)
    return int(match.group(1)) if match else float("inf")


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

    graphs = []
    for file_path in all_files:
        with open(file_path, "r", encoding="utf-8") as f:
            graph = json.load(f)
            if graph.get('labels'):  # safer
                graphs.append((file_path, graph))

    return graphs


def process_one(path, yarn_json, output_queue, mode):
    try:
        id2var = {}
        variables = set()
        c_registry = {}

        yarn_graph = YARNGraph(yarn_json)
        yarn_grew = yarn_graph.grew()
        yarn_grew = reify_he(yarn_grew, grs_path)
        
        s_descendants = get_S_descendants(yarn_grew)
        # print(s_descendants)
        yarn_grew = propagate_s_node_information(yarn_grew, s_descendants)

        # save as json
        # with open('output.json', 'w') as f:
        #     json.dump(yarn_grew, f)

        F = build_F(yarn_grew, id2var, variables)
        R = build_R(yarn_grew, id2var, c_registry)
        forest = build_scope_forest(F, R)
        print(forest['nodes'])
        print(forest['edges'])
        
        forest = add_participants_before_event_principle(forest, yarn_grew, R)
        print(forest['edges'])
        forest = add_s_node_scope(forest, s_descendants)
        print(forest['edges'])
        forest = events_before_events_principle(forest, yarn_grew, R)
        print(forest['edges'])

        all_possible_trees = get_all_possible_trees(forest)

        valid_tree_edges = [
            tree for tree in all_possible_trees
            if check_locality_of_features(tree, forest)
        ]
        valid_tree_edges = [
            tree for tree in valid_tree_edges
            if check_compatibility_of_scopes(tree, forest)
        ]

        T_all = build_T_all(forest, valid_tree_edges)

        results = []
        for T in T_all:
            if mode == 'std':
                results.append(clean_formula_std(interpret_std(T, 'NOW', id2var)))
            elif mode == 'tptp':
                results.append(clean_formula_tptp(interpret_tptp(T, 'now', id2var)))

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