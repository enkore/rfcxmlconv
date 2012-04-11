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
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from cStringIO import StringIO

class Output():
	def __init__(self):
		pass

	def getvalue(self):
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
		#	date = date()
		#	area
		#	workgroup
		#	abstract
		pass

	def AppendSection(self, title, text, level):
		# title
		# nachor (optional)
		# text
		# level = int
		#	0 = section
		#	1 = subsection
		#	2 = subsubsection
		pass

class TeXOutput(Output):
	extension = ".tex"
	_section_labels = ["section", "subsection", "subsubsection", "subsubsubsection", "paragraph", "subparagraph"]
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

	def __init__(self):
		self.o = StringIO()

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
			text = re.sub(r"(#|&|\$|%|{|}|_)", r"\\\1", text)
			text = re.sub(r"\"([^\"]*)\"", r"\\enquote{\1}", text)
		return text

	def getvalue(self):
		return self.o.getvalue() + "\\end{document}"

	def Metadata(self, data):
		data = self._escape(data)

		at = unicode()
		data["authors"] = "\\and ".join([e["fullname"] for e in data["authors"]])

		preamble = open("preamble.tex").read() % data

		self.o.write(preamble)

	def AppendSection(self, title, text, level):
		title = self._escape(title)

		self.o.write("\\" + self._section_labels[level] + "{" + title + "}\n")

		[self._do_element(e) for e in list(text)]

	def _do_element(self, element):
		if element.tag == "t" and element.text:
			self.o.write(self._escape(element.text) + "\n")
			[self._do_element(e) for e in list(element)]
		if element.tag == "xref":
			self.o.write(element.text)
		if element.tag == "list":
			style = self._list_styles[element.get("style")]
			
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

			self.o.write("\\begin{tabular}{|" + "|".join( [self._alignments[e.get("align", "center")] for e in columns] ) + "|}\n")
			self.o.write("\\cline{1-%d}\n" % cc)
			self.o.write(" & ".join( [self._escape(e.text) for e in columns]) + "\\tabularnewline\n")
			self.o.write("\\cline{1-%d}\n" % cc)

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

	def AppendSection(self, title, text, level):
		self.o.write("#" * (level+2) + " " + self._escape(title) + "\n")
		
		for element in list(text):
			self._do_element(element)

	def _do_element(self, element):
		if element.tag == "t" and element.text:
			self.o.write(self._escape(element.text) + "\n")
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

		self.o.write("\n")


class RFCParser():
	def __init__(self, dom, output):
		self.o = output

		self.root = dom
		self.title = self.root.find("front")
		self.middle = self.root.find("middle")
		self.back = self.root.find("back")

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
		#md["date"] = datetime.now()
		md["area"]  = self.title.find("area").text
		md["workgroup"] = self.title.find("workgroup").text
		md["abstract"] = self.parse_text(self.title.find("abstract").findall("t"))
		md["rfc"] = "RFC X" + self.root.get("number", "")

		return self.o._escape(md)

	def handle_section(self, element, level):
		self.o.AppendSection(element.get("title"), element, level)

		for section in element.findall("section"):
			self.handle_section(section, level+1)

	def walk(self):
		for section in self.middle.findall("section"):
			self.handle_section(section, 0)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Tool to convert RFC XML to various output formats")
	parser.add_argument("-f", "--format", default="markdown", help="Output format. Either markdown or latex.")
	parser.add_argument("file", help="Input XML")

	args = parser.parse_args()

	output = Output()
	if args.format == "markdown":
		output = MDOutput()
	if args.format == "latex":
		output = TeXOutput()

	rfcp = RFCParser(ElementTree.fromstring(open(args.file).read()), output)
	
	basename, ext = os.path.splitext(args.file)
	with open(basename + output.extension, "w+") as f:
		f.write(output.getvalue())

