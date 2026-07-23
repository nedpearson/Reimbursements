#!/usr/bin/env python3
"""Rebuild the live web portal (docs/) from current data: interactive drill-down page
+ compressed proof volumes + statement/cover letter. Run after Generate, before publishing."""
import os, sys, json, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import categorize
from parsers import _decode_html_embedded_pdf
import fitz

def _wrap(s, n):
    out=[]; line=''
    for w in str(s).split():
        if len(line)+len(w)+1>n: out.append(line); line=w
        else: line=(line+' '+w).strip()
    if line: out.append(line)
    return out or ['']

def _origin_of(r):
    """(origin sentence, availability sentence) for a source-record page."""
    f=str(r.get('file','')); note=(r.get('note') or ''); cat=r.get('category',''); desc=(r.get('desc') or '').lower()
    if 'return' in desc or 'nsf' in desc or 'returned-check' in desc:
        return ("Returned-check / NSF fees charged on the mortgage account (lender notice on file).",
                "The lender's returned-check notice is on file and available on request.")
    if cat=='Mortgage' or 'mortgage' in note or f.startswith('(from Assurance'):
        return ("Assurance Financial mortgage payment notification for this month (lender payment email/statement for account on file, property 8792 W Fairway Dr).",
                "The full monthly statement is available directly from Assurance Financial on request.")
    if cat=='AT&T Business' or r.get('flat_share') is not None:
        return ("Lindsey's agreed flat $100/month portion of the shared family wireless plan (multi-line AT&T account).",
                "The underlying AT&T statement is available on request.")
    if 'Venmo' in f or f.lower().endswith('.csv') or 'venmo' in note.lower():
        return ("Recorded from the official Venmo monthly statement — payment involving %s."%(r.get('vendor') or 'this vendor'),
                "The full Venmo statement showing this line is available on request.")
    if f.startswith('(from Gmail') or 'email' in note.lower():
        return ("Recorded from the biller's own bill/statement email (%s) in Gerald Pearson's email records."%(r.get('vendor') or 'biller'),
                "The original email/PDF for this month is available on request.")
    import re as _re
    m=_re.search(r'invoice #?\s*(\w+)',desc)
    if m or 'invoice' in desc or 'receipt' in desc:
        return ("Recorded from the vendor's written invoice/receipt from %s%s."%(r.get('vendor') or 'the vendor',(' (invoice #%s)'%m.group(1)) if m else ''),
                "The signed invoice/receipt is on file and available on request.")
    return ("Agreed amount recorded per the parties for this item.",
            "Supporting detail is available on request.")

def _origin_short(r):
    f=str(r.get('file','')); cat=r.get('category','')
    if cat=='Mortgage': return 'Assurance mortgage payment notice'
    if cat=='AT&T Business' or r.get('flat_share') is not None: return 'AT&T shared-plan portion'
    if 'Venmo' in f or f.lower().endswith('.csv'): return 'Venmo statement'
    if f.startswith('(from Gmail'): return 'Biller email/statement'
    d=(r.get('desc') or '').lower()
    if 'invoice' in d or 'receipt' in d: return 'Vendor invoice/receipt'
    return 'Agreed amount'

