"""Court submission PDF: captioned accounting of reimbursement claims, tied to the judgments
of record, with every line cross-referenced to an Exhibit in the attached proof pages.

Outputs (in output/ and docs/):
  Reimbursement_Court_Statement.pdf  - the accounting alone (caption, basis, summary, ledger)
  Reimbursement_Court_Package.pdf    - statement + exhibit index + every exhibit (one file)
Built by build_portal.build() with the same exhibit numbering the portal uses.
"""
import os, json, datetime as _dt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether)
import categorize

NAVY=colors.HexColor('#1F3864'); GREY=colors.HexColor('#555555'); LIGHT=colors.HexColor('#E8EDF7'); ROWALT=colors.HexColor('#F6F7FB')
HERE=os.path.dirname(os.path.abspath(__file__))
def M(v): return "${:,.2f}".format(v)

# ---- legal basis per category (counsel to confirm wording before filing) ----
BASIS={
 'Mortgage':("Interim Consent Judgment (signed Jan. 17, 2025), 'Former Matrimonial Domicile': Gerald Pearson 'shall pay the mortgage "
             "note on the former matrimonial domicile with a right to reimbursement in the partition.' Parties co-own 8792 W Fairway Dr "
             "in indivision (Petition for Partition, paras. 7-8); reimbursement in proportion to their equal shares.","50%"),
 'Utilities':("Necessary expense of the co-owned domicile paid by one co-owner; reimbursable by the other in proportion to her "
              "one-half share (La. C.C. art. 806). Claimed only through May 31, 2026 - Lindsey vacated under the Apr. 21, 2026 ex parte "
              "order and bills after that date are not claimed.","50%"),
 'Pool':("Necessary maintenance of the co-owned domicile (La. C.C. art. 806); claimed through May 31, 2026 only.","50%"),
 'Construction & Home Improvements':("Work on the co-owned domicile to prepare it for the court-ordered sale (realtor punch list, "
              "painting). Preservation/management expense of co-owned property (La. C.C. art. 806); Petition for Partition asks that "
              "sale expenses be borne equally.","50%"),
 'Home Repairs & A/C':("Necessary repairs to the co-owned domicile (La. C.C. art. 806).","50%"),
 'Advances to Lindsey':("Money paid directly to Lindsey Pearson (Venmo, memo lines quoted) - advances repayable in full.","100%"),
 'School/Tuition':("Interim Consent Judgment, 'School Expenses': Gerald 88% / Lindsey 12% of tuition, registration and necessary "
              "school expenses; 'Extracurricular Activities': same 88/12 split.","12%"),
 'Medical/Dental/Vision':("Interim Consent Judgment, 'Health Insurance and Uncovered Medical Cost': Gerald 88% / Lindsey 12% of "
              "out-of-pocket medical, dental, orthodontic and vision expenses.","12%"),
 'AT&T Business':("Lindsey's line on the family wireless plan carried by Gerald; her agreed portion of $100 per month, through May 2026.","flat $100/mo"),
 'Storage':("PODS container used for the household during the nesting period; co-owned household expense.","50%"),
 'Cleaning':("Cleaning of the co-owned domicile, including sale preparation (La. C.C. art. 806).","50%"),
 'Lawn/Yard':("Lawn and yard maintenance of the co-owned domicile; claimed through May 31, 2026 only.","50%"),
 'Moving/Household':("Packing and moving of Lindsey's belongings out of the domicile; agreed 80% share.","80%"),
 'Labor':("Labor for sale preparation of the co-owned domicile; agreed flat amount, shared equally.","50%"),
}

def _child_support():
    """Support paid in advance of the Apr. 21, 2026 termination (Stipulated Judgment of May 5, 2026)."""
    monthly=1012.00
    april=round(monthly*10/30,2)        # Apr 21-30 (10 of 30 days)
    may=monthly                         # May 1 payment, obligation already terminated
    return monthly,april,may,round(april+may,2)

