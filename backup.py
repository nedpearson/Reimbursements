r"""Safety backups + archive for the Reimbursement Manager.

Every time documents are generated (via the app or Publish to Web), a small
snapshot of the DATA files is saved to  archive\<timestamp>\  first — so if the
wrong button is pushed, the previous state can be restored in one click.

Only the small editable data files are archived (not the big generated PDFs):
config.json, additional.json, disputes.json, settled.json, paidback.json, and a
copy of output\summary.txt / ledger.csv for reference. Snapshots are local (the
archive folder is not published to the web).
"""
import os, json, shutil, hashlib, datetime as _dt, re

HERE   = os.path.dirname(os.path.abspath(__file__))
ARCH   = os.path.join(HERE, 'archive')
DATA   = ['config.json', 'additional.json', 'disputes.json', 'settled.json', 'paidback.json']
REFS   = [os.path.join('output', 'summary.txt'), os.path.join('output', 'ledger.csv')]
KEEP   = 60          # keep at most this many snapshots (manual ones are never auto-pruned)


def _now():
    return _dt.datetime.now()


def _data_hash():
    h = hashlib.md5()
    for f in DATA:
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            h.update(open(p, 'rb').read())
    return h.hexdigest()


def _net_from_summary():
    p = os.path.join(HERE, 'output', 'summary.txt')
    try:
        m = re.search(r'NET LINDSEY OWES YOU\s*->\s*\$\s*([\d,]+\.\d\d)', open(p, encoding='utf-8').read())
        if m:
            return float(m.group(1).replace(',', ''))
    except Exception:
        pass
    return None


def snapshot(note='', auto=True, stamp=None):
    """Save a snapshot. Auto snapshots are skipped if the data is unchanged
    since the most recent snapshot. Returns the snapshot id, or None if skipped."""
    os.makedirs(ARCH, exist_ok=True)
    cur = _data_hash()
    if auto:
        recent = snapshots()
        if recent and recent[0].get('hash') == cur:
            return None                      # nothing changed — no point saving again
    ts = stamp or _now().strftime('%Y%m%d-%H%M%S')
    sid = ts + ('' if auto else '-saved')
    dest = os.path.join(ARCH, sid)
    i = 1
    while os.path.exists(dest):
        dest = os.path.join(ARCH, sid + '-%d' % i); i += 1
    sid = os.path.basename(dest)
    os.makedirs(dest)
    saved = []
    for f in DATA:
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dest, f)); saved.append(f)
    refdir = os.path.join(dest, 'output');
    for rf in REFS:
        p = os.path.join(HERE, rf)
        if os.path.exists(p):
            os.makedirs(refdir, exist_ok=True); shutil.copy2(p, os.path.join(dest, rf))
    man = dict(when=_now().isoformat(timespec='seconds'),
               when_human=_now().strftime('%b %d, %Y  %I:%M %p'),
               note=note.strip(), auto=bool(auto), net=_net_from_summary(),
               hash=cur, files=saved)
    json.dump(man, open(os.path.join(dest, 'manifest.json'), 'w', encoding='utf-8'), indent=1)
    _prune()
    return sid


def snapshots():
    """Newest first."""
    if not os.path.isdir(ARCH):
        return []
    out = []
    for name in os.listdir(ARCH):
        d = os.path.join(ARCH, name)
        mp = os.path.join(d, 'manifest.json')
        if os.path.isdir(d) and os.path.exists(mp):
            try:
                m = json.load(open(mp, encoding='utf-8'))
            except Exception:
                m = {}
            m['id'] = name
            out.append(m)
    out.sort(key=lambda m: m.get('when', m['id']), reverse=True)
    return out


def restore(sid):
    """Restore a snapshot's data files over the live ones. The current state is
    itself snapshotted first (auto) so a restore is always undoable."""
    d = os.path.join(ARCH, sid)
    if not os.path.isdir(d):
        raise FileNotFoundError('snapshot not found: %s' % sid)
    snapshot(note='auto — before restoring %s' % sid, auto=False)
    restored = []
    for f in DATA:
        src = os.path.join(d, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(HERE, f)); restored.append(f)
    return restored


def delete(sid):
    d = os.path.join(ARCH, sid)
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)


def _prune():
    snaps = snapshots()
    if len(snaps) <= KEEP:
        return
    # drop oldest AUTO snapshots beyond the cap; keep manual ('-saved') ones
    autos = [s for s in snaps if s.get('auto')]
    for s in autos[KEEP:]:
        delete(s['id'])


if __name__ == '__main__':
    print('snapshot:', snapshot(note='manual test', auto=False))
    for s in snapshots()[:5]:
        print(' ', s['id'], s.get('net'), s.get('note'))
