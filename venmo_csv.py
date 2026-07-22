"""
Parse Venmo account-statement CSVs and classify outgoing payments.
Privacy: ONLY payments to whitelisted recipients or with a household/kid label are
disclosed. Everything else (business, loans, other people) is dropped entirely and
never appears in any report.
"""
import csv, re, os, glob

# Recipients always disclosed, with their category
RECIPIENT_CATEGORY = {
    'eli pearson':      'Kids-Direct (Eli)',
    'sarah lyons':      'Moving/Household',
    'lions lawncare':   'Lawn/Yard',
}
# Note-keyword -> category (disclosed for ANY recipient except those routed elsewhere)
KEYWORD_CATEGORY = [
    ('clean',   'Cleaning'),
    ('yard',    'Lawn/Yard'),
    ('lawn',    'Lawn/Yard'),
    ('mow',     'Lawn/Yard'),
    ('tutor',   'School/Tuition'),
    ('pack',    'Moving/Household'),
    ('organiz', 'Moving/Household'),
]
CREDIT_RECIPIENT = 'lindsey pearson'   # money to ex -> credit (counted from the Venmo PDF already)
POOL_RECIPIENT   = 'fernando perez'    # pool -> counted from Fernando's invoices; shown but not re-counted
SKIP_COUNTERPARTIES = ('temu','uber','ubr')

def _num(s):
    m=re.search(r'([+-])\s*\$([\d,]+\.\d{2})', s or '')
    return (m.group(1), float(m.group(2).replace(',',''))) if m else (None,None)

def parse(folder):
    rows=[]
    files=[]
    for dp,_,fn in os.walk(folder):
        for f in fn:
            if 'venmostatement' in f.lower() and f.lower().endswith('.csv'):
                files.append(os.path.join(dp,f))
    for path in sorted(files):
        rel=os.path.relpath(path,folder)
        for r in csv.reader(open(path,encoding='utf-8',errors='ignore')):
            if len(r)<10: continue
            if not (re.fullmatch(r'\d{16,}', (r[1] or '').strip()) and 'T' in (r[2] or '')): continue
            typ=r[3].strip(); note=(r[5] or '').strip(); frm=(r[6] or '').strip(); to=(r[7] or '').strip()
            sign,amt=_num(r[8])
            if sign!='-' or amt is None: continue            # only money OUT
            if typ not in ('Payment','Charge'): continue      # skip transfers/crypto/card
            cp = frm if to=='Ned Ecom' else to                # counterparty (payee)
            cpl=cp.lower(); notel=note.lower()
            if any(k in cpl for k in SKIP_COUNTERPARTIES): continue
            date=r[2][:10]
            # ---- routing ----
            if CREDIT_RECIPIENT in cpl:
                continue  # credit handled via the Lindsey Venmo PDF (per Ned's choice of $6,140)
            if POOL_RECIPIENT in cpl:
                rows.append(dict(date=date,vendor='Fernando (Venmo pmt)',category='Pool',
                    desc=f'Pool payment (note: {note or "-"})',amount=round(amt,2),file=rel,
                    include=False,note='pool counted from invoices - not re-counted here'))
                continue
            cat=RECIPIENT_CATEGORY.get(cpl)
            if not cat:
                for kw,c in KEYWORD_CATEGORY:
                    if kw in notel: cat=c; break
            if not cat:
                continue  # NOT DISCLOSED — dropped entirely (private)
            vendor={'Kids-Direct (Eli)':'Eli Pearson (Venmo)','Moving/Household':cp,
                    'Lawn/Yard':cp,'Cleaning':cp,'School/Tuition':cp}.get(cat,cp)
            if cat=='Kids-Direct (Eli)':
                continue  # excluded from claim entirely per Ned; acknowledged as a note in the documents
            rows.append(dict(date=date,vendor=vendor,category=cat,
                desc=(note or 'Venmo payment'),amount=round(amt,2),file=rel,include=True,note='Venmo'))
    return rows

if __name__=='__main__':
    import sys,collections
    rs=parse(sys.argv[1])
    b=collections.defaultdict(lambda:[0,0.0])
    for r in rs:
        key=(r['category'],r['include'])
        b[key][0]+=1; b[key][1]+=r['amount']
    for k,(n,v) in sorted(b.items()): print(k, n, round(v,2))
