import argparse
import json
from wf_trees_building import main_processing

def main():
    parser = argparse.ArgumentParser(description="Построение словообразовательных деревьев")
    parser.add_argument("in_file", type=str, help="json-файл с группами слов одного корня")
    parser.add_argument("vertices_file", type=str, help="txt-файл с вершинами деревьев (можно оставить пустым)")
    args = parser.parse_args()
    with open(args.in_file) as in_file:
        data = json.load(in_file)
        with open(args.vertices_file) as vertices_file:
            custom_vertices = vertices_file.readlines()
            main_processing(data, custom_vertices)

if __name__ == '__main__':
    main()
