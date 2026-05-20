from src.pipeline import load_yarn, yarn2fol

FOLDER_PATH = "annotations/"
FILE = "1.yarn.json"

corpus = load_yarn(FOLDER_PATH+FILE)
yarn2fol(corpus, mode='tptp')