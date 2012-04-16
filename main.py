#!/usr/bin/env python
#    Copyright 2012 Marian Beermann
#    https://github.com/enkore/rfcxmlconv

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 2.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import re
import sys
import os
from subprocess import call
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from cStringIO import StringIO

class Output(object):
	def __init__(self, parser):
		pass

	def getvalue(self):
		pass

	def Compile(self, file):
		pass

	def Metadata(self, data):
		# data = dict()
		#	title
		# 	authors = list()
		#		= dict
		#		fullname
		#		organization
		#		email
		#		uri
		#	date
		#	area
		#	workgroup
		#	abstract
		pass

	def AppendSection(self, title, text, level, anchor):
		# title
		# nachor (optional)
		# text
		# level = int
		#	0 = section
		#	1 = subsection
		#	2 = subsubsection
		# anchor
		pass

class TeXOutput(Output):
	extension = ".tex"
	_section_labels = ["section", "subsection", "subsubsection", "paragraph", "subparagraph"]
	_list_styles = {
		"numbers": "enumerate",
		"symbols": "itemize",
		"hanging": "description",
		"empty": "itemize",
	}
	_alignments = {
		"center": "c",
		"left": "l",
		"right": "r",
	}

	def __init__(self, parser):
		self.o = StringIO()
		self.p = parser

	def _escape(self, text):
		if type(text).__name__ == "dict":
			for key, item in text.items():
				text[key] = self._escape(item)
		if type(text).__name__ == "list":
			for i, item in enumerate(text):
				text[i] = self._escape(item)
		if type(text).__name__ == "str" or type(text).__name__ == "unicode":
			text = text.replace("\\", "\\textbackslash ")
			text = text.replace("~", "\\textasciitilde ")
			text = text.replace("^", "\\verb|^|")
			text = re.sub(r"(#|&|\$|%|{|}|_)", r"\\\1", text)
			text = re.sub(r"\"([^\"]*)\"", r"\\enquote{\1}", text)
		return text

	def getvalue(self):
		return self.o.getvalue() + "\\end{document}"

	def Compile(self, file):
		[call(["pdflatex", "-interaction=batchmode", "-quiet", "-output-directory=%s" % os.path.dirname(file), file]) for i in [1,2,3]]

	def Metadata(self, data):
		data = self._escape(data)

		at = unicode()
		data["authors"] = "\\and ".join([e["fullname"] for e in data["authors"]])

		preamble = open("preamble.tex").read() % data

		self.o.write(preamble)

	def AppendSection(self, title, text, level, anchor):
		title = self._escape(title)

		self.o.write("\\" + self._section_labels[level] + "{" + title + "}")
		if anchor:
			self.o.write("\\label{" + anchor + "}")

		self.o.write("\n\n")

		[self._do_element(e) for e in list(text)]

	def _do_element(self, element):
		if element.tag == "t" and element.text:
			self.o.write(self._escape(element.text))
		if element.tag == "t":
			[self._do_element(e) for e in list(element)]
		if element.tag == "xref":
			if not element.text:
				#self.o.write(self.p.sections[element.get("target")].replace(" ", "~") + "~\\ref{" + element.get("target") + "}") # Verbose style
				self.o.write("\\nameref{" + element.get("target") + "}") # Cleaner, better
			else:
				self.o.write(element.text)
		if element.tag == "list":
			style = self._list_styles[element.get("style", "symbols")]
			
			self.o.write("\\begin{" + style + "}\n")
			for point in list(element):
				text = self._escape(reduce(lambda u, v: u+v, [f for f in point.itertext()]))
				if style == "description":
					self.o.write("\\item[" + self._escape(point.get("hangText")) + "] ")
				else:
					self.o.write("\\item ")
				self.o.write(text + "\n")
			self.o.write("\\end{" + style + "}\n")
		if element.tag == "figure":
			self.o.write("\\begin{verbatim}\n")
			self.o.write(element.find("artwork").text)
			self.o.write("\\end{verbatim}\n")
		if element.tag == "texttable":
			columns = element.findall("ttcol")
			cc = len(columns)

			self.o.write("\\begin{tabular}{|" + "|".join( [self._alignments[e.get("align", "center")] for e in columns] ) + "|}\n\hline\n")
			self.o.write(" & ".join( [self._escape(e.text) for e in columns]) + "\\tabularnewline\n\hline\n\hline\n")

			cells = element.findall("c")
			i = 0
			for cell in cells:
				if i == cc:
					i = 0
					self.o.write("\\tabularnewline\n\\hline\n")
				self.o.write(self._escape(cell.text))
				i += 1
				if i < cc:
					self.o.write(" & ")

			self.o.write("\\tabularnewline\n\\cline{1-%d}\n" % cc)
			self.o.write("\\end{tabular}\n")
		if element.tag != "t" and element.tail:
			self.o.write(self._escape(element.tail))

		self.o.write("\n")

