import csv
from sklearn.metrics import precision_recall_fscore_support, classification_report
from src.inference import evaluate_corpus

FOLDER_PATH = "annotations/FRACAS_1premise_yesno/"

results = evaluate_corpus(FOLDER_PATH, mode='tptp')

correct = sum(r['correct'] for r in results)
total = len(results)

expected  = [r['expected']  for r in results]
predicted = [r['predicted'] for r in results]

labels = sorted(set(expected + predicted))
precision, recall, f1, support = precision_recall_fscore_support(expected, predicted, labels=labels, zero_division=0)

print(f"\n=== Results ===")
print(f"Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")
print(f"\n=== Per-class Metrics ===")
print(f"{'Label':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
print("-" * 55)
for label, p, r, f, s in zip(labels, precision, recall, f1, support):
    print(f"{label:<20} {p:>10.3f} {r:>10.3f} {f:>10.3f} {s:>10}")

print(f"\n=== Macro Averages ===")
macro_p, macro_r, macro_f, _ = precision_recall_fscore_support(expected, predicted, average='macro', zero_division=0)
print(f"{'Macro Precision:':<20} {macro_p:.3f}")
print(f"{'Macro Recall:':<20} {macro_r:.3f}")
print(f"{'Macro F1:':<20} {macro_f:.3f}")

print(f"\n=== Per-item Results ===")
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