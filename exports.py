"""Document exports: cover letter, proof pack, print package. Pure Python (reportlab + pymupdf)."""
import os, json, datetime as _dt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable)

NAVY=colors.HexColor('#1F3864'); GREEN=colors.HexColor('#2E7D32'); GREY=colors.HexColor('#606060')
LIGHT=colors.HexColor('#D9E1F2'); ROWALT=colors.HexColor('#F4F6FB')
def _S(styles,name,**k):
    k.setdefault('fontName','Times-Roman'); return ParagraphStyle(name,parent=styles['Normal'],**k)
def _money(v): return "${:,.2f}".format(v)

def category_rollup(rows,cfg):
    sp=cfg.get('split_percent',{})
    cats={}
    for r in rows:
        if not r.get('her_share') and not (r['include'] and r.get('in_window',True)): continue
        if r['vendor']=='Paid TO Lindsey': continue
        if r['include'] and r.get('in_window',True) and r.get('amount') is not None and r['category'] in sp:
            c=cats.setdefault(r['category'],[0,0.0,0.0])
            c[0]+=1; c[1]+=r['amount']; c[2]+=r.get('her_share') or 0.0
    order=[c for c in sp if c in cats]
    subtotal=sum(v[2] for v in cats.values())
    credits=sum(r['amount'] for r in rows if r['vendor']=='Paid TO Lindsey' and r.get('amount')) \
            if cfg.get('subtract_payments_to_lindsey') else 0.0
    return cats,order,subtotal,credits,subtotal-credits

def build_cover_letter(rows,cfg,out,today=None):
    today=today or _dt.date.today().strftime('%B %d, %Y')
    cats,order,subtotal,credits,net=category_rollup(rows,cfg)
    styles=getSampleStyleSheet()
    body=_S(styles,'b',fontSize=11,leading=15)
    small=_S(styles,'sm',fontSize=9,textColor=GREY,leading=12)
    doc=SimpleDocTemplate(out,pagesize=letter,topMargin=0.9*inch,bottomMargin=0.9*inch,
                          leftMargin=1.0*inch,rightMargin=1.0*inch,title='Reimbursement Cover Letter')
    E=[]
    E.append(Paragraph('<b>Gerald "Ned" Pearson Jr.</b>',_S(styles,'nm',fontSize=14)))
    E.append(Paragraph('8792 W Fairway Drive, Baton Rouge, LA 70809 · nedpearson@gmail.com',small))
    E.append(Spacer(1,14)); E.append(Paragraph(today,body)); E.append(Spacer(1,8))
    E.append(Paragraph('Lindsey Pearson',body))
    E.append(Paragraph('<b>Re: Reimbursement of shared household and child-related expenses</b>',body))
    E.append(Paragraph('Matter: Pearson v. Pearson, No. 236951 Div. A, Family Court, Parish of East Baton Rouge',small))
    E.append(Spacer(1,10))
    E.append(Paragraph('Dear Lindsey,',body))
    E.append(Paragraph('Enclosed is a complete accounting of the household and child-related expenses I have paid, '
      'together with the share of each category that is yours under our agreement and the Interim Consent Judgment '
      'dated January 10, 2025. Household costs are divided equally; school, tuition, and the children’s medical, '
      'dental, vision, tuition, and school costs are set at twelve percent (12%) — the share ordered by the '
      'Consent Judgment, corresponding to your 11.34% share of combined income on the Child Support Worksheet (Exhibit B).',body))
    data=[['Category','Total Paid','Share','Amount Owed']]
    sp=cfg['split_percent']
    for c in order:
        n,amt,her=cats[c]
        share=('flat $100/mo' if c=='AT&T Business' else f"{sp[c]:.0f}%")
        data.append([c,_money(amt),share,_money(her)])
    data.append(['Subtotal',_money(sum(v[1] for v in cats.values())),'',_money(subtotal)])
    if cfg.get('subtract_payments_to_lindsey'):
        data.append(['Less: amounts already paid to you','','','( '+_money(credits)+' )'])
    data.append(['NET AMOUNT DUE','','',_money(net)])
    cw=[3.3*inch,1.2*inch,0.95*inch,1.15*inch]
    t=Table(data,colWidths=cw)
    n=len(data)
    t.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),8.5),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
      ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
      ('ALIGN',(1,0),(-1,-1),'RIGHT'),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#BFBFBF')),
      ('TOPPADDING',(0,0),(-1,-1),3.5),('BOTTOMPADDING',(0,0),(-1,-1),3.5),
      ('ROWBACKGROUNDS',(0,1),(-1,n-4),[colors.white,ROWALT]),
      ('BACKGROUND',(0,n-3),(-1,n-3),LIGHT),('FONTNAME',(0,n-3),(-1,n-3),'Helvetica-Bold'),
      ('BACKGROUND',(0,n-1),(-1,n-1),GREEN),('TEXTCOLOR',(0,n-1),(-1,n-1),colors.white),
      ('FONTNAME',(0,n-1),(-1,n-1),'Helvetica-Bold')]))
    E.append(Spacer(1,6)); E.append(t); E.append(Spacer(1,10))
    E.append(Paragraph('Every figure is drawn from a source document. The enclosed statement itemizes each charge by date, '
      'and the proof pack reproduces the underlying bills. Utility amounts use current charges rather than past-due '
      'balances so no month is counted twice; duplicates were removed; direct payments I made to you during this period are included as advances to be repaid. Court-ordered child support (Consent Judgment of January 12, 2025; guideline worksheet $1,011.95 per month) was additionally paid through May 1, 2026, and direct support I provided to our son Eli (approximately $7,700) is likewise not claimed. '
      'The original of any bill is available on request.',body))
    E.append(Paragraph('Please review the enclosed statement and let me know within thirty (30) days how you would like '
      'to arrange payment or discuss any item. I am open to a payment schedule.',body))
    E.append(Spacer(1,16)); E.append(Paragraph('Sincerely,',body)); E.append(Spacer(1,28))
    E.append(Paragraph('Gerald "Ned" Pearson Jr.',body)); E.append(Spacer(1,10))
    E.append(Paragraph('Enclosures: Expense Reimbursement Statement; Proof Pack (source bills)',small))
    doc.build(E)
    return out

