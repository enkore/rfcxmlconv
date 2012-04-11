# rfcxmlconv

rfcxmlconv is a small tool, that converts RFC2629-like documents to Markdown or LaTeX.

## Requirements

- Python 2.7 or newer
- For LaTeX: recent pdflatex version, KOMA-Script, hyperref

## Usage

`main.py -f <format> <file>`

format may be either markdown (default) or latex.

file is the input file.

Output is written to terminal. Both output methods support nearly all features of RFC2629-like documents, such as: nested sections, paragraphs, tables, lists, artwork etc.

## License

GPLv2