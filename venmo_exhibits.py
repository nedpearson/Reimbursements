"""Turn each Venmo-statement-backed ledger line into a real exhibit: the official monthly
Venmo statement (CSV) rendered as a PDF with the matching transaction highlighted.
Writes <House Bills>/_sources/Venmo/<statement>_<ref>.pdf and registers it in config
line_sources. Run after categorize/build so output/ledger.json is current; then rebuild."""
import os, csv, json, re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
HERE=os.path.dirname(os.path.abspath(__file__))
cfg=json.load(open(os.path.join(HERE,'config.json'),encoding='utf-8'))
folder=cfg['last_folder']; out=os.path.join(folder,'_sources','Venmo'); os.makedirs(out,exist_ok=True)
rows=json.load(open(os.path.join(HERE,'output','ledger.json'),encoding='utf-8'))
ls=cfg.setdefault('line_sources',[]); have={(x['vendor'],x['date'],round(float(x['amount']),2)) for x in ls}
styles=getSampleStyleSheet(); S=lambda **k: ParagraphStyle('x',parent=styles['Normal'],**k)
added=0
for r in rows:
    f=str(r.get('file','')); 
    if not (r.get('her_share') and f.lower().endswith('.csv')): continue
    key=(r['vendor'],r['date'],round(float(r['amount']),2))
    if key in have: continue
    path=os.path.join(folder,f)
    data=list(csv.reader(open(path,encoding='utf-8-sig')))
    hdr_i=next(i for i,row in enumerate(data) if 'Datetime' in row)
    hdr=data[hdr_i]; body=[row for row in data[hdr_i+1:] if len(row)>8 and row[2]]
    keep=['Datetime','Type','Status','Note','From','To','Amount (total)','Funding Source']
    idx=[hdr.index(k) for k in keep]
    tbl=[keep]; hit=None
    for row in body:
        rec=[row[i] for i in idx]
        amt=abs(float(re.sub(r'[^\d.]','',rec[6]) or 0))
        if rec[0][:10]==r['date'] and abs(amt-float(r['amount']))<0.01 and hit is None: hit=len(tbl)
        rec[0]=rec[0].replace('T',' ')[:16]; tbl.append([Paragraph(str(c)[:60],S(fontSize=7,leading=8.5)) for c in rec])
    pdf=os.path.join(out,os.path.splitext(os.path.basename(f))[0].replace(' ','_')+'_'+r['ref']+'.pdf')
    doc=SimpleDocTemplate(pdf,pagesize=landscape(letter),leftMargin=0.5*inch,rightMargin=0.5*inch,topMargin=0.6*inch,bottomMargin=0.5*inch)
    E=[Paragraph(data[0][0].strip(' ,'),S(fontName='Helvetica-Bold',fontSize=12)),
       Paragraph(f"Official Venmo monthly statement (export: {os.path.basename(f)}). Highlighted row = line {r['ref']}: {r['vendor']} {r['date']} ${float(r['amount']):,.2f} — {r.get('desc','')}",S(fontSize=8.5,leading=11)),Spacer(1,6)]
    t=Table(tbl,colWidths=[1.0*inch,0.65*inch,0.6*inch,2.3*inch,0.95*inch,1.1*inch,0.85*inch,2.4*inch],repeatRows=1)
    st=[('FONTSIZE',(0,0),(-1,-1),7),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1F3864')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.25,colors.HexColor('#CCCCCC')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),1.5),('BOTTOMPADDING',(0,0),(-1,-1),1.5)]
    if hit: st+=[('BACKGROUND',(0,hit),(-1,hit),colors.HexColor('#FFF3B0')),('BOX',(0,hit),(-1,hit),1.2,colors.HexColor('#C0392B'))]
    t.setStyle(TableStyle(st)); E.append(t); doc.build(E)
    ls.append({'vendor':r['vendor'],'date':r['date'],'amount':float(r['amount']),'file':'_sources/Venmo/'+os.path.basename(pdf)}); have.add(key); added+=1
    print(r['ref'],'->',os.path.basename(pdf),'(row found)' if hit else '(ROW NOT FOUND - check)')
json.dump(cfg,open(os.path.join(HERE,'config.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
print('added',added)
