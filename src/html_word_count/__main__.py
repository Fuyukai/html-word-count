import argparse
import sys
from collections import deque
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from functools import partial
from pathlib import Path
from typing import TextIO

from lxml import html
from lxml.etree import _Element, _ElementTree

type FileOpener = Callable[[], AbstractContextManager[TextIO]]

# yeah, type checking here is very basic at *best* because lxml is not type annotated,
# and returns funky unions everywhere.


def get_word_count(tree: _ElementTree, xpath: str) -> int:
    """
    Gets the word count for the provided tree, using the provided XPath selector.
    """

    selected = tree.xpath(xpath)
    if not selected:
        selected = tree.getroot().getchildren()

    stack = deque(*selected)
    word_count = 0
    # "recursively" get all text
    while stack:
        el = stack.popleft()
        if isinstance(el, _Element):
            if el.text is not None:
                text = [i for i in el.text.split(" ") if i]
                word_count += len(text)

            for child in el.getchildren():
                stack.append(child)
        else:
            print("got", el)

    return word_count

def main() -> None:
    """
    Main entrypoint.
    """

    parser = argparse.ArgumentParser(usage="Counts words in HTML documents.")
    parser.add_argument(
        "-x", "--xpath",
        help="The target selector to use",
        default="/html/body//main"
    )
    parser.add_argument("FILES", nargs="*", help="The list of files to count words from")

    args = parser.parse_args()
    xpath: str = args.xpath

    files: list[FileOpener] = []

    if not args.FILES:
        # no files, use stdin for piping
        files.append(lambda: nullcontext(sys.stdin))
    else:
        for file in args.FILES:
            p = Path(file)
            files.append(partial(p.open, mode="r", encoding="utf-8"))

    total_count = 0
    for file in files:
        with file() as f:
            parsed: _ElementTree = html.parse(f)
            total_count += get_word_count(parsed, xpath)

    print(total_count)

if __name__ == "__main__":
    main()