class MDOutput(Output):
	extension = ".md"

	def __init__(self):
		self.o = StringIO()

	def _trim(self, docstring):
		if not docstring:
			return ''
		# Convert tabs to spaces (following the normal Python rules)
		# and split into a list of lines:
		lines = docstring.expandtabs().splitlines()
		# Determine minimum indentation (first line doesn't count):
		indent = sys.maxint
		for line in lines[1:]:
			stripped = line.lstrip()
			if stripped:
				indent = min(indent, len(line) - len(stripped))
		# Remove indentation (first line is special):
		trimmed = [lines[0].strip()]
		if indent < sys.maxint:
			for line in lines[1:]:
				trimmed.append(line[indent:].rstrip())
		# Strip off trailing and leading blank lines:
		while trimmed and not trimmed[-1]:
			trimmed.pop()
		while trimmed and not trimmed[0]:
			trimmed.pop(0)
		# Return a single string:
		return '\n'.join(trimmed)

	def _escape(self, text):
		if type(text).__name__ == "dict":
			for key, item in text.items():
				text[key] = self._escape(item)
		if type(text).__name__ == "list":
			for i, item in enumerate(text):
				text[i] = self._escape(item)
		if type(text).__name__ == "str" or type(text).__name__ == "unicode":
			text = self._trim(escape(text))
		return text

	def getvalue(self):
		return self.o.getvalue()

	def Metadata(self, data):
		data = self._escape(data)
		at = unicode()
		for author in data["authors"]:
			at += "- [%(fullname)s](%(uri)s) - %(email)s" % author
		data["authors"] = at

		self.o.write("""# %(rfc)s - %(title)s
**%(area)s** - Workgroup: %(workgroup)s

Authors

%(authors)s

*%(abstract)s*
""" % data)

	def AppendSection(self, title, text, level, anchor):
		self.o.write("#" * (level+2) + " " + self._escape(title) + "\n")
		
		for element in list(text):
			self._do_element(element)

	def _do_element(self, element):
		if element.tag == "t" and element.text:
			self.o.write(self._escape(element.text) + "\n")
		if element.tag == "t":
			[self._do_element(e) for e in list(element)]
		if element.tag == "xref":
			self.o.write("[%s](http://www.ietf.org/rfc/%s.txt)" % (element.text, element.get("target").lower()))
		if element.tag == "list":
			style = "- "
			if element.get("style") == "numbers":
				style = "1. "
			for point in list(element):
				text = self._escape(reduce(lambda u, v: u+v, [f for f in point.itertext()]))
				if element.get("style") == "hanging":
					self.o.write(style + "**%s** %s\n" % (self._escape(point.get("hangText")), text))
				else:
					self.o.write(style + text + "\n")
		if element.tag == "figure":
			for line in element.find("artwork").text.splitlines():
				if len(line):
					self.o.write("`" + line + "`\n\n")
		if element.tag == "texttable":
			columns = element.findall("ttcol")
			cc = len(columns)

			self.o.write("<table>\n")
			self.o.write("\t<tr>\n")
			self.o.write("\n".join( ["\t\t<th>%s</th>" % self._escape(e.text) for e in columns]))
			self.o.write("\n\t</tr>\n")

			cells = element.findall("c")
			i = 0
			self.o.write("\t<tr>\n")
			for cell in cells:
				if i == cc:
					i = 0
					self.o.write("\t</tr>\n\t<tr>\n")
				self.o.write("\t\t<td>%s</td>\n" % self._escape(cell.text))
				i += 1

			self.o.write("\t</tr>\n")
			self.o.write("</table>\n")
		if element.tag != "t" and element.tail:
			self.o.write(self._escape(element.tail))

		self.o.write("\n")