def _draw_source_record(body, exh, cat, r):
    import fitz, datetime as _d
    NAVY=(0.12,0.22,0.39); GREY=(0.4,0.4,0.4)
    pg=body.new_page(width=612,height=792)
    def T(x,y,s,size=10,color=(0,0,0),bold=False):
        pg.insert_text((x,y),str(s),fontsize=size,color=color,fontname=('hebo' if bold else 'helv'))
    T(40,60,'SOURCE RECORD',size=17,color=NAVY,bold=True)
    pg.draw_line((40,72),(572,72),color=NAVY,width=1.2)
    T(40,98,'Exhibit %d — %s'%(exh,cat),size=12,color=NAVY,bold=True)
    y=132
    def money(v): return '$%s'%format(v,',.2f')
    for k,v in [('Date',r.get('date') or '—'),('Payee / vendor',r.get('vendor') or ''),
                ('Amount billed',money(r['amount'])),("Lindsey's share",money(r['her_share']))]:
        T(40,y,k+':',size=10,color=GREY,bold=True); T(190,y,v,size=10); y+=22
    T(40,y,'Description:',size=10,color=GREY,bold=True)
    dlines=_wrap(r.get('desc') or '',62)
    for j,ln in enumerate(dlines[:3]): T(190,y+j*15,ln,size=10)
    y+=22+max(0,len(dlines[:3])-1)*15
    y+=10
    origin,avail=_origin_of(r)
    T(40,y,'Origin of this figure',size=10.5,color=NAVY,bold=True); y+=18
    for ln in _wrap(origin,92): T(40,y,ln,size=10); y+=15
    y+=8
    for ln in _wrap(avail,92): T(40,y,ln,size=9,color=GREY); y+=13
    T(40,760,'Gerald "Ned" Pearson Jr.  ·  Pearson v. Pearson, No. 236951, Family Court, East Baton Rouge Parish, LA',size=7.5,color=(0.5,0.5,0.5))
    T(40,772,'Source record prepared %s. This documents the origin of the amount; the underlying bill/statement is available on request.'%_d.date.today().strftime('%B %d, %Y'),size=7.5,color=(0.5,0.5,0.5))

