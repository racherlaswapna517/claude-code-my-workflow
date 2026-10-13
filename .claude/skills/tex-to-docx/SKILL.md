---
name: tex-to-docx
description: Convert a LaTeX manuscript (`.tex`) to a Word `.docx` that keeps the PDF's look - Times New Roman 12 pt, 1.5 spacing, numbered headings, native editable equations, figures, tables, numbered citations and page numbers - using pandoc with a custom reference template. Use when a co-author, journal or reviewer needs a Word version of a paper, or when a plain `pandoc`/`tex2docx` conversion came out in the wrong fonts with moved or broken figures. Not for slides or PDF builds.
argument-hint: "<path/to/paper.tex> [output.docx] [--reference-only] [--dry-run] [--overwrite]"
allowed-tools: ["Read", "Write", "Glob", "Grep", "Bash"]
disable-model-invocation: true
---

# TeX to DOCX

Turn a LaTeX paper into a Word file a collaborator can edit, without the damage a bare `pandoc paper.tex -o paper.docx` does (default sans-serif template, `\paragraph` headings as separate lines, unresolved citation keys, custom math macros left as text).

## When to use

- A co-author, journal or reviewer asks for Word, or wants tracked changes.
- A previous conversion lost the fonts, headings, numbering or figures.

Slides go through [`/translate-to-quarto`](../translate-to-quarto/SKILL.md); PDF builds through [`/compile-latex`](../compile-latex/SKILL.md).

## Goal and deliverable

`<paper>.docx` beside the `.tex` (or at the path given), in which:

- the text is Times New Roman 12 pt with 1.5 line spacing, US Letter, 1-inch margins, justified with automatic hyphenation (Word does not hyphenate unless told to; justified text looks gappy without it);
- headings are numbered and sized like the LaTeX `article` class (17.3 / 14.4 / 12 pt, bold, upright);
- every equation is a native Word equation, not an image;
- figures are embedded inline at 6 inches wide, captions read "Fig. N." and "Table N.";
- citations are numbered `[4, 5]` in bibliography order and the reference list is numbered;
- a page-number footer is present.

## How it works

The scripts live in `scripts/` beside this file and are driven by `build_docx.py`:

1. `make_reference.py` builds the pandoc reference template from pandoc's own default (fonts, spacing, heading sizes, table grid, footer, hyphenation).
2. `preprocess.py` writes a cleaned copy of the `.tex` plus a metadata file (title, authors with affiliations, abstract): citations become numbers, `\DeclareMathOperator` macros are expanded, `\paragraph`/`\subparagraph` become bold run-in text, captions are numbered, the table column spec is simplified to `p{..\textwidth}` widths, and the bibliography becomes a numbered list. The original `.tex` is never modified.
3. pandoc converts the cleaned copy with the template and `--number-sections`.
4. `verify_docx.py` checks the result structurally.

Run it with `python3 ${CLAUDE_SKILL_DIR}/scripts/build_docx.py <paper.tex> [out.docx]`.

## Constraints, and why

- **Convert a copy, never the source.** The `.tex` is authoritative; the `.docx` is a derived deliverable ([`repo-hygiene.md`](../../rules/repo-hygiene.md): scratch must not become main).
- **Do not overwrite an existing `.docx` silently.** Collaborators may have edited it. The script stops unless `--overwrite` is passed.
- **Never claim a visual check.** Nothing here renders the file in Word. The report says "not viewed in Word" and lists the structural facts (images, table shape, equation count). If the user needs certainty, they open it in Word and look at the equation and table pages.
- **Say what Word cannot reproduce.** Page breaks, float placement and exact equation spacing differ from the PDF; do not promise page-for-page fidelity.
- **Supported LaTeX subset.** A `thebibliography` block (not BibTeX files), `\cite`, `\section` to `\subsubsection`, `\paragraph`, `itemize`/`enumerate`, `equation` and `cases`, `figure` with `\includegraphics`, a `table` with a `tabular` using `p{..\textwidth}` columns, and the `\title`/`\author`/`abstract` block. Anything else is passed to pandoc as is, so check the report for warnings.
- **Do not install tools without asking.** pandoc is required; if it is missing, say so and stop.

## How to verify it is done

The script exits 0 only if `verify_docx.py` finds: every embedded image present in the package, no backslash left in body text, no raw LaTeX in equations, and a footer reference. Compare the census with the source: figure count, table rows and columns, and the number of equations. A drop in any of them means a construct was not converted.

## Output / report format

Report: the output path, the census line (images with sizes, table shape, equations, headings, list items), any pandoc warnings verbatim, and the sentence "Not viewed in Word". With `--dry-run` report the census of a temporary build and state that nothing was written.

## Exit behavior

- **Success:** exit 0, the file written, the census reported.
- **Output exists, no `--overwrite`:** stop with the path named; write nothing.
- **pandoc missing or fails:** stop with its message; write nothing.
- **Verification problem:** the file is written, the problem is reported first, exit 1. Do not describe the file as ready.

## Flags

- `--reference-only` - build only the Word template (`reference.docx`) so it can be reused or inspected; converts nothing.
- `--dry-run` - convert to a temporary file, run the structural check, write nothing to the output path.
- `--overwrite` - replace an existing output file.

## Cross-references

- [`/compile-latex`](../compile-latex/SKILL.md) - build the PDF this conversion is meant to resemble.
- [`/translate-to-quarto`](../translate-to-quarto/SKILL.md) - the slide-deck equivalent for Beamer.
- [`/verify-artifact`](../verify-artifact/SKILL.md) - before sending the `.docx` to a co-author or journal, prove it is the file you mean.
- [`repo-hygiene.md`](../../rules/repo-hygiene.md) - where generated files may live.

## What this skill does NOT do

- **Edit or fix the `.tex`.** Source problems (a missing bibliography entry, an undefined macro) are reported, not repaired.
- **Render or visually verify in Word.** It checks structure only.
- **Convert slides or BibTeX-based papers.** Beamer goes to Quarto; a paper that cites through `.bib` files needs its bibliography resolved first.
- **Commit or send anything.** Committing is [`/commit`](../commit/SKILL.md); sending is the user's call.
