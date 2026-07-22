#!/usr/bin/env python3
"""Rebuild the live web portal (docs/) from current data: interactive drill-down page
+ compressed proof volumes + statement/cover letter. Run after Generate, before publishing."""
import os, sys, json, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import categorize
from parsers import _decode_html_embedded_pdf
import fitz

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
    # ---- portal data ----
    CATS=['Mortgage','Utilities','Pool',"Construction (De Roman's)",'Home Repairs & A/C','Advances to Lindsey','School/Tuition','AT&T Business','Storage','Cleaning','Lawn/Yard','Moving/Household','Labor','Medical/Dental/Vision']
    items=[]; credits=[]
    for r in rows:
        if r['vendor']=='Paid TO Lindsey' and r.get('amount'):
            credits.append(dict(d=r.get('date',''),desc=r.get('desc') or 'Payment to Lindsey',a=r['amount'])); continue
        if not (r['include'] and r.get('in_window',True) and r.get('amount') is not None and r.get('her_share') is not None): continue
        f=str(r.get('file',''))
        if f in fin: m=fin[f]; src=dict(t='exh',exh=m['exh'],vol=m['vol'],pg=m['page'])
        elif 'mortgage' in (r.get('note') or '') or f.startswith('(from Assurance'): src=dict(t='email',doc='Assurance payment notice (email)')
        elif f.startswith('(from Gmail'): src=dict(t='email',doc='Bill from email records')
        elif 'Venmo' in f or f.lower().endswith('.csv'): src=dict(t='venmo',doc='Venmo statement')
        else: src=dict(t='manual',doc='Agreed amount' if not r.get('flat_share') else 'Agreed portion')
        items.append(dict(cat=r['category'],d=r.get('date',''),v=r['vendor'],desc=(r.get('desc') or '')[:70],a=r['amount'],h=r['her_share'],src=src))
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
    html=tpl.replace('__DATA__',json.dumps(data,separators=(',',':'))).replace('__ADDITIONAL__',json.dumps(addl,separators=(',',':'))).replace('__NET__',format(data['net'],',.2f')).replace('__CREDITS__',format(data['credit_total'],',.2f')).replace('__UPDATED__',data['updated'])
    from safewrite import write_text, copy_file
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
