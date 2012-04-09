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
from xml.etree import ElementTree
#XMLParser, TreeBuilder
import datetime

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
		print data

	def AppendSection(self, title, text, level):
		# title
		# nachor (optional)
		# text
		# level = int
		#	0 = section
		#	1 = subsection
		#	2 = subsubsection
		print title, level
		print text

class TeXOutput(Output):
	pass

class MDOutput(Output):
	def __init__(self):
		self.o = StringIO()

	def getvalue(self):
		return self.o.getvalue()

	def Metadata(self, data):
		at = unicode()
		for author in data["authors"]:
			at += "- [%(fullname)s](%(uri)s) - %(email)s" % author
		data["authors"] = at

		self.o.write("""# %(title)s
**%(area)s** - Workgroup: %(workgroup)s

Authors

%(authors)s

*%(abstract)s*
""" % data)

	def AppendSection(self, title, text, level):
		self.o.write("#" * (level+2) + " " + title + "\n")
		
		for element in list(text):
			if element.tag == "section":
				continue

			print element.tag
			if element.tag == "t" and element.text:
				self.o.write(element.text + "\n")
			if element.tag == "list":
				style = "- "
				if element.get("style") == "numbers":
					style = "1. "
				for point in list(element):
					self.o.write(style + point.text + "\n")
			if element.tag == "texttable":
				self.o.write("(Here would be a table, but markdown doesn't support tables. Sorry!\n")

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

	def parse_text(self, elements):
		return reduce(lambda u, v: u+v, [e.text for e in elements])

	def collect_metadata(self):
		md = dict()
		md["title"] = self.title.find("title").text
		authors = list()
		for author in self.title.findall("author"):
			authors.append({
				"fullname": author.get("fullname"),
				"organization": author.find("organization").text,
				"email": author.find("address/email").text,
				"uri": author.find("address/uri").text
			})
		md["authors"] = authors
		#md["date"] = datetime.now()
		md["area"]  = self.title.find("area").text
		md["workgroup"] = self.title.find("workgroup").text
		md["abstract"] = self.parse_text(self.title.find("abstract").findall("t"))
		return md

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

	output = MDOutput()

	rfcp = RFCParser(ElementTree.fromstring(open(args.file).read()), output)
	print output.getvalue()

