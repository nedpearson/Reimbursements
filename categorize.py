#!/usr/bin/env python3
"""
Reimbursement auto-categorizer.
Usage:  python3 categorize.py "/path/to/House Bills"
Outputs (next to this script): ledger.csv, reimbursement.xlsx, summary.txt
Drop new bills into the folder and re-run — new items are auto-categorized.
"""
import os, sys, re, glob, json, csv, hashlib, datetime as _dt
import parsers, extractors as EX
import venmo_csv
import email_bills
try:
    import report
except Exception:
    report=None

HERE=os.path.dirname(os.path.abspath(__file__))
CFG=json.load(open(os.path.join(HERE,'config.json')))

def item_id(r):
    """Stable short id for one ledger line — used to mark it Paid / proof-submitted.
    Same inputs -> same id in the app and the portal builder."""
    key='%s|%s|%s|%s'%(r.get('category',''),r.get('date',''),r.get('vendor',''),r.get('amount',''))
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:10]

# order categories are displayed in (portal + statement) so ref numbers read top-to-bottom
DISPLAY_CATS=['Mortgage','Utilities','Pool',"Construction & Home Improvements",'Home Repairs & A/C',
    'Advances to Lindsey','School/Tuition','AT&T Business','Storage','Cleaning','Lawn/Yard',
    'Moving/Household','Labor','Medical/Dental/Vision']
def assign_refs(rows):
    """Give every counted charge a stable, human-friendly reference like C-001, in the same
    order it appears on the portal/statement (category, then vendor by share, then date)."""
    from collections import defaultdict
    pos={c:i for i,c in enumerate(DISPLAY_CATS)}
    billable=[r for r in rows if r.get('include') and r.get('in_window',True)
              and r.get('amount') is not None and r.get('her_share') is not None]
    bycat=defaultdict(list)
    for r in billable: bycat[r['category']].append(r)
    n=0
    for cat in sorted(bycat, key=lambda c: pos.get(c, 99)):
        vg=defaultdict(list)
        for r in bycat[cat]: vg[r['vendor']].append(r)
        for v in sorted(vg, key=lambda vv:-sum(x['her_share'] for x in vg[vv])):
            for r in sorted(vg[v], key=lambda x:(x.get('date') or '')):
                n+=1; r['ref']='C-%03d'%n
    return rows

def infer_venmo_dates(raw, asof_year=2026):
    """raw: list of (datestr, amt, note). Assign real dates walking newest->oldest."""
    out=[]; year=asof_year; prev_m=13
    for d,a,n in raw:
        ds=d.strip()
        # relative like '2d','15d' -> approx as of April 2026 (statement gen date)
        if re.fullmatch(r'\d+d',ds) or ds in ('Yesterday','Today') or re.fullmatch(r'\d+[wh]',ds):
            out.append(('2026-04-15',a,n,'approx')); continue
        m=re.match(r'([A-Za-z]{3})\s+(\d{1,2})(?:,\s*(\d{4}))?',ds)
        if not m:
            out.append(('',a,n,'')); continue
        mon=parsers.MONTHS.get(m.group(1).lower()[:3]); day=int(m.group(2)); yr=m.group(3)
        if yr: year=int(yr)
        else:
            if mon>prev_m: year-=1   # month increased going down list => crossed year boundary
        prev_m=mon
        out.append((f"{year}-{mon:02d}-{day:02d}",a,n,''))
    return out

