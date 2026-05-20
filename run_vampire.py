from src.inference import evaluate_corpus

FOLDER_PATH = "annotations/FRACAS_1premise_yesno/"

results = evaluate_corpus(FOLDER_PATH, mode='tptp')

correct = sum(r['correct'] for r in results)
total = len(results)
print(f"\n=== Results ===")
print(f"Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")

for r in results:
    status = "✓" if r['correct'] else "✗"
    print(f"{status} [{r['id']}] expected={r['expected']} predicted={r['predicted']} | {r['premise']} => {r['hypothesis']}")