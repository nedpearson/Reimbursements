#!/usr/bin/env python3
"""Build Amounts_Paid_For_Lindsey.pdf from additional.json — always in sync.
Called automatically by build_portal.py; can also be run alone."""
import os, json, datetime as _dt
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY = colors.HexColor('#1F3864')
GREY = colors.HexColor('#666666')
ROWALT = colors.HexColor('#F2F5FA')


def _money(v):
    return '$%s' % format(v, ',.2f')


def build(out=None):
    a = json.load(open(os.path.join(HERE, 'additional.json'), encoding='utf-8'))
    out = out or os.path.join(HERE, a.get('doc', 'Amounts_Paid_For_Lindsey.pdf'))
    styles = getSampleStyleSheet()
    title = ParagraphStyle('t', parent=styles['Normal'], fontName='Helvetica-Bold',
                           fontSize=16, textColor=NAVY, leading=20)
    sub = ParagraphStyle('s', parent=styles['Normal'], fontSize=9.5,
                         textColor=GREY, leading=13)
    h2 = ParagraphStyle('h', parent=styles['Normal'], fontName='Helvetica-Bold',
                        fontSize=11.5, textColor=NAVY, spaceBefore=14, leading=15)
    E = [Paragraph(a.get('title', "Additional Amounts Paid on Lindsey's Behalf"), title),
         Spacer(1, 4),
         Paragraph(a.get('subtitle', ''), sub),
         Spacer(1, 2),
         Paragraph('Prepared %s — Gerald "Ned" Pearson Jr. · Pearson v. Pearson, No. 236951'
                   % _dt.date.today().strftime('%B %d, %Y'), sub),
         Spacer(1, 10)]
    for s in a['sections']:
        E.append(Paragraph('%s &nbsp;—&nbsp; %s' % (s['name'], _money(s['total'])), h2))
        if s.get('basis'):
            E.append(Paragraph(s['basis'], sub))
        items = s.get('items') or []
        if items:
            data = [['Date', 'Description', 'Amount']] + \
                   [[i['d'], i['desc'], _money(i['a'])] for i in items] + \
                   [['', 'Section total', _money(s['total'])]]
            t = Table(data, colWidths=[0.95 * inch, 4.45 * inch, 1.15 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
                ('TOPPADDING', (0, 0), (-1, -1), 2.2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.2),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, ROWALT]),
            ]))
            E.append(Spacer(1, 4)); E.append(t)
    E.append(Spacer(1, 14))
    gt = Table([['GRAND TOTAL — PAID ON LINDSEY\'S BEHALF', _money(a['grand_total'])]],
               colWidths=[5.4 * inch, 1.15 * inch])
    gt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10.5),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    E.append(gt)
    if a.get('alt'):
        E.append(Spacer(1, 8)); E.append(Paragraph(a['alt'], sub))
    from safewrite import write_via_temp
    write_via_temp(out, lambda tmp: SimpleDocTemplate(
        tmp, pagesize=letter, topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        title=a.get('title', 'Additional Amounts')).build(list(E)), print)
    return out


if __name__ == '__main__':
    print('Built', build())
