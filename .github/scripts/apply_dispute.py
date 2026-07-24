#!/usr/bin/env python3
"""Apply a dispute decision to docs/overrides.json.

Reads TITLE and BODY (from the GitHub issue) out of the environment. The issue body,
built by the portal's Dispute button, looks like:

    id: <stable charge id>
    label: <human label, e.g. C-042 · Exhibit 12 — Pool 2025-02-01 $342.00>
    action: approve   (or: deny)

approve -> add to "removed" (portal drops the charge + recomputes every total)
deny    -> add to "denied"  (charge stays, shown as "reviewed — dispute declined")
"""
import os, re, json, datetime

body = os.environ.get('BODY', '') or ''
title = os.environ.get('TITLE', '') or ''

def field(name):
    m = re.search(r'(?im)^\s*%s\s*:\s*(.+?)\s*$' % re.escape(name), body)
    return m.group(1).strip() if m else ''

cid = field('id')
label = field('label')
action = (field('action') or ('approve' if 'approve' in title.lower() else 'deny')).lower()

if not cid:
    print('No charge id found in issue body; nothing to do.')
    raise SystemExit(0)

path = os.path.join('docs', 'overrides.json')
try:
    data = json.load(open(path, encoding='utf-8'))
except Exception:
    data = {}
data.setdefault('removed', [])
data.setdefault('denied', [])

# one decision per charge id — clear any prior decision first
data['removed'] = [x for x in data['removed'] if x.get('id') != cid]
data['denied'] = [x for x in data['denied'] if x.get('id') != cid]

now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
if action == 'approve':
    data['removed'].append({'id': cid, 'label': label, 'reason': 'dispute upheld', 'ts': now})
    print('APPROVED — removed:', label or cid)
else:
    data['denied'].append({'id': cid, 'label': label, 'note': 'reviewed — charge stands', 'ts': now})
    print('DENIED — kept:', label or cid)

json.dump(data, open(path, 'w', encoding='utf-8'), indent=1)
