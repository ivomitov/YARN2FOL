import csv
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

with open("results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "premise", "hypothesis", "expected", "predicted", "correct"])
    writer.writeheader()
    for r in results:
        writer.writerow({
            "id": r["id"],
            "premise": r["premise"],
            "hypothesis": r["hypothesis"],
            "expected": r["expected"],
            "predicted": r["predicted"],
            "correct": 1 if r["correct"] else 0,
        })

print(f"\nResults saved to results.csv")