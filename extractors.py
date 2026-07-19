"""Per-vendor amount/date extraction. Returns list of line-item dicts."""
import os, re, glob
from parsers import (_lines_from_pdf, _looks_like_html_pdf, _decode_html_embedded_pdf,
                     _ocr_lines_cli, _merge_split_money, money, norm_date, detect_vendor)

CATEGORY = {
 'atmos':'Utilities','entergy':'Utilities','brwater':'Utilities','att_internet':'Utilities',
 'pool':'Pool','pods':'Storage','cleaning':'Cleaning','venmo_lions':'Lawn/Yard',
 'att_business':'AT&T Business','facts':'School/Tuition','studyville':'School/Tuition',
 'venmo_eli':'Kids-Direct (Eli)','venmo_lindsey':'Credit/Payment to Lindsey',
}
VENDOR_LABEL = {
 'atmos':'Atmos (Gas)','entergy':'Entergy (Electric)','brwater':'BR Water','att_internet':'AT&T Internet',
 'pool':'Pool (Fernando)','pods':'PODS (Storage)','cleaning':'House Cleaning','venmo_lions':'Lions Lawncare',
 'att_business':'AT&T Business (Pearsons Luggage)','facts':"St Luke's School (FACTS)",'studyville':'Studyville',
 'venmo_eli':'Payments to Eli','venmo_lindsey':'Paid TO Lindsey',
}

def _text(lines): return "\n".join(lines)

def get_lines(path):
    """Return (lines, note). Handles normal, html-wrapped, and scanned pdfs + images."""
    low=path.lower()
    if low.endswith(('.png','.jpg','.jpeg')):
        return _ocr_lines_cli(path), 'ocr'
    if _looks_like_html_pdf(path):
        real=_decode_html_embedded_pdf(path)
        if real: return _lines_from_pdf(real), 'html-embedded-pdf'
    lines=_lines_from_pdf(path)
    if len("".join(lines))<40:            # scanned image pdf
        return _ocr_lines_cli(path,pages=1), 'ocr'
    return lines, ''

# ---- individual vendor extractors: return (date, amount, desc, extra_note) or None ----
def ex_atmos(ls):
    t=_text(ls); dm=re.search(r'Billing Date:\s*([\d/]+)',t); cur=None
    for i,l in enumerate(ls):
        if l.rstrip(':')=='Current Charges' and i+1<len(ls) and money(ls[i+1]) is not None:
            cur=money(ls[i+1]); break
    return norm_date(dm.group(1) if dm else ''), cur, 'Gas current charges',''

def ex_entergy(ls):
    M=_merge_split_money(ls); T=" ".join(M)
    dm=re.search(r'Mail\s*Date\s*(\d{2}/\d{2}/\d{4})',T)
    cur=None
    m=re.search(r'Amount Due by(?: Due date)?\s*\d{2}/\d{2}/\d{4}\.?\s*\$(\d+\.\d{2})',T)
    if m: cur=float(m.group(1))
    if cur is None:
        m=re.search(r'\$(\d+\.\d{2})\s*Amount Due by',T)
        if m: cur=float(m.group(1))
    note=''
    if cur is None and re.search(r'DO NOT PAY|credit balance',T,re.I):
        cur=0.0; note='credit balance / do not pay'
    return norm_date(dm.group(1) if dm else ''), cur, 'Electric amount due (current period)', note

def ex_brwater(ls):
    amt=None; due=''; t="\n".join(ls)
    for i,l in enumerate(ls):
        if l=='Amount Due' and i+1<len(ls) and amt is None: amt=money(ls[i+1])
        if l=='Due Date' and i+1<len(ls) and not due: due=ls[i+1]
    svc=next((l for l in ls if 'FAIRWAY' in l.upper()),'')
    typ='Irrigation' if 'IRRG' in svc.upper() else 'Water/Sewer'
    if amt is None:
        pa=re.search(r'Payment Amount:\s*\$([\d,]+\.\d{2})',t)
        pd=re.search(r'Payment Date:\s*([\d/]+)',t)
        if pa:  # this is a PAYMENT CONFIRMATION, not a bill -> flag as duplicate
            return norm_date(pd.group(1) if pd else ''), float(pa.group(1).replace(',','')), f'{typ} PAYMENT CONFIRMATION', 'payment-confirmation'
    return norm_date(due), amt, f'{typ} amount due',''