def build(rows,cfg,mapping,mapping_id,proof_doc,outdir,docs,progress=print):
    import fitz
    sp=cfg.get('split_percent',{})
    pos={c:i for i,c in enumerate(categorize.DISPLAY_CATS)}
    billable=[r for r in rows if r['include'] and r.get('in_window',True) and r.get('amount') is not None
              and r.get('her_share') is not None and r['vendor']!='Paid TO Lindsey' and sp.get(r['category']) is not None]
    billable.sort(key=lambda r:(pos.get(r['category'],99),r.get('ref') or 'Z',r.get('date') or ''))
    def exh_of(r):
        f=str(r.get('file','')); rid=categorize.item_id(r)
        if f in mapping: return mapping[f]['exh'],False
        if rid in mapping_id: return mapping_id[rid]['exh'],True
        return None,None
    cats={}
    for r in billable:
        c=cats.setdefault(r['category'],[0,0.0,0.0]); c[0]+=1; c[1]+=r['amount']; c[2]+=r['her_share']
    order=sorted(cats,key=lambda c:pos.get(c,99))
    net=round(sum(v[2] for v in cats.values()),2)
    dates=sorted(r['date'] for r in billable if r.get('date'))
    styles=getSampleStyleSheet()
    def S(name,**k):
        k.setdefault('fontName','Times-Roman'); return ParagraphStyle(name,parent=styles['Normal'],**k)
    body=S('b',fontSize=10.5,leading=14); small=S('sm',fontSize=8.5,leading=11,textColor=GREY)
    h1=S('h1',fontName='Times-Bold',fontSize=13,alignment=TA_CENTER,spaceBefore=6,spaceAfter=8)
    h2=S('h2',fontName='Times-Bold',fontSize=11.5,textColor=NAVY,spaceBefore=12,spaceAfter=5)
    cell=S('c',fontSize=8.6,leading=10.6); cellb=S('cb',fontName='Times-Bold',fontSize=8.6,leading=10.6)
    today=_dt.date.today().strftime('%B %d, %Y')

    E=[]
    cap=Table([[Paragraph('GERALD PEARSON<br/><br/>VERSUS<br/><br/>LINDSEY PEARSON',S('cp',fontName='Times-Bold',fontSize=11,leading=14)),
                Paragraph('DOCKET NO. 236951; DIV. "A"<br/><br/>THE FAMILY COURT<br/><br/>PARISH OF EAST BATON ROUGE<br/><br/>STATE OF LOUISIANA',
                          S('cp2',fontName='Times-Bold',fontSize=11,leading=14,alignment=TA_RIGHT))]],colWidths=[3.4*inch,3.4*inch])
    cap.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,-1),1.2,colors.black),('BOTTOMPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
    E+= [cap,Spacer(1,14),
         Paragraph('ACCOUNTING OF REIMBURSEMENT CLAIMS',S('t',fontName='Times-Bold',fontSize=14,alignment=TA_CENTER,leading=18)),
         Paragraph('Amounts paid by Gerald Pearson for the co-owned domicile, the minor children, and Lindsey Pearson, '
                   'and the share owed by Lindsey Pearson under the judgments of record',S('st',fontSize=10,alignment=TA_CENTER,leading=13,textColor=GREY)),
         Spacer(1,12),
         Paragraph(f'Period: {dates[0]} through {dates[-1]}. Prepared {today} from the source documents reproduced as Exhibits 1-{proof_doc_count(mapping,mapping_id)} '
                   'in the attached proof pages. Every line in the ledger (Section V) carries its Exhibit number.',body)]
    # I. Record
    E.append(Paragraph('I.  Judgments and pleadings of record relied upon',h2))
    rec=[['Date','Document','Provision applied'],
         ['Jan. 17, 2025','Interim Consent Judgment (Judge Baker)','Gerald pays the mortgage note with a right to reimbursement in the partition; Gerald 88% / Lindsey 12% of tuition, registration, school expenses, extracurriculars and uncovered medical/dental/vision; child support $1,012/mo payable by Gerald.'],
         ['Sept. 29, 2025','Judgment of Divorce','Parties divorced; co-ownership of 8792 W Fairway Dr continues (pre-nuptial agreement, no community).'],
         ['Apr. 21, 2026','Ex Parte Order - temporary sole custody to Gerald','Nesting ended; Lindsey no longer occupies the domicile. House bills are claimed only through May 31, 2026.'],
         ['May 5, 2026','Interim Stipulated Judgment (Judge Woodruff-White, pro tem)','Child support terminated retroactive to Apr. 21, 2026; Gerald reserves reimbursement of support paid in advance of that date. Lindsey retrieved belongings May 8, 2026.'],
         ['Filed 2025','Petition for Partition and Rule to List the Domicile for Sale','Accounting between co-owners; reimbursement claims reserved; sale expenses to be split equally.']]
    t=Table([[Paragraph(x,cellb if i==0 else cell) for x in row] for i,row in enumerate(rec)],colWidths=[0.95*inch,2.0*inch,3.85*inch],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#B8BEC9')),('VALIGN',(0,0),(-1,-1),'TOP'),
                           ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    E.append(t)
    # II. Summary
    E.append(Paragraph('II.  Summary of amounts owed by Lindsey Pearson',h2))
    d=[['Category','Lines','Total paid by Gerald','Her share','Amount owed']]
    for c in order:
        n,amt,her=cats[c]; d.append([c,str(n),M(amt),BASIS.get(c,('', f"{sp.get(c)}%"))[1],M(her)])
    d.append(['TOTAL OWED BY LINDSEY PEARSON','',M(sum(v[1] for v in cats.values())),'',M(net)])
    t=Table([[Paragraph(x,cellb if (i==0 or i==len(d)-1) else cell) for x in row] for i,row in enumerate(d)],
            colWidths=[2.6*inch,0.6*inch,1.5*inch,1.0*inch,1.1*inch],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#B8BEC9')),('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,ROWALT]),
        ('BACKGROUND',(0,-1),(-1,-1),LIGHT),('ALIGN',(1,1),(4,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    E.append(t)
    E.append(Paragraph('Figures are the actual amounts on the bills and payment records reproduced in the Exhibits. Utility lines use the '
                       'current-period charge, never a past-due balance, so no month is counted twice. Duplicate documents and partial-payment '
                       'receipts are excluded. No interest, estimates, projections or settlement figures are included.',small))
    # II-b child support
    mo,apr,may,cs=_child_support()
    E.append(Paragraph('II-A.  Child support paid after the termination date (reserved by the May 5, 2026 judgment - shown separately, not in the total above)',h2))
    d=[['Period','Basis','Amount'],
       ['Apr. 21-30, 2026 (10 of 30 days)',f'{M(mo)}/mo x 10/30 - paid for April before the retroactive termination',M(apr)],
       ['May 2026 (paid May 1, 2026)',f'{M(mo)} full month paid after the obligation had ended',M(may)],
       ['Reimbursable child support','',M(cs)]]
    t=Table([[Paragraph(x,cellb if i in (0,len(d)-1) else cell) for x in row] for i,row in enumerate(d)],colWidths=[2.3*inch,3.5*inch,1.0*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#B8BEC9')),('ALIGN',(2,1),(2,-1),'RIGHT'),
                           ('BACKGROUND',(0,-1),(-1,-1),LIGHT),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    E.append(t)
    # III. Basis
    E.append(Paragraph('III.  Percentage applied to each category and its source in the record',h2))
    d=[['Category','Share','Source of the percentage']]
    for c in order: d.append([c,BASIS.get(c,('',f"{sp.get(c)}%"))[1],BASIS.get(c,('Agreed between the parties.',''))[0]])
    t=Table([[Paragraph(x,cellb if i==0 else cell) for x in row] for i,row in enumerate(d)],colWidths=[1.7*inch,0.8*inch,4.3*inch],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#B8BEC9')),('VALIGN',(0,0),(-1,-1),'TOP'),
                           ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    E.append(t)
    E.append(Paragraph('Legal characterizations above are offered for counsel\'s review; the figures do not depend on them.',small))
    # IV. Voluntary support
    ap=os.path.join(HERE,'additional.json'); addl=json.load(open(ap,encoding='utf-8')) if os.path.exists(ap) else None
    if addl:
        E.append(Paragraph('IV.  Amounts Gerald Pearson paid for Lindsey Pearson that are NOT claimed',h2))
        E.append(Paragraph('For the Court\'s context only. These were paid by Gerald and are not part of the total in Section II.',body))
        d=[['Item','Period / basis','Amount paid']]
        for s in addl.get('sections',[]):
            nm=s['name']
            if 'Health insurance' in nm:
                nm+=' - ordered by the Jan. 17, 2025 Consent Judgment only until the Sept. 29, 2025 divorce; Oct. 2025 - May 2026 continued voluntarily'
            d.append([nm,s.get('basis',''),M(s['total'])])
        d.append(['Court-ordered child support, Jan. 2025 - Apr. 20, 2026','$1,012/mo under the Consent Judgment, paid through May 1, 2026 (reserved portion in II-A)','paid as ordered'])
        d.append(['Direct support to Elijah Pearson (fuel, food, school needs)','Aug 2024 - Jul 2026, approximate','about $7,700'])
        d.append([addl.get('grand_label','TOTAL VOLUNTARY SUPPORT'),'',M(addl.get('grand_total',0))])
        t=Table([[Paragraph(x,cellb if i in (0,len(d)-1) else cell) for x in row] for i,row in enumerate(d)],colWidths=[2.9*inch,2.9*inch,1.0*inch],repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#B8BEC9')),('ALIGN',(2,1),(2,-1),'RIGHT'),
                               ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,-1),(-1,-1),LIGHT),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        E.append(t)
    # V. Ledger
    E.append(PageBreak())
    E.append(Paragraph('V.  Itemized ledger - every line with its Exhibit',h1))
    E.append(Paragraph('Ref = line number used throughout. Exhibit = page in the attached proof pages reproducing the bill, invoice, statement '
                       'or payment record for that line ("SR" = source record page describing a payment made without a paper bill).',small))
    for c in order:
        items=[r for r in billable if r['category']==c]
        E.append(Paragraph(f"{c} - {M(cats[c][1])} paid, {M(cats[c][2])} owed at {BASIS.get(c,('',str(sp.get(c))+'%'))[1]}",h2))
        d=[['Ref','Date','Payee','Description','Paid','Owed','Exhibit']]
        for r in items:
            ex,rec_=exh_of(r); exs=(f"Ex. {ex}"+(' (SR)' if rec_ else '')) if ex else '-'
            d.append([r.get('ref',''),r.get('date') or '',r['vendor'][:28],(r.get('desc') or '')[:60],M(r['amount']),M(r['her_share']),exs])
        d.append(['','','',f'{c} subtotal',M(cats[c][1]),M(cats[c][2]),''])
        t=Table([[Paragraph(x,cellb if i in (0,len(d)-1) else cell) for x in row] for i,row in enumerate(d)],
                colWidths=[0.5*inch,0.72*inch,1.35*inch,2.33*inch,0.72*inch,0.68*inch,0.65*inch],repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#C9CED8')),('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,ROWALT]),
            ('ALIGN',(4,1),(5,-1),'RIGHT'),('BACKGROUND',(0,-1),(-1,-1),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
        E.append(t)
    E.append(Spacer(1,18))
    E.append(Paragraph('Respectfully submitted for the Court\'s accounting between co-owners and parents under the judgments cited above.',body))
    E.append(Spacer(1,26)); E.append(Paragraph('_______________________________________<br/>GERALD PEARSON',body))
    E.append(Spacer(1,6)); E.append(Paragraph('Through counsel of record: Lori E. Palmintier (La. Bar No. 35951), Brock &amp; Palmintier Law, LLC, 4608 Bluebonnet Blvd., Baton Rouge, LA 70809',small))

    def footer(cv,dd):
        cv.saveState(); cv.setFont('Times-Roman',7.5); cv.setFillColor(GREY)
        cv.drawString(0.8*inch,0.5*inch,'Pearson v. Pearson, No. 236951 Div. A - Accounting of Reimbursement Claims')
        cv.drawRightString(7.7*inch,0.5*inch,f'Page {dd.page}'); cv.restoreState()
    stmt=os.path.join(outdir,'Reimbursement_Court_Statement.pdf')
    SimpleDocTemplate(stmt,pagesize=letter,topMargin=0.8*inch,bottomMargin=0.8*inch,leftMargin=0.8*inch,rightMargin=0.8*inch,
                      title='Accounting of Reimbursement Claims - Pearson v. Pearson No. 236951').build(E,onFirstPage=footer,onLaterPages=footer)
    # exhibit index + package
    idx=[]
    for rel,m in mapping.items(): idx.append((m['exh'],m['cat'],m['base'],m['page']))
    for rid,m in mapping_id.items(): idx.append((m['exh'],m['cat'],'Source record - '+m['doc'],m['page']))
    idx.sort()
    EI=[Paragraph('EXHIBIT INDEX',S('ei',fontName='Times-Bold',fontSize=13,alignment=TA_CENTER)),Spacer(1,8),
        Paragraph('Exhibit pages follow this index in order. Page numbers are within the exhibit section.',small),Spacer(1,6)]
    d=[['Ex.','Category','Document','Exhibit page']]+[[str(e),c,f[:64],str(p)] for e,c,f,p in idx]
    t=Table([[Paragraph(x,cellb if i==0 else cell) for x in row] for i,row in enumerate(d)],colWidths=[0.5*inch,1.7*inch,3.9*inch,0.9*inch],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#C9CED8')),
                           ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,ROWALT]),('TOPPADDING',(0,0),(-1,-1),1.5),('BOTTOMPADDING',(0,0),(-1,-1),1.5)]))
    EI.append(t)
    ip=os.path.join(outdir,'_court_idx.pdf')
    SimpleDocTemplate(ip,pagesize=letter,topMargin=0.7*inch,bottomMargin=0.7*inch,leftMargin=0.8*inch,rightMargin=0.8*inch).build(EI)
    pkg=fitz.open(); pkg.insert_pdf(fitz.open(stmt)); pkg.insert_pdf(fitz.open(ip)); pkg.insert_pdf(proof_doc)
    out=os.path.join(outdir,'Reimbursement_Court_Package.pdf'); pkg.save(out,deflate=True,garbage=3); pkg.close()
    try: os.remove(ip)
    except OSError: pass
    import shutil
    for fn in ('Reimbursement_Court_Statement.pdf','Reimbursement_Court_Package.pdf'):
        shutil.copyfile(os.path.join(outdir,fn),os.path.join(docs,fn))
    progress(f'Court package: statement + {len(idx)} exhibits -> {out} ({os.path.getsize(out)/1e6:.1f} MB)')
    return stmt,out

def proof_doc_count(mapping,mapping_id):
    return max([m['exh'] for m in mapping.values()]+[m['exh'] for m in mapping_id.values()]+[0])
