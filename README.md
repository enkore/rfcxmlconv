# rfcxmlconv

rfcxmlconv is a small tool, that converts RFC2629-like documents to Markdown or LaTeX.

## Requirements

- Python 2.7 or newer
- For LaTeX: recent pdflatex version, KOMA-Script, hyperref

## Usage

`main.py -f <format> <file>`

- `format` may be either markdown (default) or latex.
- `file` is the input file.
- Output is written to standard output, use shell redirects for file access: `./main.py -f latex bullocks.xml > bullocks.tex && pdflatex bullocks.tex`

## License

GPLv2