def ex_att_internet(ls):
    t=_text(ls); dm=re.search(r'Issue Date:?\s*([A-Za-z]{3} \d{2}, \d{4})',t); cur=None
    for i,l in enumerate(ls):
        if l.lower()=='total for internet' and i+1<len(ls): cur=money(ls[i+1])
    return norm_date(dm.group(1) if dm else ''), cur, 'Internet monthly charge',''

def ex_att_business(ls):
    t=_text(ls); dm=re.search(r'Issue Date:\s*([A-Za-z]{3} \d{2}, \d{4})',t); cur=None
    for i,l in enumerate(ls):
        if l.lower()=='total services' and i+1<len(ls): cur=money(ls[i+1])
    return norm_date(dm.group(1) if dm else ''), cur, 'Wireless (Pearsons Luggage) current services',''

def ex_pool(ls):
    t=_text(ls); dm=re.search(r'DATE\s*(\d{2}/\d{2}/\d{4})',t)
    inv=re.search(r'INVOICE #\s*(\d+)',t); pay=bal=None
    for i,l in enumerate(ls):
        if l=='PAYMENT' and i+1<len(ls): pay=money(ls[i+1])
        if l=='BALANCE DUE' and i+1<len(ls): bal=money(ls[i+1])
    return norm_date(dm.group(1) if dm else ''), round((pay or 0)+(bal or 0),2), f"Pool service inv#{inv.group(1) if inv else '?'}", (inv.group(1) if inv else '')

def ex_pods(ls):
    t=_text(ls); dm=re.search(r'Invoice Date\s*(\d{2}/\d{2}/\d{4})',t)
    amt=None
    m=re.search(r'Invoice Total \(USD\)\s*\$([\d,]+\.\d{2})',t) or re.search(r'Invoice amount\s*\$([\d,]+\.\d{2})',t)
    if m: amt=float(m.group(1).replace(',',''))
    return norm_date(dm.group(1) if dm else ''), amt, 'Storage container',''

def ex_facts(ls):
    t=_text(ls); dm=re.search(r'Payment Date\s*(\d{2} [A-Za-z]{3} \d{4})',t)
    pay=re.search(r'payment for \$([\d,]+\.\d{2})',t)
    pid=re.search(r'payid/(\d+)',t)
    amt=float(pay.group(1).replace(',','')) if pay else None
    return norm_date(dm.group(1) if dm else ''), amt, 'Tuition payment', (pid.group(1) if pid else '')

def ex_studyville(ls):
    t=_text(ls)
    # payment receipt?
    paid=re.search(r'You paid \$([\d,]+\.\d{2})',t)
    on=re.search(r'on (\d{2}/\d{2}/\d{4})',t)
    tot=re.search(r'Total:\s*\$([\d,]+\.\d{2})',t)
    sale=re.search(r'Sale ID:?\s*(\d+)',t) or re.search(r'Sale ID\s*(\d+)',t)
    sdate=re.search(r'Sale [Dd]ate:?\s*([\d/]+)',t)
    if paid:  # payment confirmation
        return norm_date(on.group(1) if on else (sdate.group(1) if sdate else '')), float(paid.group(1).replace(',','')), 'Payment', ('receipt|sale'+(sale.group(1) if sale else ''))
    if tot and 'sales receipt' in t.lower():  # mindbody receipt
        return norm_date(sdate.group(1) if sdate else ''), float(tot.group(1).replace(',','')), 'Payment', ('receipt|sale'+(sale.group(1) if sale else ''))
    # invoice (billed, not necessarily paid)
    inv=re.search(r'Invoice no\.?:?\s*(\d+)',t); idate=re.search(r'Invoice date:\s*([\d/]+)',t)
    itot=re.search(r'Total\s*\$([\d,]+\.\d{2})',t)
    if itot:
        return norm_date(idate.group(1) if idate else ''), float(itot.group(1).replace(',','')), f"INVOICE #{inv.group(1) if inv else '?'} (billed)", ('invoice|'+(inv.group(1) if inv else ''))
    return '',None,'',''

def ex_cleaning(ls):
    t=_text(ls); dm=re.search(r'([A-Z][a-z]{2} \d{1,2}, \d{4})',t)
    amt=None
    m=re.search(r'\$([\d,]+\.\d{2})',t)
    if m: amt=float(m.group(1).replace(',',''))
    return norm_date(dm.group(1) if dm else ''), amt, 'House cleaning (Zelle)',''