class RFCParser():
	def __init__(self, dom, output):
		self.o = output(self)

		self.root = dom
		self.title = self.root.find("front")
		self.middle = self.root.find("middle")
		self.back = self.root.find("back")

		self.sections = dict()

	def run(self):
		self.o.Metadata(self.collect_metadata())
		self.walk()

	def _checked_text(self, e):
		if e == None:
			return ""
		else:
			return e.text

	def parse_text(self, elements):
		return reduce(lambda u, v: u+v, [e.text for e in elements])

	def collect_metadata(self):
		md = dict()
		md["title"] = self.title.find("title").text
		authors = list()
		for author in self.title.findall("author"):
			authors.append({
				"fullname": author.get("fullname"),
				"organization": self._checked_text(author.find("organization")),
				"email": self._checked_text(author.find("address/email")),
				"uri": self._checked_text(author.find("address/uri")),
			})
		md["authors"] = authors
		md["date"] = "%s %s" % (self.title.find("date").get("month"), self.title.find("date").get("year"))
		md["area"]  = self.title.find("area").text
		md["workgroup"] = self.title.find("workgroup").text
		md["abstract"] = self.parse_text(self.title.find("abstract").findall("t"))
		md["rfc"] = "RFC X" + self.root.get("number", "")

		def _findsec(element):
			if element.get("anchor", None):
				self.sections[element.get("anchor")] = element.get("title")
			[_findsec(section) for section in element.findall("section")]
		[_findsec(section) for section in self.middle.findall("section")]

		return md

	def handle_section(self, element, level):
		self.o.AppendSection(element.get("title"), element, level, element.get("anchor", None))

		[self.handle_section(section, level+1) for section in element.findall("section")]

	def walk(self):
		for section in self.middle.findall("section"):
			self.handle_section(section, 0)

def main():
	parser = argparse.ArgumentParser(description="Tool to convert RFC XML to various output formats")
	parser.add_argument("-f", "--format", default="markdown", help="Output format. Either markdown or latex.")
	parser.add_argument("-c", "--compile", action="store_const", const=True, default=False, help="Compile the resulting document, if possible.")
	parser.add_argument("-t", "--title", action="store_const", const=True, default=False, help="Print title of document and exit.")
	parser.add_argument("file", help="Input XML", nargs="*")

	args = parser.parse_args()
	
	output_modules = {
		"markdown": MDOutput,
		"latex": TeXOutput,
	}

	for infile in args.file:
		if not args.title:
			print "Processing %s..." % infile

		output = output_modules[args.format]
		rfcp = RFCParser(ElementTree.fromstring(open(infile).read()), output)

		if args.title:
			print rfcp.collect_metadata()["rfc"] + rfcp.collect_metadata()["title"]
			return 0

		rfcp.run()
		
		basename, ext = os.path.splitext(infile)
		outfile = basename + output.extension
		with open(outfile, "w+") as f:
			f.write(rfcp.o.getvalue())

		if args.compile:
			rfcp.o.Compile(outfile)

def get_title(file):
	rfcp = RFCParser(ElementTree.fromstring(open(file).read()), Output())
	return "%s %s" % (rfcp.collect_metadata()["rfc"], rfcp.collect_metadata()["title"])

if __name__ == "__main__":
	sys.exit(main())