# Reimbursement Manager

Desktop program that tracks shared household & child-related expenses for the
Pearson v. Pearson reimbursement claim, auto-categorizes bills, and generates
the full document set to send to Lindsey.

## One-time setup
1. Install Python 3 (https://www.python.org/downloads/ — tick **Add Python to PATH**)
2. Double-click **install.bat** (installs dependencies + creates the desktop icon)

## Daily use
- Double-click the **Reimbursement Manager** icon on your desktop (or `Start.bat`).
- **Generate & Export** tab → *Generate All Documents* reads the bills folder
  (`C:\Users\nedpe\Desktop\House Bills`) and produces, in `output\`:
  - `Reimbursement_Breakdown.xlsx` — full workbook (Summary, dated Ledger, By-Month, Settings, Credits, Review, Missing Bills)
  - `Reimbursement_Statement.pdf` — itemized statement
  - `Reimbursement_Cover_Letter.pdf` — transmittal letter
  - `Reimbursement_Proof_Pack.pdf` — the actual bills, exhibit-numbered
  - `Reimbursement_Package_PRINT.pdf` — print-and-mail package
- **Add / Import** tab → add manual expenses (e.g. Labor), import new bill PDFs
  or Venmo statement CSVs.
- **Settings** tab → change any percentage, the date cutoff, or the credits toggle.

## Automatic email import
A Claude Cowork scheduled task ("Weekly bill collector") scans Gmail every Monday,
saves bill originals to Google Drive, and reports new items — no manual entry needed.
Manual import in the app remains available any time.

## Rules encoded
50% household (mortgage, utilities, pool, storage, cleaning, lawn, moving,
construction, labor) · 12% school/tuition & medical · AT&T Business flat $100/mo ·
Eli-direct excluded (kept on Review tab) · James pool excluded · utility bills use
current-period charges (never past-due) · duplicates auto-detected · payments to
Lindsey credited.

## Repo
https://github.com/nedpearson/Reimbursements
