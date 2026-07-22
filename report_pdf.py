"""Professional PDF reimbursement statement (reportlab)."""
import json, os, datetime as _dt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, HRFlowable)

NAVY=colors.HexColor('#1F3864'); ACCENT=colors.HexColor('#2E7D32')
LIGHT=colors.HexColor('#D9E1F2'); GREY=colors.HexColor('#606060'); ROWALT=colors.HexColor('#F4F6FB')

def _money(v):
    if v is None: return ''
    return ("(${:,.2f})".format(-v)) if v<0 else "${:,.2f}".format(v)

def build_pdf(rows, cfg, out, prepared_for="Lindsey Pearson", prepared_by='Gerald "Ned" Pearson',
              matter="Pearson v. Pearson — No. 236951, Family Court, East Baton Rouge Parish, LA"):
    sp=cfg.get('split_percent',{})
    def pct(cat):
        v=sp.get(cat); 
        return (v/100.0 if v and v>1 else v) or 0
    cutoff=cfg.get('date_cutoff')
    def inwin(r): return not (cutoff and r.get('date') and r['date']<cutoff)
    CREDIT='Paid TO Lindsey'
    billable=[r for r in rows if r['include'] and inwin(r) and r['amount'] is not None and r['vendor']!=CREDIT and sp.get(r['category']) is not None]
    credits=[r for r in rows if r['vendor']==CREDIT and r['amount'] is not None and inwin(r)]
    # category rollup
    cats={}
    for r in billable:
        c=cats.setdefault(r['category'],[0,0.0,0.0]); c[0]+=1; c[1]+=r['amount']
        # use the engine's computed share (handles flat-dollar rows like AT&T $100/mo
        # and half-up rounding) instead of recomputing from the category percent
        hs=r.get('her_share')
        c[2]+=hs if hs is not None else round(r['amount']*pct(r['category']),2)
    for c in cats: cats[c][2]=round(cats[c][2],2)
    order=[c for c in sp.keys() if c in cats]
    subtotal=round(sum(v[2] for v in cats.values()),2)
    def pctlabel(cat):
        return 'flat' if (pct(cat)==0 and cats.get(cat,[0,0,0.0])[2]>0) else f"{pct(cat)*100:.0f}%"
    credit_tot=sum(r['amount'] for r in credits) if cfg.get('subtract_payments_to_lindsey') else 0.0
    net=subtotal-credit_tot
    dates=sorted(r['date'] for r in billable if r['date'])
    span=f"{dates[0]} to {dates[-1]}" if dates else ""

    styles=getSampleStyleSheet()
    def S(name,**k):
        k.setdefault('fontName','Helvetica')
        return ParagraphStyle(name,parent=styles['Normal'],**k)
    title=S('t',fontName='Helvetica-Bold',fontSize=22,textColor=NAVY,alignment=TA_CENTER,leading=26)
    sub=S('s',fontSize=10.5,textColor=GREY,alignment=TA_CENTER,leading=15)
    h2=S('h2',fontName='Helvetica-Bold',fontSize=13,textColor=NAVY,spaceBefore=14,spaceAfter=6)
    body=S('b',fontSize=9.5,leading=13,textColor=colors.HexColor('#333333'))
    small=S('sm',fontSize=8,leading=11,textColor=GREY)

    doc=SimpleDocTemplate(out,pagesize=letter,topMargin=0.7*inch,bottomMargin=0.7*inch,
                          leftMargin=0.75*inch,rightMargin=0.75*inch,title="Expense Reimbursement Statement")
    E=[]
    E.append(Paragraph("Expense Reimbursement Statement",title))
    E.append(Spacer(1,4))
    E.append(Paragraph("Shared household &amp; child-related expenses",sub))
    E.append(Spacer(1,10))
    E.append(HRFlowable(width='100%',thickness=1.4,color=NAVY))
    E.append(Spacer(1,10))
    meta=[[Paragraph("<b>Prepared by</b>",body),Paragraph(prepared_by,body),
           Paragraph("<b>Statement date</b>",body),Paragraph(_dt.date.today().strftime('%B %d, %Y'),body)],
          [Paragraph("<b>Reimbursement from</b>",body),Paragraph(prepared_for,body),
           Paragraph("<b>Period covered</b>",body),Paragraph(span,body)]]
    mt=Table(meta,colWidths=[1.35*inch,2.1*inch,1.3*inch,2.15*inch])
    mt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    E.append(mt)
    E.append(Paragraph(f"Matter: {matter}",small))
    E.append(Spacer(1,14))

    # NET banner
    banner=Table([[Paragraph(f"<font color='white'><b>NET AMOUNT DUE TO {prepared_by.upper()}</b></font>",
                    S('bn',fontSize=12,alignment=TA_LEFT)),
                   Paragraph(f"<font color='white'><b>{_money(net)}</b></font>",
                    S('bv',fontSize=17,alignment=TA_RIGHT))]],colWidths=[4.2*inch,2.7*inch])
    banner.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),ACCENT),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LEFTPADDING',(0,0),(0,0),14),('RIGHTPADDING',(-1,-1),(-1,-1),14)]))
    E.append(banner)
    E.append(Spacer(1,16))

    # Summary table
    E.append(Paragraph("Summary by category",h2))
    data=[['Category','Items','Total billed','Her %','Amount owed']]
    for c in order:
        n,amt,her=cats[c]
        data.append([c,str(n),_money(amt),pctlabel(c),_money(her)])
    data.append(['Subtotal','','','',_money(subtotal)])
    if cfg.get('subtract_payments_to_lindsey'):
        data.append([f'Less: payments already made to {prepared_for.split()[0]}','','','',_money(-credit_tot)])
    data.append(['NET AMOUNT DUE','','','',_money(net)])
    t=Table(data,colWidths=[2.9*inch,0.6*inch,1.25*inch,0.6*inch,1.25*inch])
    ts=[('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
        ('ALIGN',(1,0),(-1,-1),'RIGHT'),('ALIGN',(0,0),(0,-1),'LEFT'),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#BFBFBF')),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('ROWBACKGROUNDS',(0,1),(-1,len(order)),[colors.white,ROWALT])]
    sr=len(order)+1
    ts+=[('BACKGROUND',(0,sr),(-1,sr),LIGHT),('FONTNAME',(0,sr),(-1,sr),'Helvetica-Bold')]
    ts+=[('BACKGROUND',(0,len(data)-1),(-1,len(data)-1),ACCENT),('TEXTCOLOR',(0,len(data)-1),(-1,len(data)-1),colors.white),
         ('FONTNAME',(0,len(data)-1),(-1,len(data)-1),'Helvetica-Bold'),('FONTSIZE',(0,len(data)-1),(-1,len(data)-1),11)]
    t.setStyle(TableStyle(ts))
    E.append(t)
    E.append(Spacer(1,10))
    E.append(Paragraph("How this was calculated",h2))
    method=("Each expense was taken from source bills and receipts. Utility bills use the current-period charge "
      "(past-due balances excluded so no month is counted twice). Percentages reflect the parties' agreement: "
      "household and utility costs are shared 50/50; school/tuition and medical/dental/vision at "
      f"{int(pct('School/Tuition')*100)}%. Duplicate documents and partial-payment receipts were removed. "
      "Direct payments made to Lindsey during this period are itemized as advances to be repaid. "
      "A full itemized ledger follows.")
    E.append(Paragraph(method,body))

    # Itemized appendix by category
    E.append(PageBreak())
    E.append(Paragraph("Itemized ledger",title))
    E.append(Spacer(1,8))
    for c in order:
        items=sorted([r for r in billable if r['category']==c],key=lambda x:x['date'] or '')
        E.append(Paragraph(f"{c} &nbsp;—&nbsp; {_money(cats[c][1])} billed, {_money(cats[c][2])} owed at {pctlabel(c)}",h2))
        d=[['Date','Vendor','Description','Amount']]
        for r in items:
            d.append([r['date'] or '',r['vendor'],(r['desc'] or '')[:52],_money(r['amount'])])
        tt=Table(d,colWidths=[0.9*inch,1.7*inch,3.1*inch,1.0*inch],repeatRows=1)
        tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7.6),
            ('ALIGN',(3,0),(3,-1),'RIGHT'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,ROWALT]),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        E.append(tt); E.append(Spacer(1,10))
    if credits:
        E.append(Paragraph(f"Payments already made to {prepared_for} (credited)",h2))
        d=[['Date','Description','Amount']]
        for r in sorted(credits,key=lambda x:x['date'] or ''):
            d.append([r['date'] or '',(r['desc'] or '')[:60],_money(r['amount'])])
        d.append(['','TOTAL CREDITED',_money(credit_tot if cfg.get('subtract_payments_to_lindsey') else sum(r['amount'] for r in credits))])
        tt=Table(d,colWidths=[0.9*inch,4.8*inch,1.0*inch],repeatRows=1)
        tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7.6),('ALIGN',(2,0),(2,-1),'RIGHT'),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,ROWALT]),
            ('BACKGROUND',(0,-1),(-1,-1),LIGHT),('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        E.append(tt)

    def footer(cv,d):
        cv.saveState(); cv.setFont('Helvetica',7.5); cv.setFillColor(GREY)
        cv.drawString(0.75*inch,0.45*inch,"Expense Reimbursement Statement — generated from source documents")
        cv.drawRightString(7.75*inch,0.45*inch,f"Page {d.page}")
        cv.restoreState()
    doc.build(E,onFirstPage=footer,onLaterPages=footer)
    return out

if __name__=='__main__':
    import sys
    rows=json.load(open(os.path.join(os.path.dirname(__file__),'ledger.json')))
    cfg=json.load(open(os.path.join(os.path.dirname(__file__),'config.json')))
    build_pdf(rows,cfg,os.path.join(os.path.dirname(__file__),'Reimbursement_Statement.pdf'))
    print("PDF written")
