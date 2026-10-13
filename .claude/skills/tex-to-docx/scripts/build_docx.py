#!/usr/bin/env python3
"""Convert a LaTeX paper to .docx via pandoc, keeping the PDF's look.

usage: build_docx.py PAPER.tex [OUT.docx] [--reference-only] [--dry-run] [--overwrite]
"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
flags = {a for a in sys.argv[1:] if a.startswith('--')}
if not args or flags - {'--reference-only', '--dry-run', '--overwrite'}:
    sys.exit(__doc__)
pandoc = shutil.which('pandoc') or '/usr/local/bin/pandoc'
if not os.path.exists(pandoc):
    sys.exit('pandoc not found (brew install pandoc)')
tex = os.path.abspath(args[0])
out = os.path.abspath(args[1]) if len(args) > 1 else os.path.splitext(tex)[0] + '.docx'
work = tempfile.mkdtemp(prefix='tex2docx-')
ref = os.path.join(work, 'reference.docx')

if '--reference-only' in flags:
    ref_out = out if args[1:] else os.path.join(os.path.dirname(tex), 'reference.docx')
    subprocess.run([sys.executable, os.path.join(HERE, 'make_reference.py'), ref_out, pandoc], check=True)
    sys.exit(0)

if os.path.exists(out) and '--overwrite' not in flags and '--dry-run' not in flags:
    sys.exit('%s exists; pass --overwrite or choose another name' % out)

subprocess.run([sys.executable, os.path.join(HERE, 'make_reference.py'), ref, pandoc], check=True)
clean, meta = os.path.join(work, 'clean.tex'), os.path.join(work, 'meta.yaml')
subprocess.run([sys.executable, os.path.join(HERE, 'preprocess.py'), tex, clean, meta], check=True)
target = os.path.join(work, 'out.docx') if '--dry-run' in flags else out
cmd = [pandoc, clean, '-f', 'latex', '-t', 'docx', '--reference-doc=' + ref, '--number-sections',
       '--metadata-file=' + meta, '--resource-path=' + os.path.dirname(tex), '-o', target]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.stderr.strip():
    print('pandoc warnings:\n' + r.stderr)
if r.returncode:
    sys.exit('pandoc failed (exit %d)' % r.returncode)
v = subprocess.run([sys.executable, os.path.join(HERE, 'verify_docx.py'), target])
print(('dry run, nothing written (checked a temporary build): ' if '--dry-run' in flags else 'wrote ') + (out if '--dry-run' not in flags else ''))
shutil.rmtree(work, ignore_errors=True)
sys.exit(v.returncode)
