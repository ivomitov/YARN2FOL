from src.pipeline import load_yarn, yarn2fol
from pathlib import Path
import subprocess
import tempfile
import os
import re
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

def negate_inside_s_context(formula):
    """
    Transforms ?[X]: (s(X) & BODY)
    into       ?[X]: (s(X) & ~(BODY))
    """
    import re
    match = re.match(r'(\?\[(\w+)\]:\s*\(s\(\2\)\s*&\s*)(.+)\)$', formula.strip())
    if match:
        prefix = match.group(1)
        body   = match.group(3)
        return f"{prefix}~({body}))"
    else:
        # fallback: negate the whole formula
        return f"~({formula})"


def build_tptp_problem(problem_id, premise_formula, hypothesis_formula, background_path="src/axioms/"):
    general_axioms = Path(background_path + "axioms.p").read_text() if Path(background_path).exists() else ""
    problems_specific_axioms_path = background_path + f"{problem_id}_axioms.p"
    problems_specific_axioms = Path(problems_specific_axioms_path).read_text() if Path(problems_specific_axioms_path).exists() else ""
    if "apcom" in premise_formula and "win" in premise_formula:
        print(f"{general_axioms}\n{problems_specific_axioms}\nfof(premise, axiom, {premise_formula}).\nfof(hypothesis, conjecture, {hypothesis_formula}).")
    return f"{general_axioms}\n{problems_specific_axioms}\nfof(premise, axiom, {premise_formula}).\nfof(hypothesis, conjecture, {hypothesis_formula})."

def run_vampire(tptp_formula, timeout=10):
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
        
        match = re.search(r'SZS status (\w+)', output)
        if match:
            status = match.group(1)
            if status == "Theorem":
                return "yes"
            else:
                return status
        return output
    
    except subprocess.TimeoutExpired:
        return "timeout"
    
    finally:
        os.unlink(tmp_path)


def evaluate_pair(problem_id, p_formulas, h_formulas):
    """
    Try all p/h combinations.
    yes + unknown -> yes
    no + unknown -> no
    yes + no -> unknown
    """
    answers = set()
    for p_formula in p_formulas:
        for h_formula in h_formulas:
            # test p => h
            tptp = build_tptp_problem(problem_id, p_formula, h_formula)
            if run_vampire(tptp) == "yes":
                answers.add("yes")
            else:
                # test p => ~h
                tptp_neg = build_tptp_problem(problem_id, p_formula, negate_inside_s_context(h_formula))
                if run_vampire(tptp_neg) == "yes":
                    answers.add("no")
                else:
                    answers.add("unknown")

    if "yes" in answers and "no" in answers:
        return "unknown (yes&no)"
    elif "yes" in answers:
        return "yes"
    elif "no" in answers:
        return "no"
    else:
        return "unknown"


def evaluate_corpus(folder_path, mode='tptp'):
    corpus = load_yarn(folder_path)
    #corpus = [(path, graph) for path, graph in corpus if not graph.get('d')] #!skip discourse relations for now
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
            results.append({
                "id": problem_id,
                "premise": p_graph['meta']['text'],
                "hypothesis": h_graph['meta']['text'],
                "expected": expected,
                "predicted": "error",
                "correct": False,
            })
            continue

        p_formulas = [formula.replace('\n ', '') for formula in p_formulas]
        h_formulas = [formula.replace('\n ', '') for formula in h_formulas]

        predicted = evaluate_pair(problem_id, p_formulas, h_formulas)
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