def build_proof_pack(rows,bills_folder,out,progress=None):
    import fitz
    from reportlab.platypus import SimpleDocTemplate
    say=progress or (lambda m:None)
    files=[]; seen=set()
    order=[r['category'] for r in rows]
    catorder=[]
    for r in rows:
        if r['category'] not in catorder: catorder.append(r['category'])
    for cat in catorder:
        for r in rows:
            if r['include'] and r.get('in_window',True) and r['category']==cat and r.get('file') \
               and not str(r['file']).startswith('(') and not str(r['file']).lower().endswith('.csv'):
                if r['file'] not in seen: seen.add(r['file']); files.append((cat,r['file']))
    body=fitz.open(); index=[]; exh=0
    for cat,rel in files:
        path=os.path.join(bills_folder,rel)
        if not os.path.exists(path): continue
        try:
            if rel.lower().endswith(('.png','.jpg','.jpeg')):
                img=fitz.open(path); src=fitz.open('pdf',img.convert_to_pdf())
            else:
                try:
                    src=fitz.open(path)
                    if len(src)==0: raise ValueError('empty')
                    if src[0].rect.width==400 and not src[0].get_text().strip():
                        raise ValueError('html-wrapped')
                except Exception:
                    from parsers import _decode_html_embedded_pdf
                    real=_decode_html_embedded_pdf(path)
                    if not real: continue
                    src=fitz.open(real)
            exh+=1; index.append((exh,cat,os.path.basename(rel),body.page_count+1))
            for pi in range(min(2,len(src))):
                pix=src[pi].get_pixmap(dpi=110)
                jpg=pix.tobytes('jpeg',jpg_quality=60)
                pg=body.new_page(width=612,height=792)
                pg.insert_image(fitz.Rect(18,30,594,774),stream=jpg,keep_proportion=True)
                pg.insert_text((18,20),f"Exhibit {exh}  |  {cat}  |  {os.path.basename(rel)} (p.{pi+1})",
                               fontsize=7,color=(0.35,0.35,0.35))
        except Exception as e:
            say(f"proof: skipped {rel}: {e}")
    # index page
    styles=getSampleStyleSheet()
    E=[Paragraph("Exhibit Index — Source Documents",
        ParagraphStyle('t',parent=styles['Normal'],fontName='Helvetica-Bold',fontSize=16,textColor=NAVY)),
       Spacer(1,8)]
    data=[['Ex.','Category','Document','Pack page']]+[[str(e),c,f[:58],str(p)] for e,c,f,p in index]
    t=Table(data,colWidths=[0.45*inch,1.55*inch,4.1*inch,0.8*inch],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
      ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),6.8),
      ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
      ('TOPPADDING',(0,0),(-1,-1),1.6),('BOTTOMPADDING',(0,0),(-1,-1),1.6),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,ROWALT])]))
    E.append(t)
    idx_path=out+'.idx.pdf'
    SimpleDocTemplate(idx_path,pagesize=letter,topMargin=0.55*inch,bottomMargin=0.5*inch,
                      leftMargin=0.65*inch,rightMargin=0.65*inch).build(E)
    final=fitz.open(); final.insert_pdf(fitz.open(idx_path)); final.insert_pdf(body)
    from safewrite import write_via_temp
    try:
        if not write_via_temp(out,lambda tmp: final.save(tmp,deflate=True,garbage=3),say):
            return out       # locked: previous version kept, user already told
    finally:
        try: os.remove(idx_path)
        except OSError: pass
    say(f"Proof pack: {exh} exhibits, {final.page_count} pages")
    return out

def build_print_package(cover_pdf,statement_pdf,out):
    import fitz
    m=fitz.open()
    for p in (cover_pdf,statement_pdf):
        if p and os.path.exists(p): m.insert_pdf(fitz.open(p))
    m.save(out,deflate=True)
    return out

def export_all(rows,cfg,bills_folder,outdir,progress=None):
    say=progress or (lambda m:None)
    from safewrite import write_via_temp
    os.makedirs(outdir,exist_ok=True)
    outs={}
    cov=os.path.join(outdir,'Reimbursement_Cover_Letter.pdf')
    try:
        if write_via_temp(cov,lambda tmp: build_cover_letter(rows,cfg,tmp),say):
            say("Cover letter built.")
        outs['cover']=cov
    except Exception as e: say(f"Cover letter failed: {e}")
    stmt=os.path.join(outdir,'Reimbursement_Statement.pdf')
    try:
        build_proof_pack(rows,bills_folder,os.path.join(outdir,'Reimbursement_Proof_Pack.pdf'),say)
        outs['proof']=os.path.join(outdir,'Reimbursement_Proof_Pack.pdf')
    except Exception as e: say(f"Proof pack failed: {e}")
    try:
        prn=os.path.join(outdir,'Reimbursement_Package_PRINT.pdf')
        if write_via_temp(prn,lambda tmp: build_print_package(cov,stmt,tmp),say):
            say("Print package built.")
        outs['print']=prn
    except Exception as e: say(f"Print package failed: {e}")
    return outs
