# Reimbursement Manager — Handoff Notes

Personal reimbursement-tracking system for **Pearson v. Pearson, No. 236951** (Family Court, EBR Parish).
Reads bills from a folder, categorizes them, computes what Lindsey owes, and publishes a
shareable web portal + printable documents. Repo: https://github.com/nedpearson/Reimbursements

## Current state (2026-07-23, commit 25bd52c)
- **Main claim (net): $89,114.84** — what Lindsey owes. Ledger = workbook = portal = statement, penny-exact.
- **Voluntary support (separate): $58,248.92** — Yukon loan + GEICO + health, shown as generosity, not part of the claim.
- Live portal: https://nedpearson.github.io/Reimbursements/  (GitHub Pages from `docs/`, served with `.nojekyll`).

## How to run
- Requires **Python 3.14** (on Ned's PC) with `pip install -r requirements.txt` (pymupdf, openpyxl, reportlab).
- **Start.bat** — opens the desktop app (`app.pyw`). It finds the working python's `pythonw` sibling to avoid the broken Windows Store stub.
- **Publish to Web.bat** — rebuilds everything (`build_portal.py`) and `git push`es. Tags a `restore-point` first.
- **Undo Last Publish.bat** — rolls the live page back to the last restore point.
- **Email Packet.bat** — zips all deliverables and opens a pre-filled email.

## Architecture (module roles)
- **categorize.py** — the engine. `build()` walks the bills folder + merges email/venmo data; `apply_split()` applies the per-category % (Decimal ROUND_HALF_UP); `generate()` writes ledger.csv/json, summary.txt, workbook, statement. `item_id()` = stable per-line id. Auto-snapshots via backup.py before each run.
- **extractors.py / parsers.py** — vendor-specific bill parsing (PDF text, OCR fallback, HTML-embedded PDFs).
- **email_bills.py** — bills found in Gmail not in the folder (hard-coded, deduped by month/invoice).
- **venmo_csv.py** — parses Venmo statement CSVs (private recipients suppressed).
- **report.py** — Excel workbook (formula-driven Settings tab). **report_pdf.py** — itemized statement PDF (grouped by vendor). **exports.py** — cover letter, proof pack, print package. **make_additional_pdf.py** — the "voluntary support" chart from additional.json.
- **build_portal.py** — rebuilds `docs/`: injects data into portal_template.html, builds proof volumes (real bills + generated source-record pages so every line links to a document), writes `.nojekyll`.
- **portal_template.html** — the single-page portal (drill-down, vendor grouping, per-line Dispute / "I paid this", Web3Forms upload center, mobile-optimized, professional design).
- **app.pyw** — desktop GUI (tabs: Generate & Export, Edit Amounts, Mark Paid, Add/Import, Archive/Backups, Settings).
- **backup.py** — auto-snapshot + Archive/restore (snapshots in `archive/`, local only).
- **safewrite.py** — every output writes to a temp file then swaps in; a locked file keeps the prior version instead of crashing.

## Editable data files (JSON; edit in the app or by hand, then Generate + Publish)
- **config.json** — split percentages, date cutoff, manual_entries (mortgage schedule, labor, Hager Painting $600, etc.), `web3forms_key`.
- **additional.json** — the voluntary-support sections + court framing.
- **disputes.json** — Lindsey's disputes + Ned's responses/status.
- **settled.json** — per-line paid / proof-pending ids (drives green PAID + balance).
- **paidback.json** — legacy lump-payment log.

## Split percentages (config.json)
Household/utilities/mortgage/pool/etc. 50% · School & Medical 12% (court-ordered, 11.34% income share) ·
Moving 80% · Advances to Lindsey 100% · AT&T Business flat $100/mo.

## Open items / TODO
- **Web3Forms key** — paste a free key (web3forms.com) into app Settings to turn on real on-page file uploads (currently shows a setup note + email fallback).
- Ned to drop actual photos into `House Bills\Misc\`: Hager Painting invoice (as `HagerPainting_Inv811012_June2026.jpg`), Kids A/C docs, returned-check + Chase withdrawal slips — each then upgrades from a source record to the real bill exhibit.
- Real GEICO/NFP statements for Aug 2024–Sep 2025 (those months currently at the documented monthly rate).
- Entergy Aug–Nov 2024 + pre-2025 water months (portal logins). Fernando pool inv #3435 amount.
- Attorney sign-off on the "voluntary support" framing language.

## Safety
- Every Generate auto-saves a data snapshot to `archive/` (restore from the app's Archive tab).
- Every Publish saves a git `restore-point` tag; `Undo Last Publish.bat` reverts the live page.
- `archive/`, `output/`, `.deps_installed`, `__pycache__/` are gitignored (local only).

## Notes for whoever finishes in Antigravity
- Bills source folder on Ned's PC: `C:\Users\nedpe\Desktop\House Bills` (set as `last_folder` in config.json).
- The portal is a static site — file uploads need the Web3Forms backend (or swap in another form handler).
- Never expose the private Venmo recipients or include Jaclyn in any output (both are deliberately suppressed).
- Two project docs (in the attached Claude project) carry the full history: `reimbursement-summary.md` and `reimbursement-portal.md`.
