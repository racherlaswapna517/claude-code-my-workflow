#!/usr/bin/env python3
"""Structural check of a converted .docx (no third-party packages).

usage: verify_docx.py OUT.docx
Prints a census and exits 1 on a structural problem. It does not render the file.
"""
import re, sys, zipfile

z = zipfile.ZipFile(sys.argv[1])
doc = z.read('word/document.xml').decode('utf8')
rels = z.read('word/_rels/document.xml.rels').decode('utf8')
names = set(z.namelist())
problems = []

targets = dict(re.findall(r'<Relationship [^>]*?Id="([^"]+)"[^>]*?Target="([^"]+)"', rels))
targets.update({a: b for b, a in re.findall(r'<Relationship [^>]*?Target="([^"]+)"[^>]*?Id="([^"]+)"', rels)})
embeds = re.findall(r'<a:blip [^>]*r:embed="([^"]+)"', doc)
for rid in embeds:
    t = 'word/' + targets.get(rid, '?')
    if t not in names:
        problems.append('image %s -> %s missing from the package' % (rid, t))
sizes = [(int(a) / 914400, int(b) / 914400) for a, b in re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', doc)]
tables = re.findall(r'<w:tbl>.*?</w:tbl>', doc, flags=re.S)
text = re.sub(r'<[^>]+>', '', doc)
math = doc.count('<m:oMath>')
math_text = ' '.join(re.findall(r'<m:t[^>]*>([^<]*)</m:t>', doc))
if '\\' in text:
    problems.append('backslash left in body text: %r' % re.findall(r'.{20}\\.{20}', text)[:3])
if re.search(r'\\|operatorname', math_text):
    problems.append('raw LaTeX left in equations')
if 'footerReference' not in doc:
    problems.append('no footer reference (page numbers)')
print('images: %d %s' % (len(embeds), ['%.1fx%.1f in' % s for s in sizes]))
for t in tables:
    rows = re.findall(r'<w:tr[ >]', t)
    print('table: %d rows x %d cols' % (len(rows), len(re.findall(r'<w:gridCol', t))))
print('equations: %d | headings: %d | list items: %d' % (math, len(re.findall(r'w:val="Heading\d"', doc)), doc.count('<w:numPr>')))
print('NOT viewed in Word: this is a structural check, not a render.')
for p in problems:
    print('PROBLEM:', p)
sys.exit(1 if problems else 0)
