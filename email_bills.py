"""
Bills found in Ned's Gmail (swept 2026-07-18) that are NOT in the House Bills folder.
Each entry was hand-verified against the folder to avoid double-counting.
Re-run guard: an entry is skipped if a paper bill for the same vendor+month
(or same pool invoice #) has since been added to the folder.
"""
ENTRIES=[
 # --- Entergy: months with no PDF on file (total amount due from bill-ready emails) ---
 dict(v='Entergy (Electric)',cat='Utilities',d='2024-09-07',a=522.76,n='from email - no PDF on file'),
 dict(v='Entergy (Electric)',cat='Utilities',d='2024-12-06',a=506.49,n='from email - no PDF on file'),
 dict(v='Entergy (Electric)',cat='Utilities',d='2025-01-09',a=511.18,n='from email - no PDF on file'),
 dict(v='Entergy (Electric)',cat='Utilities',d='2026-04-08',a=472.14,n='from email - PDF on file unparseable'),
 dict(v='Entergy (Electric)',cat='Utilities',d='2026-06-06',a=412.17,n='from email - no PDF on file'),
 # --- Atmos: current charges for months w/o PDF ---
 dict(v='Atmos (Gas)',cat='Utilities',d='2024-08-12',a=84.20,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2024-09-11',a=36.94,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2024-10-10',a=59.81,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2024-11-11',a=53.16,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2024-12-11',a=63.83,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2025-01-13',a=68.48,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2025-07-11',a=49.96,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2026-05-12',a=41.88,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2026-06-10',a=57.46,n='from email (current charges)'),
 dict(v='Atmos (Gas)',cat='Utilities',d='2026-07-13',a=50.83,n='from email (current charges)'),
 # --- AT&T internet 4580: pre-Feb-2025 and tail months w/o PDF ---
 dict(v='AT&T Internet',cat='Utilities',d='2024-08-31',a=110.38,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2024-09-30',a=110.38,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2024-10-30',a=110.38,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2024-12-01',a=115.38,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2024-12-30',a=115.38,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2025-02-02',a=115.40,n='from email (Jan service)'),
 dict(v='AT&T Internet',cat='Utilities',d='2026-03-31',a=125.42,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2026-05-31',a=160.42,n='from email'),
 dict(v='AT&T Internet',cat='Utilities',d='2026-07-01',a=125.42,n='from email'),
 # --- AT&T Business (Pearsons Luggage) 2825: all months w/o PDF ---
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2024-08-22',a=794.98,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2024-09-22',a=804.96,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2024-10-22',a=791.50,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2024-11-22',a=773.47,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-02-22',a=805.91,n='from email (Dec24/Jan25 not in inbox)'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-03-22',a=800.43,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-04-22',a=2931.19,n='from email - includes device purchase'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-05-22',a=560.44,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-06-22',a=552.41,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-07-22',a=552.41,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-08-22',a=552.40,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-09-22',a=690.14,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-10-22',a=575.96,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-11-22',a=578.17,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2025-12-22',a=796.16,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2026-03-22',a=662.53,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2026-04-24',a=1329.98,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2026-05-24',a=689.70,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2026-06-24',a=1473.59,n='from email'),
 dict(v='AT&T Business (Pearsons Luggage)',cat='AT&T Business',d='2026-07-22',a=228.22,n='from email'),
 # --- Pool (Fernando): invoices found in email, not in folder (deduped by invoice #) ---
 dict(v='Pool (Fernando)',cat='Pool',d='2024-09-18',a=356.00,n='inv#2119 from email',inv='2119'),
 dict(v='Pool (Fernando)',cat='Pool',d='2024-10-04',a=443.00,n='inv#2178 from email',inv='2178'),
 dict(v='Pool (Fernando)',cat='Pool',d='2024-11-04',a=356.00,n='inv#2234 from email',inv='2234'),
 dict(v='Pool (Fernando)',cat='Pool',d='2024-12-04',a=348.00,n='inv#2298 from email',inv='2298'),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-01-07',a=429.00,n='inv#2375 from email',inv='2375'),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-01-25',a=280.00,n='inv#2319 - JAMES POOL, not the Fairway house',inv='2319',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-01-25',a=280.00,n='inv#2383 - JAMES POOL, not the Fairway house',inv='2383',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-02-25',a=350.00,n='inv#2450 - JAMES POOL, not the Fairway house',inv='2450',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-03-14',a=280.00,n='inv#2507 - JAMES POOL, not the Fairway house',inv='2507',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-06-10',a=280.00,n='inv#2625 - JAMES POOL, not the Fairway house',inv='2625',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-06-10',a=350.00,n='inv#2698 - JAMES POOL, not the Fairway house',inv='2698',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-07-03',a=280.00,n='inv#2766 - JAMES POOL, not the Fairway house',inv='2766',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-08-14',a=376.00,n='inv#2801 from email',inv='2801'),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-08-14',a=350.00,n='inv#2836 - JAMES POOL, not the Fairway house',inv='2836',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-09-08',a=280.00,n='inv#2911 - JAMES POOL, not the Fairway house',inv='2911',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-10-14',a=280.00,n='inv#3008 - JAMES POOL, not the Fairway house',inv='3008',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-11-06',a=350.00,n='inv#3048 - JAMES POOL, not the Fairway house',inv='3048',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2025-12-01',a=280.00,n='inv#3134 - JAMES POOL, not the Fairway house',inv='3134',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2026-01-05',a=350.00,n='inv#3189 - JAMES POOL, not the Fairway house',inv='3189',excl=True),
 dict(v='Pool (Fernando)',cat='Pool',d='2026-05-08',a=425.00,n='inv#3435 from email',inv='3435'),
 dict(v='Pool (Fernando)',cat='Pool',d='2026-06-08',a=460.00,n='inv#3526 from email',inv='3526'),
 dict(v='Pool (Fernando)',cat='Pool',d='2026-06-25',a=475.00,n='inv#3576 from email',inv='3576'),
 # --- BR Water irrigation autopay confirmations ---
 dict(v='BR Water',cat='Utilities',d='2026-05-12',a=62.36,n='Irrigation autopay (email)'),
 dict(v='BR Water',cat='Utilities',d='2026-06-09',a=18.94,n='Irrigation autopay (email)'),
 dict(v='BR Water',cat='Utilities',d='2026-07-09',a=12.39,n='Irrigation autopay (email)'),
 # --- PODS: recurring months not in folder; service ended 5/15/2026 ---
 dict(v='PODS (Storage)',cat='Storage',d='2026-02-10',a=279.00,n='recurring rate from PODS order (email)'),
 dict(v='PODS (Storage)',cat='Storage',d='2026-03-10',a=279.00,n='recurring rate from PODS order (email)'),
 dict(v='PODS (Storage)',cat='Storage',d='2026-04-10',a=279.00,n='recurring rate from PODS order (email)'),
 dict(v='PODS (Storage)',cat='Storage',d='2026-05-15',a=330.75,n='final month + pickup fee 51.75 (email)'),
 # --- De Roman's Construction (sale-prep work at 8792 W Fairway) — 50% per Ned ---
 dict(v="De Roman's Construction",cat="Construction (De Roman's)",d='2026-03-24',a=5600.00,
      n="inv#0000717 - renovation phase 1, sale prep (paid; 'payment to Paco')",inv='DR0000717'),
 dict(v="De Roman's Construction",cat="Construction (De Roman's)",d='2026-05-31',a=10300.00,
      n="inv#0001127 - shower & laundry room completion, realtor punch list (paid)",inv='DR0001127'),
 # --- BR Water Jan-May 2025 (from unlocked bills in Ned's 6/17/25 email; current charges per month) ---
 dict(v='BR Water',cat='Utilities',d='2025-01-20',a=177.42,n='Water/Sewer Jan 2025 current charges (email)',inv='BRW-2501-R'),
 dict(v='BR Water',cat='Utilities',d='2025-02-20',a=173.99,n='Water/Sewer Feb 2025 current charges (email)',inv='BRW-2502-R'),
 dict(v='BR Water',cat='Utilities',d='2025-03-20',a=151.19,n='Water/Sewer Mar 2025 current charges (email)',inv='BRW-2503-R'),
 dict(v='BR Water',cat='Utilities',d='2025-04-20',a=157.27,n='Water/Sewer Apr 2025 current charges (email)',inv='BRW-2504-R'),
 dict(v='BR Water',cat='Utilities',d='2025-05-20',a=137.49,n='Water/Sewer May 2025 current charges (email)',inv='BRW-2505-R'),
 dict(v='BR Water',cat='Utilities',d='2025-01-20',a=38.79,n='Irrigation Jan 2025 current charges (email)',inv='BRW-2501-I'),
 dict(v='BR Water',cat='Utilities',d='2025-05-20',a=18.19,n='Irrigation May 2025 current charges (email)',inv='BRW-2505-I'),
]

def merge(rows):
    """Append email entries, skipping any month/invoice now covered by a file-based row."""
    monthcov={}   # (vendor, YYYY-MM) -> max positive amount seen from files
    invcov=set()
    for r in rows:
        if r.get('date') and r.get('amount'):
            monthcov[(r['vendor'],r['date'][:7])]=max(monthcov.get((r['vendor'],r['date'][:7]),0),r['amount'] or 0)
        import re as _re
        m=_re.search(r'inv#(\d+)',r.get('desc') or '')
        if m: invcov.add(m.group(1))
    out=[]
    for e in ENTRIES:
        if e.get('inv') and e['inv'] in invcov: continue
        if not e.get('inv') and monthcov.get((e['v'],e['d'][:7]),0)>0: continue
        inc=not e.get('excl')
        row=dict(date=e['d'],vendor=(e['v'] if inc else e['v']+' — James pool'),category=e['cat'],desc=e['n'],
            amount=e['a'],file='(from Gmail sweep 2026-07-18)',include=inc,
            note=('email-sourced' if inc else 'James pool - excluded per Ned'))
        if e['cat']=='AT&T Business':
            row['flat_share']=100.0; row['note']+=' | flat $100/mo per agreement'
        out.append(row)
    return out
