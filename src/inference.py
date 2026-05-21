from src.pipeline import load_yarn, yarn2fol
import subprocess
import tempfile
import os
from collections import defaultdict

def pair_corpus(corpus):
    """Group corpus entries by their problem_id prefix, pairing p and h."""
    groups = defaultdict(dict)
    for path, graph in corpus:
        sent_id = graph['meta']['sent_id'] # e.g. '1p' or '1h'
        if '-' not in sent_id: 
            problem_id = sent_id[:-1]               # e.g. '1'
            role = sent_id[-1]                  # 'p' or 'h'
            groups[problem_id][role] = (path, graph)
        else:
            continue
    return groups


def build_tptp_problem(premise_formula, hypothesis_formula):
    return f"fof(premise, axiom, {premise_formula}).\nfof(hypothesis, conjecture, {hypothesis_formula})."

def run_vampire(tptp_formula, timeout=30):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tptp', delete=False) as f:
        f.write(tptp_formula)
        tmp_path = f.name
    
    try:
        result = subprocess.run(
            ["vampire", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout
        
        if "Theorem" in output:
            return "yes"
        elif "CounterSatisfiable" in output:
            return "no"
        elif "Satisfiable" in output:
            return "unknown"
        else:
            return output
    
    except subprocess.TimeoutExpired:
        return "timeout"
    
    finally:
        os.unlink(tmp_path)

def evaluate_pair(p_formulas, h_formulas):
    """
    yes + unknown -> yes
    no + unknown -> no
    yes + no -> unknown
    """
    answers = set()
    for p_formula in p_formulas:
        for h_formula in h_formulas:
            tptp = build_tptp_problem(p_formula, h_formula)
            answers.add(run_vampire(tptp))

    if 'yes' in answers and 'no' in answers:
        return 'unknown'
    elif 'yes' in answers:
        return 'yes'
    elif 'no' in answers:
        return 'no'
    else:
        return 'unknown'


def evaluate_corpus(folder_path, mode='tptp'):
    corpus = load_yarn(folder_path)
    corpus = [(path, graph) for path, graph in corpus if not graph.get('d')] #!skip discourse relations for now
    groups = pair_corpus(corpus)

    results = []

    for problem_id, pair in sorted(groups.items(), key=lambda x: int(x[0])):
        if 'p' not in pair or 'h' not in pair:
            print(f"{problem_id}: missing premise or hypothesis, skipping")
            continue

        p_path, p_graph = pair['p']
        h_path, h_graph = pair['h']
        expected = h_graph['meta'].get('fracas_answer')

        print(f"\nPair {problem_id}:")
        print(f"  P: {p_graph['meta']['text']}")
        print(f"  H: {h_graph['meta']['text']}")
        print(f"  Expected: {expected}")

        p_formulas = yarn2fol([(p_path, p_graph)], mode=mode)[0]
        h_formulas = yarn2fol([(h_path, h_graph)], mode=mode)[0]

        if p_formulas is None or h_formulas is None:
            print("  ERROR: could not generate formula")
            continue

        p_formulas = [formula.replace('\n ', '') for formula in p_formulas]
        h_formulas = [formula.replace('\n ', '') for formula in h_formulas]

        predicted = evaluate_pair(p_formulas, h_formulas)
        correct = predicted == expected

        print(f"  Predicted: {predicted} | Correct: {correct}")

        results.append({
            "id": problem_id,
            "premise": p_graph['meta']['text'],
            "hypothesis": h_graph['meta']['text'],
            "expected": expected,
            "predicted": predicted,
            "correct": correct,
        })

    return results