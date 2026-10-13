#!/usr/bin/env python3
"""Prepare a LaTeX paper for pandoc: write a cleaned copy plus the front matter pandoc needs.

usage: preprocess.py PAPER.tex CLEAN.tex META.yaml
Handles the subset documented in ../SKILL.md. Prints a one-line census.
"""
import re, sys


def strip_comments(t):
    return '\n'.join(re.split(r'(?<!\\)%', l)[0] for l in t.split('\n'))


def braced(s, i):
    """s[i] == '{'; return (content, index after the matching '}')."""
    d = 0
    for j in range(i, len(s)):
        if s[j] == '{' and s[j - 1] != '\\':
            d += 1
        elif s[j] == '}' and s[j - 1] != '\\':
            d -= 1
            if d == 0:
                return s[i + 1:j], j + 1
    raise ValueError('unbalanced braces')


def clean_inline(s):
    s = s.replace('\\ ', ' ').replace('\\\\', '\n')
    return re.sub(r'\s+', ' ', s).strip()


def front_matter(raw):
    title = clean_inline(re.search(r'\\title\{((?:[^{}]|\{[^{}]*\})*)\}', raw).group(1))
    authors = []
    m = re.search(r'\\author\{', raw)
    if m:
        block, _ = braced(raw, m.end() - 1)
        for a in re.split(r'\\and', block):
            a = re.sub(r'\\begin\{tabular\}(\[[^\]]*\])?\{[^}]*\}|\\end\{tabular\}', '', a)
            lines = [clean_inline(l) for l in a.split('\\\\') if clean_inline(l)]
            if lines:
                authors.append(lines)
    ab = re.search(r'\\begin\{abstract\}(?:\\normalsize)?(.*?)\\end\{abstract\}', raw, flags=re.S)
    kw = re.search(r'\\noindent\\textbf\{Keywords[-—]*\}([^\n]*)', raw)
    return title, authors, ab.group(1).strip() if ab else '', kw.group(1).strip() if kw else ''


def macros(preamble):
    """\\DeclareMathOperator{\\name}{text} -> replacement table."""
    out = []
    for m in re.finditer(r'\\DeclareMathOperator(\*?)\{\\(\w+)\}\{([^}]*)\}', preamble):
        star, name, text = m.groups()
        out.append((name, r'\operatorname%s{%s}' % ('*' if star else '', text)))
    return out


def main(src, dst, meta):
    raw = strip_comments(open(src, encoding='utf8').read())
    pre, rest = raw.split(r'\begin{document}', 1)
    body = rest[:rest.index(r'\end{document}')]
    title, authors, abstract, kw = front_matter(raw)

    bib_start = body.index(r'\begin{thebibliography}')
    bib = body[bib_start:body.index(r'\end{thebibliography}')]
    keys = re.findall(r'\\bibitem\{([^}]+)\}', bib)
    idx = {k: i + 1 for i, k in enumerate(keys)}
    main_txt = body[body.index(r'\section{'):bib_start]

    def cite(m):
        return '[' + ', '.join(str(idx[k.strip()]) for k in m.group(1).split(',')) + ']'
    main_txt = re.sub(r'\\cite\{([^}]+)\}', cite, main_txt)

    main_txt = re.sub(r'\\subparagraph\{([^}]*)\}', r'\\textbf{\\textit{\1}}', main_txt)
    main_txt = re.sub(r'\\paragraph\{((?:[^{}]|\{[^{}]*\})*)\}', r'\\textbf{\1}', main_txt)
    for name, text in macros(pre) + [('displaystyle', '')]:
        main_txt = re.sub(r'\\%s(?![A-Za-z])' % name, lambda m, t=text: t, main_txt)

    fig, tab = [0], [0]

    def cap(kind, counter, label):
        def f(m):
            counter[0] += 1
            return r'\caption{%s %d. %s}' % (label, counter[0], m.group(1)) + '\n\\label'
        return f
    parts = re.split(r'(\\begin\{(?:figure|table)\}.*?\\end\{(?:figure|table)\})', main_txt, flags=re.S)
    for i, p in enumerate(parts):
        if p.startswith(r'\begin{figure}'):
            parts[i] = re.sub(r'\\caption\{(.*?)\}\s*\\label', cap('fig', fig, 'Fig.'), p, flags=re.S)
        elif p.startswith(r'\begin{table}'):
            p = re.sub(r'\\caption\{(.*?)\}\s*\\label', cap('tab', tab, 'Table'), p, flags=re.S)
            spec = re.search(r'\\begin\{tabular\}\{(.*?)\}\s*\\toprule', p, flags=re.S)
            if spec:
                widths = re.findall(r'p\{([\d.]+)\\textwidth\}', spec.group(1))
                if widths:
                    new = ''.join(r'p{%s\textwidth}' % w for w in widths)
                    p = p[:spec.start()] + r'\begin{tabular}{%s}' % new + '\n\\toprule' + p[spec.end():]
            for junk in (r'\renewcommand{\arraystretch}{1.3}', r'\small', r'\footnotesize', r'\normalsize'):
                p = p.replace(junk, '')
            parts[i] = p
    main_txt = ''.join(parts)
    main_txt = re.sub(r'width=[\d.]+\\(?:text|line)width', 'width=6in', main_txt)

    refs = re.findall(r'\\bibitem\{[^}]+\}\s*(.*?)(?=\\bibitem|\Z)', bib, flags=re.S)
    refs_tex = '\\section*{References}\n\n' + '\n\n'.join('[%d]~%s' % (i + 1, r.strip()) for i, r in enumerate(refs)) + '\n'
    refs_tex = refs_tex.replace(r'\url{', r'\texttt{')

    kw_tex = ('\\noindent\\textbf{Keywords---} %s\n\n' % kw) if kw else ''
    open(dst, 'w', encoding='utf8').write(
        '\\documentclass{article}\n\\usepackage{amsmath,amssymb,graphicx,booktabs}\n\\begin{document}\n'
        + kw_tex + main_txt + '\n' + refs_tex + '\n\\end{document}\n')

    y = 'title: %s\n' % repr(title)
    if authors:
        y += 'author:\n'
        for a in authors:
            y += '  - |\n' + ''.join('    %s%s\n' % (l, '\\' if k < len(a) - 1 else '') for k, l in enumerate(a))
    if abstract:
        y += 'abstract: |\n' + '\n'.join('  ' + l for l in abstract.split('\n')) + '\n'
    open(meta, 'w', encoding='utf8').write(y)
    print('figs %d, tables %d, refs %d, authors %d' % (fig[0], tab[0], len(refs), len(authors)))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
