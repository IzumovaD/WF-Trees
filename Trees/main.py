import argparse
import json
from wf_trees_building import main_processing

def main():
    parser = argparse.ArgumentParser(description="Построение словообразовательных деревьев")
    parser.add_argument("in_file", type=str, help="json-файл с группами слов одного корня")
    args = parser.parse_args()
    with open(args.in_file) as in_file:
        data = json.load(in_file)
        main_processing(data)

if __name__ == '__main__':
    main()