def build(folder):
    rows=[]; seen_hash=set(); seen_payid=set(); seen_text=set(); seen_pool=set(); seen_studysale=set()
    files=[]
    for dp,_,fn in os.walk(folder):
        for f in fn:
            if f.lower().endswith(('.pdf','.jpg','.jpeg','.png')): files.append(os.path.join(dp,f))
    files.sort()
    study=[p for p in files if 'studyville' in os.path.basename(p).lower()]
    if study:
        for r in EX.reconcile_studyville(study, folder, EX.get_lines):
            rows.append(r)
    SUPERSEDED={'venmo _ eli pearson.pdf','venmo _ lions lawncare.pdf'}
    OWN_OUTPUT=('reimbursement_','amounts_paid_for_lindsey')   # our own generated documents
    for p in files:
        if 'studyville' in os.path.basename(p).lower():
            continue
        if os.path.basename(p).lower() in SUPERSEDED:
            continue  # replaced by full Venmo CSV statements
        if os.path.basename(p).lower().startswith(OWN_OUTPUT):
            continue  # never re-ingest documents this program generated
        rel=os.path.relpath(p,folder); base=os.path.basename(p)
        try:
            lines,src=EX.get_lines(p)
        except Exception as e:
            rows.append(dict(date='',vendor='?',category='NEEDS REVIEW',desc=f'parse error: {e}',
                             amount=None,file=rel,include=False,note='could not read')); continue
        text="\n".join(lines)
        # content-hash dedup: identical documents saved under different names
        if len(text.strip())>150:
            th=hashlib.md5(text.encode('utf-8','ignore')).hexdigest()
            if th in seen_text:
                rows.append(dict(date='',vendor='(duplicate file)',category='NEEDS REVIEW',
                    desc='Identical content to another file already counted',amount=None,file=rel,
                    include=False,note='exact-duplicate document - excluded')); continue
            seen_text.add(th)
        v=parsers.detect_vendor(p,text)
        cat=EX.CATEGORY.get(v,'NEEDS REVIEW'); vl=EX.VENDOR_LABEL.get(v,v)
        def push(date,amt,desc,note='',include=True,vendor=vl,category=cat):
            rows.append(dict(date=date,vendor=vendor,category=category,desc=desc,
                amount=(round(amt,2) if amt is not None else None),file=rel,include=include,note=note))
        if v=='atmos':      d,a,de,n=EX.ex_atmos(lines);      push(d,a,de,n)
        elif v=='entergy':  d,a,de,n=EX.ex_entergy(lines);    push(d,a,de,n)
        elif v=='brwater':
            d,a,de,n=EX.ex_brwater(lines)
            if n=='payment-confirmation':
                push(d,a,de,'payment receipt - excluded (duplicate of the billed month)',include=False)
            else: push(d,a,de,n)
        elif v=='att_internet': d,a,de,n=EX.ex_att_internet(lines); push(d,a,de,n)
        elif v=='att_business':
            d,a,de,n=EX.ex_att_business(lines)
            push(d,100.0,'Her portion of shared wireless plan (family bill)',n)
            rows[-1]['flat_share']=CFG.get('att_business_flat_per_month',100.0)
            rows[-1]['file']='(shared family wireless plan - statement available on request)'
            rows[-1]['note']=(rows[-1].get('note') or '')+' $100/mo portion per agreement'
        elif v=='pool':
            d,a,de,inv=EX.ex_pool(lines)
            JAMES_POOL={'3268','3336','2319','2383','2450','2507','2625','2698','2766','2836','2911','3008','3048','3134','3189'}
            if inv and inv in seen_pool: push(d,a,de,'duplicate invoice#',include=False)
            elif inv in JAMES_POOL:
                seen_pool.add(inv); push(d,a,de,'JAMES POOL - excluded per Ned',include=False,vendor='Pool (Fernando) — James pool')
            else: seen_pool.add(inv); push(d,a,de)
        elif v=='pods':
            d,a,de,n=EX.ex_pods(lines)
            if a is None:
                POD={'pods august 2025.pdf':('2025-07-10',304.98),'pods sept 2025.pdf':('2025-08-10',297.25),
                     'pods oct 2025.pdf':('2025-09-10',297.25),'pods oct(2) 2025.pdf':('2025-10-10',297.25),
                     'pods nov 2025.pdf':('2025-11-10',297.25),'pods dec 2025.pdf':('2025-12-10',297.25),
                     'pods jan 2026.pdf':('2026-01-10',297.25)}
                key=os.path.basename(p).lower()
                if key in POD: d,a=POD[key]; n=(n or '')+' (known amount; OCR unavailable)'
            push(d,a,de,n)
        elif v=='cleaning':
            d,a,de,n=EX.ex_cleaning(lines)
            if a is None and 'cleaning' in os.path.basename(p).lower():
                d,a=('2026-04-19',600.00); n=(n or '')+' (known amount; OCR unavailable)'
            push(d,a,de,n)
        elif v=='facts':
            d,a,de,pid=EX.ex_facts(lines)
            de='Tuition payment — paid by Gerald Pearson'
            if pid and pid in seen_payid: push(d,a,de,'duplicate FACTS payment id',include=False)
            else: seen_payid.add(pid); push(d,a,de)
        elif v=='studyville':
            pass  # handled by reconcile_studyville pre-pass
        elif v in ('venmo_lions','venmo_eli','venmo_lindsey'):
            raw=EX.ex_venmo(lines,v)
            for d,a,n,flag in infer_venmo_dates(raw):
                note=n+(' | '+flag if flag else '')
                push(d,a,(n or ('Advance to Lindsey' if v=='venmo_lindsey' else 'Payment to '+vl)),note,include=True)
        else:
            # unknown: capture biggest $ as a guess, mark for review
            m=re.findall(r'\$?([\d,]+\.\d{2})',text)
            guess=max((float(x.replace(',','')) for x in m),default=None) if m else None
            push('',guess,'UNRECOGNIZED - please categorize','auto-detect failed',include=False,
                 vendor='?',category='NEEDS REVIEW')
    # ----- Venmo CSV statements -----
    try:
        rows.extend(venmo_csv.parse(folder))
    except Exception as _e:
        pass
    # ----- bills found in Gmail (not in folder) -----
    try:
        rows.extend(email_bills.merge(rows))
    except Exception:
        pass
    # ----- manual entries (no PDF in folder), e.g. mortgage -----
    for me in CFG.get('manual_entries',[]):
        rec=me.get('recurring_monthly')
        if rec:
            sched=me.get('amount_schedule')
            def _amt_for(ym):
                if sched:
                    for seg in sched:
                        if seg['start']<=ym<=seg['end']: return float(seg['amount'])
                return float(me['amount'])
            sy,sm=map(int,rec['start'].split('-')); ey,em=map(int,rec['end'].split('-'))
            y,m=sy,sm
            while (y,m)<=(ey,em):
                ym=f"{y:04d}-{m:02d}"
                rows.append(dict(date=f"{ym}-01",vendor=me['vendor'],category=me['category'],
                    desc=me['description'],amount=round(_amt_for(ym),2),
                    file=me.get('source','(from Assurance payment notices - email)'),
                    include=True,note=me.get('note','mortgage (actual)')))
                m+=1
                if m>12: m=1; y+=1
        else:
            row=dict(date=me.get('date',''),vendor=me['vendor'],category=me['category'],
                desc=me['description'],amount=round(float(me['amount']),2),
                file=me.get('source','(manual entry - config.json)'),include=True,note='manual')
            if me.get('flat_share') is not None: row['flat_share']=float(me['flat_share'])
            rows.append(row)
    return rows