def ex_venmo(ls, who):
    """Return list of (date,amount,desc) for each 'You paid X'."""
    out=[]; i=0
    while i<len(ls):
        if ls[i].startswith('You paid'):
            date=ls[i+1] if i+1<len(ls) else ''; amt=None; note=''
            j=i+1
            for j in range(i+1,min(i+6,len(ls))):
                m=re.match(r'-\s*\$([\d,]+\.\d{2})',ls[j])
                if m: amt=float(m.group(1).replace(',','')); break
                if j>i+1 and ls[j] not in ('.',) and not ls[j].startswith('-'): note=ls[j]
            out.append((date,amt,note)); i=j+1 if amt else i+1
        else: i+=1
    return out

def reconcile_studyville(files, folder, get_lines):
    """Treat-all-as-paid reconciliation. Returns list of row dicts."""
    import os, re
    invoices={}   # inv# -> dict
    receipts=[]   # dicts
    debts=[]
    for p in files:
        lines,_=get_lines(p); t="\n".join(lines); rel=os.path.relpath(p,folder)
        if re.search(r'debt collect',t,re.I):
            m=re.search(r'total amount due is \$([\d,]+)',t,re.I)
            debts.append(dict(date='',amount=(float(m.group(1).replace(',','')) if m else None),file=rel)); continue
        inv=re.search(r'Invoice no\.?:?\s*(\d+)',t); invdate=re.search(r'Invoice date:?\s*([\d/]+)',t)
        paid=re.search(r'You paid \$([\d,]+\.\d{2})',t); on=re.search(r'on (\d{2}/\d{2}/\d{4})',t)
        tot=re.search(r'Total:?\s*\$([\d,]+\.\d{2})',t); sale=re.search(r'Sale ID:?\s*(\d+)',t)
        amtdue=re.search(r'Amount due\s*\$([\d,]+\.\d{2})',t)
        sdate=re.search(r'Sale [Dd]ate:?\s*([\d/]+)',t)
        is_invoice = invdate and tot and inv and not paid
        if is_invoice:
            num=inv.group(1)
            if num not in invoices:
                invoices[num]=dict(date=norm_date(invdate.group(1)),amount=float(tot.group(1).replace(',','')),
                                   file=rel,invno=num)
            else:
                receipts.append(dict(kind='dupinv',date=norm_date(invdate.group(1)),amount=float(tot.group(1).replace(',','')),
                                     invref=num,sale=None,file=rel,amtdue=None))
        else:
            amt=float(paid.group(1).replace(',','')) if paid else (float(tot.group(1).replace(',','')) if tot else None)
            receipts.append(dict(kind='receipt',date=norm_date(on.group(1) if on else (sdate.group(1) if sdate else '')),
                amount=amt,invref=(inv.group(1) if inv else None),
                sale=(sale.group(1) if sale else None),file=rel,
                amtdue=(float(amtdue.group(1)) if amtdue else None)))
    rows=[]
    seen_sale=set()
    for num,d in invoices.items():
        rows.append(dict(date=d['date'],vendor='Studyville',category='School/Tuition',
            desc=f'Tuition invoice #{num} (treated as paid)',amount=round(d['amount'],2),file=d['file'],
            include=True,note='invoice counted as paid'))
    for r in receipts:
        inc=True; note=''
        if r['kind']=='dupinv':
            inc=False; note=f"duplicate of invoice #{r['invref']} already counted"
        elif r.get('amtdue')==0.0:
            inc=False; note='$0 due - duplicate view of a counted charge'
        elif r['invref'] and r['invref'] in invoices:
            inc=False; note=f"partial payment toward invoice #{r['invref']} (already counted in full)"
        elif r['sale'] and r['sale'] in seen_sale:
            inc=False; note='duplicate sale/receipt'
        else:
            if r['sale']: seen_sale.add(r['sale'])
        rows.append(dict(date=r['date'],vendor=('Studyville' if inc else 'Studyville (dup/partial)'),
            category='School/Tuition',desc=('Tuition payment' if inc else 'Studyville receipt'),
            amount=(round(r['amount'],2) if r['amount'] is not None else None),file=r['file'],include=inc,note=note))
    for d in debts:
        rows.append(dict(date=d['date'],vendor='Studyville (COLLECTIONS)',category='School/Tuition',
            desc='Debt-collection notice (unpaid balance of invoices already counted)',
            amount=d['amount'],file=d['file'],include=False,note='not added - represented by invoices above'))
    return rows
