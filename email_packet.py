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


def _user_email():
    """The account the email is sent FROM (config 'user_email', editable)."""
    try:
        import json
        cfg = json.load(open(os.path.join(HERE, 'config.json')))
        return (cfg.get('user_email') or '').strip() or 'nedpearson@gmail.com'
    except Exception:
        return 'nedpearson@gmail.com'


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


def _subject_body(greeting=''):
    net = _net_amount()
    subject = 'Reimbursement packet — Pearson v. Pearson, No. 236951'
    lines = [
        (greeting.rstrip(',') + ',') if greeting else 'Hello,',
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


def _ask_recipient():
    """Small dialog: who is this going to? Returns (email, greeting) — both may be ''.
    Blank email = compose opens with the To field empty, fill it in yourself."""
    try:
        import tkinter as tk
        created = False
        root = getattr(tk, '_default_root', None)
        if not root:
            root = tk.Tk(); root.withdraw(); created = True
        dlg = tk.Toplevel(root); dlg.title('Email Full Packet')
        dlg.attributes('-topmost', True); dlg.resizable(False, False); dlg.grab_set()
        tk.Label(dlg, text='Send to (email address — leave blank to type it in Gmail):',
                 anchor='w').grid(row=0, column=0, sticky='w', padx=12, pady=(12, 2))
        e_to = tk.Entry(dlg, width=44); e_to.grid(row=1, column=0, padx=12, sticky='we')
        tk.Label(dlg, text='Greeting name (optional — e.g. Lindsey, or leave blank):',
                 anchor='w').grid(row=2, column=0, sticky='w', padx=12, pady=(10, 2))
        e_nm = tk.Entry(dlg, width=44); e_nm.grid(row=3, column=0, padx=12, sticky='we')
        res = {'ok': False}
        def ok(*_):    res['ok'] = True;  dlg.destroy()
        def cancel(*_):                    dlg.destroy()
        bf = tk.Frame(dlg); bf.grid(row=4, column=0, pady=12)
        tk.Button(bf, text='Continue', width=12, bg='#1F3864', fg='white',
                  relief='flat', command=ok).pack(side='left', padx=6)
        tk.Button(bf, text='Cancel', width=10, command=cancel).pack(side='left', padx=6)
        dlg.bind('<Return>', ok); dlg.bind('<Escape>', cancel)
        e_to.focus_set(); root.wait_window(dlg)
        to, nm = e_to.get().strip(), e_nm.get().strip()
        if created:
            root.destroy()
        if not res['ok']:
            return None, None            # cancelled
        return to, nm
    except Exception:
        return '', ''                    # headless fallback: no recipient pre-filled


def build_zip():
    files = _existing()
    if not files:
        return None, 'No documents found in the output folder. Open Reimbursement Manager and click "Generate All Documents" first.'
    # If everything is too big for Gmail, drop the print package (it duplicates the rest).
    from safewrite import write_via_temp
    def make(zfiles):
        def w(tmp):
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
                for p, _ in zfiles:
                    z.write(p, os.path.basename(p))
        if not write_via_temp(ZIP_PATH, w, print):
            return -1                     # zip locked (open in Explorer preview etc.)
        return os.path.getsize(ZIP_PATH)
    size = make(files)
    if size < 0:
        return ZIP_PATH, ('Could not refresh the zip — it is open in another window. '
                          'The previous zip will be attached; close it and retry for the latest.')
    if size > GMAIL_MAX:
        slim = [(p, n) for p, n in files if 'PRINT' not in p]
        size = make(slim)
        if size > GMAIL_MAX:
            return ZIP_PATH, ('The packet is %.1f MB — over the 25 MB email limit. '
                              'It was still created; send it via Google Drive / WeTransfer, '
                              'or send the proof pack in a second email.' % (size / 1048576))
    return ZIP_PATH, None


def _outlook_configured():
    """True only if Outlook actually has a mail profile set up.
    (Launching an unconfigured Outlook pops its account-setup wizard.)"""
    if not sys.platform.startswith('win'):
        return False
    try:
        import winreg
        for ver in ('16.0', '15.0'):
            try:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                   r'Software\Microsoft\Office\%s\Outlook\Profiles' % ver)
                has = winreg.QueryInfoKey(k)[0] > 0   # at least one profile subkey
                winreg.CloseKey(k)
                if has:
                    return True
            except OSError:
                continue
    except Exception:
        pass
    return False


def try_outlook(subject, body, to=''):
    """Open an Outlook draft with every file attached. True on success."""
    if not _outlook_configured():
        return False
    try:
        import win32com.client  # pywin32, only if user has it
        ol = win32com.client.Dispatch('Outlook.Application')
        mail = ol.CreateItem(0)
        mail.Subject, mail.Body = subject, body
        if to:
            mail.To = to
        try:   # send from the configured account if Outlook has several
            for acct in ol.Session.Accounts:
                if str(acct.SmtpAddress).lower() == _user_email().lower():
                    mail._oleobj_.Invoke(64209, 0, 8, 0, acct)  # SendUsingAccount
                    break
        except Exception:
            pass
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
        r = getattr(tk, '_default_root', None)
        if not r:
            r = tk.Tk(); r.withdraw(); created = True
        try:
            r.attributes('-topmost', True)   # don't hide behind the browser
        except Exception:
            pass
        fn = messagebox.showwarning if warn else messagebox.showinfo
        fn(title, msg, parent=r)
        if created:
            r.destroy()
        else:
            try: r.attributes('-topmost', False)
            except Exception: pass
    except Exception:
        print(msg)


def gmail_fallback(subject, body, zip_path, warn, to=''):
    compose = ('https://mail.google.com/mail/?authuser='
               + urllib.parse.quote(_user_email())          # open under YOUR account
               + '&view=cm&fs=1'
               + (('&to=' + urllib.parse.quote(to)) if to else '')
               + '&su=' + urllib.parse.quote(subject) + '&body=' + urllib.parse.quote(body))
    webbrowser.open(compose)
    if sys.platform.startswith('win'):
        subprocess.Popen(['explorer', '/select,', zip_path])
    step2 = 'Press Send.' if to else 'Add the recipient\'s address and press Send.'
    msg = ('Your email is open in the browser with the subject and message filled in'
           + (' and addressed to %s' % to if to else '') + '.\n\n'
           '1)  Drag the highlighted file  "%s"  from the File Explorer window into the email.\n'
           '2)  ' % os.path.basename(zip_path) + step2)
    if warn:
        msg += '\n\nNote: ' + warn
    _popup('Email Full Packet — 2 steps left', msg)


def main():
    to, greeting = _ask_recipient()
    if to is None:                          # user pressed Cancel
        return
    subject, body = _subject_body(greeting)
    zip_path, warn = build_zip()
    if zip_path is None:                    # nothing generated yet
        _popup('Email Full Packet', warn, warn=True)
        return
    if try_outlook(subject, body, to):
        return
    gmail_fallback(subject, body, zip_path, warn, to)


if __name__ == '__main__':
    main()
