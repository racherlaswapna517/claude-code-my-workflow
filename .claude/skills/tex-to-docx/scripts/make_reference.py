#!/usr/bin/env python3
"""Build the Times New Roman 12 pt / 1.5-spacing pandoc reference.docx.

usage: make_reference.py OUT_REFERENCE.docx [PANDOC]
"""
import os, re, shutil, subprocess, sys, tempfile, zipfile

out = os.path.abspath(sys.argv[1])
pandoc = sys.argv[2] if len(sys.argv) > 2 else 'pandoc'
work = tempfile.mkdtemp(prefix='ref-')
base = os.path.join(work, 'ref0.docx')
with open(base, 'wb') as fh:
    fh.write(subprocess.run([pandoc, '--print-default-data-file', 'reference.docx'], check=True, capture_output=True).stdout)
x = os.path.join(work, 'x')
with zipfile.ZipFile(base) as z:
    z.extractall(x)


def rd(p):
    return open(os.path.join(x, p), encoding='utf8').read()


def wr(p, t):
    os.makedirs(os.path.dirname(os.path.join(x, p)), exist_ok=True)
    open(os.path.join(x, p), 'w', encoding='utf8').write(t)


TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman" />'
s = rd('word/styles.xml')
s = re.sub(r'(<w:docDefaults>.*?<w:rPr>)\s*<w:rFonts [^>]*/>', r'\1' + TNR, s, count=1, flags=re.S)
s = re.sub(r'<w:pPrDefault>.*?</w:pPrDefault>',
           '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto" /></w:pPr></w:pPrDefault>', s, flags=re.S)


def style(sid, ppr=None, rpr=None):
    global s
    m = re.search(r'(<w:style [^>]*w:styleId="%s".*?)</w:style>' % sid, s, flags=re.S)
    b = m.group(1)
    if ppr is not None:
        b = re.sub(r'<w:pPr\s*/>|<w:pPr>.*?</w:pPr>', '', b, flags=re.S) + '<w:pPr>%s</w:pPr>' % ppr
    if rpr is not None:
        b = re.sub(r'<w:rPr\s*/>|<w:rPr>.*?</w:rPr>', '', b, flags=re.S) + '<w:rPr>%s</w:rPr>' % rpr
    s = s[:m.start()] + b + '</w:style>' + s[m.end():]


style('BodyText', '<w:spacing w:before="0" w:after="120" /><w:jc w:val="both" />')
style('Compact', '<w:spacing w:before="0" w:after="60" /><w:jc w:val="both" />')
style('Title', '<w:keepNext /><w:spacing w:before="0" w:after="240" w:line="240" w:lineRule="auto" /><w:jc w:val="center" />',
      TNR + '<w:b /><w:bCs /><w:sz w:val="32" /><w:szCs w:val="32" />')
style('Author', '<w:keepNext /><w:keepLines /><w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto" /><w:jc w:val="center" />',
      TNR + '<w:b w:val="0" /><w:bCs w:val="0" /><w:sz w:val="24" /><w:szCs w:val="24" />')
style('AbstractTitle', '<w:keepNext /><w:keepLines /><w:spacing w:before="360" w:after="60" /><w:jc w:val="center" />',
      '<w:b /><w:sz w:val="24" /><w:szCs w:val="24" />')
style('Abstract', '<w:spacing w:before="60" w:after="120" /><w:jc w:val="both" />', '<w:sz w:val="24" /><w:szCs w:val="24" />')
# LaTeX article sizes at 12 pt: section 17.28, subsection 14.4, subsubsection 12 (all bold, upright)
for sid, sz, tab, before, after in (('Heading1', 34, 500, 360, 120), ('Heading2', 29, 640, 240, 120),
                                    ('Heading3', 24, 780, 200, 100), ('Heading4', 24, 780, 160, 80)):
    style(sid, '<w:keepNext /><w:keepLines /><w:tabs><w:tab w:val="left" w:pos="%d" /></w:tabs>'
               '<w:spacing w:before="%d" w:after="%d" /><w:outlineLvl w:val="%d" />' % (tab, before, after, int(sid[-1]) - 1),
          TNR + '<w:b /><w:bCs /><w:color w:val="000000" /><w:sz w:val="%d" /><w:szCs w:val="%d" />' % (sz, sz))
style('Caption', '<w:spacing w:before="60" w:after="200" /><w:jc w:val="center" />', '<w:i w:val="0" /><w:iCs w:val="0" />')
m = re.search(r'<w:style [^>]*w:styleId="Table".*?</w:style>', s, flags=re.S)
tbl = m.group(0)
bd = ''.join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="000000" />' % k for k in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
tbl = tbl.replace('<w:tblInd w:w="0" w:type="dxa" />', '<w:tblInd w:w="0" w:type="dxa" /><w:tblBorders>%s</w:tblBorders>' % bd)
tbl = re.sub(r'<w:tblStylePr w:type="firstRow">.*?</w:tblStylePr>',
             '<w:tblStylePr w:type="firstRow"><w:rPr><w:b /></w:rPr><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="D9D9D9" /></w:tcPr></w:tblStylePr>',
             tbl, flags=re.S)
s = s[:m.start()] + tbl + s[m.end():]
wr('word/styles.xml', s)

# Word does not hyphenate unless told to; LaTeX does, and justified text looks gappy without it
wr('word/settings.xml', rd('word/settings.xml').replace(
    '<w:defaultTabStop w:val="720" />',
    '<w:defaultTabStop w:val="720" /><w:autoHyphenation /><w:consecutiveHyphenLimit w:val="2" />'))

# page number footer, US Letter, 1-inch margins
wr('word/footer1.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
wr('word/document.xml', re.sub(
    r'<w:sectPr>.*?</w:sectPr>',
    '<w:sectPr><w:footerReference w:type="default" r:id="rId40" /><w:footnotePr><w:numRestart w:val="eachSect" /></w:footnotePr>'
    '<w:pgSz w:w="12240" w:h="15840" /><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0" /></w:sectPr>',
    rd('word/document.xml'), flags=re.S))
wr('word/_rels/document.xml.rels', rd('word/_rels/document.xml.rels').replace(
    '</Relationships>',
    '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Id="rId40" Target="footer1.xml" /></Relationships>'))
wr('[Content_Types].xml', rd('[Content_Types].xml').replace(
    '</Types>',
    '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml" /></Types>'))

if os.path.exists(out):
    os.remove(out)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(x, '[Content_Types].xml'), '[Content_Types].xml')
    for root, _, files in os.walk(x):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, x)
            if arc != '[Content_Types].xml':
                z.write(full, arc)
shutil.rmtree(work)
print('reference template written:', out)
