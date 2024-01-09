import argparse
from pathlib import Path

from retype.optimizer import Optimizer
from retype.parser import Parser
from retype.writer import HtmlWriter

def main():
    argParser = argparse.ArgumentParser(description='Converts EPUB to HTML')
    argParser.add_argument('input', type=str, nargs='*', help='Input file path')
    args = argParser.parse_args()

    for input in args.input:
        parser = Parser(input)
        Optimizer(parser.content())
        writer = HtmlWriter(parser.content())

        # Use original file name, with .HTML extension
        with open(Path(input).parent / (Path(input).stem + '.html'), 'w', encoding='utf-8') as file:
            file.write(writer.output())

if __name__ == '__main__':
    main()