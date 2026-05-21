from src.pipeline import load_yarn, yarn2fol
from pathlib import Path

FOLDER_PATH = "annotations/FRACAS_1premise_yesno"
FILE = "1.yarn.json"

corpus = load_yarn(FOLDER_PATH)
results = yarn2fol(corpus, mode='tptp', verbose=True)

output_path = Path("formulas.txt")
with open(output_path, "w", encoding="utf-8") as f:
    for (path, graph), formulas in zip(corpus, results):
        meta = graph.get("meta", {})
        f.write(f"{'='*60}\n")
        f.write(f"ID:   {meta.get('sent_id', path.name)}\n")
        f.write(f"Text: {meta.get('text', '')}\n")
        f.write(f"Type: {meta.get('type', '')}\n")
        f.write(f"{'-'*60}\n")
        if formulas is None:
            f.write("ERROR or TIMEOUT\n")
        else:
            for i, formula in enumerate(formulas, 1):
                f.write(f"[{i}] {formula}\n\n")
        f.write("\n")

print(f"Formulas written to {output_path}")