def build(bills_folder=None, progress=print):
    cfg=json.load(open(os.path.join(HERE,'config.json')))
    bills_folder=bills_folder or cfg.get('last_folder')
    docs=os.path.join(HERE,'docs'); proof=os.path.join(docs,'proof')
    os.makedirs(proof,exist_ok=True)
    res=categorize.generate(bills_folder,outdir=os.path.join(HERE,'output'),progress=progress)
    rows=res['rows']
    try:
        import exports
        exports.export_all(rows,cfg,bills_folder,os.path.join(HERE,'output'),progress=progress)
    except Exception as _e:
        progress('exports refresh skipped: %s'%_e)
    # ---- proof volumes ----
    catorder=[]; files=[]; seen=set()
    for r in rows:
        if r['category'] not in catorder: catorder.append(r['category'])
    for cat in catorder:
        for r in rows:
            f=str(r.get('file',''))
            if r['include'] and r.get('in_window',True) and r['category']==cat and f and not f.startswith('(') and not f.lower().endswith('.csv'):
                if f not in seen: seen.add(f); files.append((cat,f))
    body=fitz.open(); mapping={}; exh=0
    for cat,rel in files:
        path=os.path.join(bills_folder,rel)
        if not os.path.exists(path): continue
        try:
            if rel.lower().endswith(('.png','.jpg','.jpeg')):
                src=fitz.open('pdf',fitz.open(path).convert_to_pdf())
            else:
                try:
                    src=fitz.open(path)
                    if len(src)==0 or (src[0].rect.width==400 and not src[0].get_text().strip()): raise ValueError
                except Exception:
                    real=_decode_html_embedded_pdf(path)
                    if not real: continue
                    src=fitz.open(real)
            exh+=1; mapping[rel]=dict(exh=exh,cat=cat,page=body.page_count+1,base=os.path.basename(rel))
            for pi in range(min(2,len(src))):
                pix=src[pi].get_pixmap(dpi=88); jpg=pix.tobytes('jpeg',jpg_quality=38)
                pg=body.new_page(width=612,height=792)
                pg.insert_image(fitz.Rect(20,32,592,772),stream=jpg,keep_proportion=True)
                pg.insert_text((20,22),f"Exhibit {exh} | {cat} | {os.path.basename(rel)} (p.{pi+1})",fontsize=7,color=(.35,.35,.35))
        except Exception as e: progress(f"portal: skip {rel}: {e}")
    # ---- source-record exhibits: one page for every included line WITHOUT a file bill
    # (mortgage notices, email-sourced utility months, Venmo advances, agreed amounts) so
    # every "source of truth" on the portal opens a real document. ----
    mapping_id={}
    for cat in catorder:
        for r in rows:
            if not (r['include'] and r.get('in_window',True) and r.get('amount') is not None and r.get('her_share') is not None): continue
            if r['category']!=cat: continue
            f=str(r.get('file',''))
            if f in mapping: continue          # already shown as an actual bill exhibit
            rid=categorize.item_id(r)
            if rid in mapping_id: continue
            exh+=1
            mapping_id[rid]=dict(exh=exh,cat=cat,page=body.page_count+1,doc=_origin_short(r))
            _draw_source_record(body,exh,cat,r)
    tmp=os.path.join(docs,'_wp.pdf'); body.save(tmp,deflate=True,garbage=4)
    sz=os.path.getsize(tmp)/1e6; full=fitz.open(tmp); n=full.page_count
    per=max(1,int(n*2.2/sz)) if sz else n; volmap={}; volno=0; p=0
    for old in os.listdir(proof):
        if old.startswith('vol'):
            try: os.remove(os.path.join(proof,old))
            except OSError: pass   # open somewhere; will be overwritten via temp-swap below
    from safewrite import write_via_temp
    while p<n:
        volno+=1; end=min(n,p+per); v=fitz.open(); v.insert_pdf(full,from_page=p,to_page=end-1)
        write_via_temp(os.path.join(proof,f'vol{volno}.pdf'),
                       lambda tmp,_v=v: _v.save(tmp,deflate=True),progress)
        for gp in range(p+1,end+1): volmap[gp]=(volno,gp-p)
        p=end
    full.close(); os.remove(tmp)
    fin={rel:dict(exh=m['exh'],cat=m['cat'],vol=volmap[m['page']][0],page=volmap[m['page']][1],base=m['base']) for rel,m in mapping.items()}
    fin_id={rid:dict(exh=m['exh'],cat=m['cat'],vol=volmap[m['page']][0],page=volmap[m['page']][1],doc=m['doc']) for rid,m in mapping_id.items()}
    # ---- portal data ----
    CATS=['Mortgage','Utilities','Pool',"Construction & Home Improvements",'Home Repairs & A/C','Advances to Lindsey','School/Tuition','AT&T Business','Storage','Cleaning','Lawn/Yard','Moving/Household','Labor','Medical/Dental/Vision']
    items=[]; credits=[]
    for r in rows:
        if r['vendor']=='Paid TO Lindsey' and r.get('amount'):
            credits.append(dict(d=r.get('date',''),desc=r.get('desc') or 'Payment to Lindsey',a=r['amount'])); continue
        if not (r['include'] and r.get('in_window',True) and r.get('amount') is not None and r.get('her_share') is not None): continue
        f=str(r.get('file',''))
        rid=categorize.item_id(r)
        if f in fin: m=fin[f]; src=dict(t='exh',exh=m['exh'],vol=m['vol'],pg=m['page'],doc=m['base'],rec=False)
        elif rid in fin_id: m=fin_id[rid]; src=dict(t='exh',exh=m['exh'],vol=m['vol'],pg=m['page'],doc=m['doc'],rec=True)
        else: src=dict(t='manual',doc='Agreed amount' if not r.get('flat_share') else 'Agreed portion')
        items.append(dict(cat=r['category'],d=r.get('date',''),v=r['vendor'],desc=(r.get('desc') or '')[:70],a=r['amount'],h=r['her_share'],src=src,id=rid))
    cats={}
    for it in items:
        c=cats.setdefault(it['cat'],dict(n=0,billed=0.0,owed=0.0)); c['n']+=1; c['billed']+=it['a']; c['owed']+=it['h']
    data=dict(updated=__import__('datetime').date.today().strftime('%B %d, %Y'),
        net=round(sum(i['h'] for i in items)-(sum(c['a'] for c in credits) if cfg.get('subtract_payments_to_lindsey') else 0.0),2),
        credit_total=round(sum(c['a'] for c in credits),2),
        cats=[dict(name=c,**{k:(round(v,2) if isinstance(v,float) else v) for k,v in cats[c].items()},
              basis=('flat $100/mo' if c=='AT&T Business' else ('12%' if c in ('School/Tuition','Medical/Dental/Vision') else ('100%' if c=='Advances to Lindsey' else ('80%' if c=='Moving/Household' else '50%'))))) for c in CATS if c in cats],
        items=items, credits=sorted(credits,key=lambda x:x['d']))
    tpl=open(os.path.join(HERE,'portal_template.html'),encoding='utf-8').read()
    addl={}
    ap=os.path.join(HERE,'additional.json')
    if os.path.exists(ap):
        addl=json.load(open(ap,encoding='utf-8'))
    subtract=bool(cfg.get('subtract_payments_to_lindsey'))
    tpl=tpl.replace('__CREDITNOTE__', ('after $__CREDITS__ already paid to Lindsey is credited' if subtract else 'includes the direct payments/advances Ned made to Lindsey — see the Advances category below'))
    tpl=tpl.replace('__CREDITSTITLE__', ('Credits — amounts Ned already paid Lindsey (subtracted)' if subtract else 'Payments Ned made to Lindsey — settled separate expenses (NOT subtracted)'))
    disputes={'items':[]}
    dp=os.path.join(HERE,'disputes.json')
    if os.path.exists(dp):
        try:
            _d=json.load(open(dp,encoding='utf-8'))
            disputes={'items':[i for i in _d.get('items',[]) if i.get('item')]}
        except Exception as _e:
            progress('disputes.json unreadable, skipping: %s'%_e)
    paidback={'payments':[],'total':0.0}
    pb=os.path.join(HERE,'paidback.json')
    if os.path.exists(pb):
        try:
            _p=json.load(open(pb,encoding='utf-8'))
            pays=[x for x in _p.get('payments',[]) if x.get('amount')]
            paidback={'payments':pays,'total':round(sum(float(x['amount']) for x in pays),2)}
        except Exception as _e:
            progress('paidback.json unreadable, skipping: %s'%_e)
    # ---- per-line settled status (Ned-controlled paid + pending proof) ----
    settled={'paid':[],'pending':[]}
    st=os.path.join(HERE,'settled.json')
    if os.path.exists(st):
        try:
            _s=json.load(open(st,encoding='utf-8'))
            settled={'paid':list(_s.get('paid',[])),'pending':[i for i in _s.get('pending',[]) if i not in set(_s.get('paid',[]))]}
        except Exception as _e:
            progress('settled.json unreadable, skipping: %s'%_e)
    paidset=set(settled['paid'])
    settled['paid_total']=round(sum(i['h'] for i in items if i['id'] in paidset),2)
    settled['paid_count']=sum(1 for i in items if i['id'] in paidset)
    settled['item_count']=len(items)
    form_email=str(cfg.get('form_email') or 'nedpearson@gmail.com')
    html=tpl.replace('__DATA__',json.dumps(data,separators=(',',':'))).replace('__ADDITIONAL__',json.dumps(addl,separators=(',',':'))).replace('__DISPUTES__',json.dumps(disputes,separators=(',',':'))).replace('__PAIDBACK__',json.dumps(paidback,separators=(',',':'))).replace('__SETTLED__',json.dumps(settled,separators=(',',':'))).replace('__FORM_EMAIL__',form_email).replace('__NET__',format(data['net'],',.2f')).replace('__CREDITS__',format(data['credit_total'],',.2f')).replace('__UPDATED__',data['updated'])
    from safewrite import write_text, copy_file
    # .nojekyll: serve the docs/ folder exactly as-is (skip GitHub's Jekyll build,
    # which can fail on large sites and take the whole page down with a 404).
    try: open(os.path.join(docs,'.nojekyll'),'w').close()
    except Exception: pass
    write_text(os.path.join(docs,'index.html'),html,progress)
    try:
        import make_additional_pdf
        make_additional_pdf.build()          # keep the chart in sync with additional.json
    except Exception as _e:
        progress('additional chart rebuild skipped: %s'%_e)
    ac=os.path.join(HERE,'Amounts_Paid_For_Lindsey.pdf')
    if os.path.exists(ac): copy_file(ac,os.path.join(docs,'Amounts_Paid_For_Lindsey.pdf'),progress)
    for fn in ('Reimbursement_Statement.pdf','Reimbursement_Cover_Letter.pdf'):
        s=os.path.join(HERE,'output',fn)
        if os.path.exists(s): copy_file(s,os.path.join(docs,fn),progress)
    progress(f"Portal rebuilt: {len(items)} items, {exh} exhibits, {volno} proof volumes, net ${data['net']:,.2f}")
    return data['net']

if __name__=='__main__':
    build()
