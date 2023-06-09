import argparse
from roots_groupping import main_processing_roots
from words_groupping import main_processing_words

def main():
    parser = argparse.ArgumentParser(description=
                                     "Распознавание алломорфных корней и сбор групп слов одного корня")
    parser.add_argument("in_file", type=str, help="RuMorphsLemmas")
    args = parser.parse_args()
    with open(args.in_file, "r") as in_file:
        data = in_file.readlines()
        main_processing_roots(data)
    with open(args.in_file, "r") as in_file:
        data = in_file.readlines()
        main_processing_words(data)

if __name__ == '__main__':
    main()
