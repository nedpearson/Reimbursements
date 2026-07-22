"""One-click 'Email Full Packet'.

Bundles every deliverable (cover letter, statement, workbook, proof pack,
print package, Additional-amounts chart) and opens an email that is ready
to send — nothing depends on the web link.

Order of attack:
  1. Outlook installed?  -> open a draft with every file already ATTACHED.
  2. Otherwise           -> build one ZIP, open a Gmail compose window with
                            subject/body pre-filled, pop File Explorer with
                            the ZIP highlighted, and show a 2-step note:
                            drag the file in, press Send.

Nothing is ever sent automatically — you always press Send yourself.
"""
import os, re, sys, zipfile, subprocess, urllib.parse, webbrowser

HERE   = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'output')

PACKET = [  # (path, nice name)
    (os.path.join(OUTDIR, 'Reimbursement_Cover_Letter.pdf'),  'Cover letter'),
    (os.path.join(OUTDIR, 'Reimbursement_Statement.pdf'),     'Itemized statement'),
    (os.path.join(OUTDIR, 'Reimbursement_Breakdown.xlsx'),    'Excel workbook'),
    (os.path.join(OUTDIR, 'Reimbursement_Proof_Pack.pdf'),    'Proof pack (every bill, exhibit-stamped)'),
    (os.path.join(OUTDIR, 'Reimbursement_Package_PRINT.pdf'), 'Print package'),
    (os.path.join(HERE,   'Amounts_Paid_For_Lindsey.pdf'),    'Additional amounts paid on your behalf'),
]
ZIP_PATH  = os.path.join(OUTDIR, 'Reimbursement_Full_Packet.zip')
GMAIL_MAX = 24 * 1024 * 1024   # stay safely under Gmail's 25 MB cap


def _net_amount():
    """Pull the NET figure out of output/summary.txt (falls back to '')."""
    try:
        txt = open(os.path.join(OUTDIR, 'summary.txt'), encoding='utf-8').read()
        m = re.search(r'NET LINDSEY OWES YOU\s*->\s*\$\s*([\d,]+\.\d\d)', txt)
        return m.group(1) if m else ''
    except Exception:
        return ''


def _existing():
    return [(p, n) for p, n in PACKET if os.path.exists(p)]


def _subject_body():
    net = _net_amount()
    subject = 'Reimbursement packet — Pearson v. Pearson, No. 236951'
    lines = [
        'Lindsey,',
        '',
        'Attached is the complete reimbursement packet: the cover letter, the itemized '
        'statement, the Excel workbook, and the proof pack with every bill included as a '
        'numbered exhibit.',
    ]
    if net:
        lines += ['', f'Total owed: ${net}. Every line item in the statement ties to an '
                      'exhibit in the proof pack.']
    lines += ['', 'If you want the original file for any individual bill, reply and I will '
                  'send it.', '', 'Ned']
    return subject, '\n'.join(lines)


def build_zip():
    files = _existing()
    if not files:
        return None, 'No documents found in the output folder. Open Reimbursement Manager and click "Generate All Documents" first.'
    # If everything is too big for Gmail, drop the print package (it duplicates the rest).
    def make(zfiles):
        with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
            for p, _ in zfiles:
                z.write(p, os.path.basename(p))
        return os.path.getsize(ZIP_PATH)
    size = make(files)
    if size > GMAIL_MAX:
        slim = [(p, n) for p, n in files if 'PRINT' not in p]
        size = make(slim)
        if size > GMAIL_MAX:
            return ZIP_PATH, ('The packet is %.1f MB — over the 25 MB email limit. '
                              'It was still created; send it via Google Drive / WeTransfer, '
                              'or send the proof pack in a second email.' % (size / 1048576))
    return ZIP_PATH, None


def try_outlook(subject, body):
    """Open an Outlook draft with every file attached. True on success."""
    try:
        import win32com.client  # pywin32, only if user has it
        ol = win32com.client.Dispatch('Outlook.Application')
        mail = ol.CreateItem(0)
        mail.Subject, mail.Body = subject, body
        for p, _ in _existing():
            mail.Attachments.Add(p)
        mail.Display()   # draft window — user presses Send
        return True
    except Exception:
        return False


def _popup(title, msg, warn=False):
    try:
        import tkinter as tk
        from tkinter import messagebox
        created = False
        if not getattr(tk, '_default_root', None):
            r = tk.Tk(); r.withdraw(); created = True
        (messagebox.showwarning if warn else messagebox.showinfo)(title, msg)
        if created:
            r.destroy()
    except Exception:
        print(msg)


def gmail_fallback(subject, body, zip_path, warn):
    compose = ('https://mail.google.com/mail/?view=cm&fs=1&su='
               + urllib.parse.quote(subject) + '&body=' + urllib.parse.quote(body))
    webbrowser.open(compose)
    if sys.platform.startswith('win'):
        subprocess.Popen(['explorer', '/select,', zip_path])
    msg = ('Your email is open in the browser with the subject and message filled in.\n\n'
           '1)  Drag the highlighted file  "%s"  from the File Explorer window into the email.\n'
           '2)  Add Lindsey\'s address and press Send.' % os.path.basename(zip_path))
    if warn:
        msg += '\n\nNote: ' + warn
    _popup('Email Full Packet — 2 steps left', msg)


def main():
    subject, body = _subject_body()
    zip_path, warn = build_zip()
    if zip_path is None:                    # nothing generated yet
        _popup('Email Full Packet', warn, warn=True)
        return
    if try_outlook(subject, body):
        return
    gmail_fallback(subject, body, zip_path, warn)


if __name__ == '__main__':
    main()