def apply_split(rows):
    sp=CFG['split_percent']; cutoff=CFG.get('date_cutoff')
    for r in rows:
        # a row with no date AND no amount is unusable — send to Review, never the claim
        if r.get('include') and not r.get('date') and not r.get('amount') and r.get('flat_share') is None:
            r['include']=False
            r['note']=((r.get('note') or '')+' | no date/amount readable - moved to Review').strip(' |')
        if cutoff and r['date'] and r['date']<cutoff:
            r['in_window']=False
        else:
            r['in_window']=True
        pct=sp.get(r['category'])
        r['pct']=pct
        _ae=CFG.get('att_business_end')
        if _ae and r['category']=='AT&T Business' and r.get('date') and r['date'][:7]>_ae:
            r['in_window']=False; r['note']=(r.get('note') or '')+f' | after AT&T end {_ae}'
        billable = r['include'] and r['in_window'] and r['amount'] is not None and pct is not None
        from decimal import Decimal, ROUND_HALF_UP
        def _m(v): return float(Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        if r.get('flat_share') is not None:
            r['her_share']=_m(r['flat_share']) if billable else 0.0
        else:
            r['her_share']=_m(r['amount']*pct/100) if billable else 0.0
    return rows

def generate(folder, outdir=None, progress=None):
    """Build everything. Returns dict with rows, net, subtotal, credits, summary_lines, files."""
    global CFG
    CFG=json.load(open(os.path.join(HERE,'config.json')))
    outdir=outdir or HERE
    os.makedirs(outdir,exist_ok=True)
    def say(m):
        if progress: progress(m)
    try:                                   # safety net: snapshot the prior data state first
        import backup
        sid=backup.snapshot(note='auto — before generate', auto=True)
        if sid: say("Backup saved (archive): %s"%sid)
    except Exception as _be:
        say("(backup skipped: %s)"%_be)
    say("Reading bills in: "+folder)
    rows=apply_split(build(folder))
    assign_refs(rows)
    say("Categorized %d line items."%len(rows))
    from safewrite import write_via_temp, write_text
    cols=['ref','date','vendor','category','desc','amount','pct','her_share','include','in_window','note','file']
    def _wcsv(tmp):
        with open(tmp,'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
            for r in sorted(rows,key=lambda x:(x['category'],x['date'] or '')): w.writerow({k:r.get(k) for k in cols})
    write_via_temp(os.path.join(outdir,'ledger.csv'),_wcsv,say)
    write_via_temp(os.path.join(outdir,'ledger.json'),
                   lambda tmp: json.dump(rows,open(tmp,'w',encoding='utf-8'),indent=1),say)
    from collections import defaultdict
    bycat=defaultdict(lambda:[0,0.0,0.0]); credits=0.0
    for r in rows:
        if r['vendor']=='Paid TO Lindsey' and r['amount'] and (not CFG.get('date_cutoff') or not r['date'] or r['date']>=CFG['date_cutoff']):
            credits+=r['amount']
        if r['her_share']:
            bycat[r['category']][0]+=1; bycat[r['category']][1]+=r['amount']; bycat[r['category']][2]+=r['her_share']
    subtotal=sum(v[2] for v in bycat.values())
    credit_applied=credits if CFG.get('subtract_payments_to_lindsey') else 0.0
    net=subtotal-credit_applied
    lines=["REIMBURSEMENT SUMMARY  (generated %s)"%_dt.date.today().isoformat(),"="*60]
    for c in sorted(bycat):
        n,amt,her=bycat[c]
        lines.append(f"{c:22s} {n:3d} items  billed ${amt:11,.2f}  @{CFG['split_percent'].get(c)}%  -> ${her:11,.2f}")
    lines.append("-"*60)
    lines.append(f"{'SUBTOTAL she owes':22s}                                 -> ${subtotal:12,.2f}")
    if CFG.get('subtract_payments_to_lindsey'):
        lines.append(f"{'LESS credits paid':22s}                                 -> -${credit_applied:11,.2f}")
    lines.append("="*60)
    lines.append(f"{'NET LINDSEY OWES YOU':22s}                                 -> ${net:12,.2f}")
    write_text(os.path.join(outdir,'summary.txt'),"\n".join(lines),say)
    files={'csv':os.path.join(outdir,'ledger.csv')}
    # Excel — built in a temp file, swapped in; if the workbook is open in Excel
    # the previous version is kept and the user is told to close it.
    if report is not None:
        try:
            xlsx=os.path.join(outdir,'Reimbursement_Breakdown.xlsx')
            def _wxlsx(tmp):
                report.build_workbook(rows,tmp); _try_recalc(tmp)
            if write_via_temp(xlsx,_wxlsx,say):
                say("Built Excel workbook.")
            files['xlsx']=xlsx
        except Exception as e: say("Excel build failed: %s"%e)
    # PDF
    try:
        import report_pdf
        pdf=os.path.join(outdir,'Reimbursement_Statement.pdf')
        if write_via_temp(pdf,lambda tmp: report_pdf.build_pdf(rows,CFG,tmp),say):
            say("Built PDF statement.")
        files['pdf']=pdf
    except Exception as e: say("PDF build failed: %s"%e)
    say("Done. Net Lindsey owes: $%,.2f"%net if False else "Done.")
    return dict(rows=rows,net=net,subtotal=subtotal,credits=credit_applied,summary_lines=lines,files=files)

def _try_recalc(xlsx):
    import subprocess
    rc=os.path.join(HERE,'recalc.py')
    if os.path.exists(rc):
        try: subprocess.run([sys.executable,rc,xlsx],timeout=120,capture_output=True)
        except Exception: pass

def main():
    folder=sys.argv[1] if len(sys.argv)>1 else '.'
    res=generate(folder)
    print("\n".join(res['summary_lines']))
    print("\nOutputs:",", ".join(os.path.basename(v) for v in res['files'].values()))

if __name__=='__main__':
    main()
