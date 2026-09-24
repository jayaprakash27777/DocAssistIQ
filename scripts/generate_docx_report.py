"""DocAssistIQ — Comprehensive Academic & Professional Project Report Generator.

This script constructs a publication-grade, professionally styled Microsoft Word
document (.docx) covering all 19 mandatory sections for the DocAssistIQ platform.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

# ---------------------------------------------------------------------------
# COLOR PALETTE SPECIFICATION
# ---------------------------------------------------------------------------
HEX_PRIMARY = "0F2942"      # Deep Navy / Midnight Blue
HEX_SECONDARY = "0D9488"    # Medical Teal / Cyan
HEX_ACCENT = "0284C7"       # Clinical Sky Blue
HEX_DARK = "1F2937"         # Charcoal Body Text
HEX_LIGHT_BG = "F8FAFC"     # Slate 50 Neutral Light Shading
HEX_BORDER = "CBD5E1"       # Slate 300 Subtle Border
HEX_WARNING = "B91C1C"      # Clinical Red / Alert Crimson
HEX_WARNING_BG = "FEF2F2"   # Light Crimson Shading
HEX_SUCCESS = "15803D"      # Forest Green
HEX_SUCCESS_BG = "F0FDF4"   # Light Green Shading

COLOR_PRIMARY = RGBColor(15, 41, 66)
COLOR_SECONDARY = RGBColor(13, 148, 136)
COLOR_ACCENT = RGBColor(2, 132, 199)
COLOR_DARK = RGBColor(31, 41, 55)
COLOR_MUTED = RGBColor(100, 116, 139)
COLOR_WARNING = RGBColor(185, 28, 28)

# ---------------------------------------------------------------------------
# XML STYLING HELPERS
# ---------------------------------------------------------------------------
def set_cell_background(cell, fill_hex: str):
    """Set the background hex color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    """Set internal cell margins (padding) in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4"):
    """Set thin clean horizontal borders and subtle outer borders on a table."""
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for b in ['top', 'bottom', 'insideH']:
        border = OxmlElement(f'w:{b}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    for b in ['left', 'right', 'insideV']:
        border = OxmlElement(f'w:{b}')
        border.set(qn('w:val'), 'none')
        tblBorders.append(border)
    tblPr.append(tblBorders)

def add_page_number_to_run(run):
    """Inject Word PAGE and NUMPAGES fields into a text run."""
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = "PAGE"
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

# ---------------------------------------------------------------------------
# DOCUMENT INITIALIZATION & CORE TYPOGRAPHY
# ---------------------------------------------------------------------------
def init_document():
    doc = docx.Document()
    
    # 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True
        
        # Header for subsequent pages
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("DocAssistIQ — Comprehensive Engineering & Clinical Report")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED
        
        # Footer for subsequent pages
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun1 = fp.add_run("DocAssistIQ Technical Specification | Page ")
        frun1.font.name = "Calibri"
        frun1.font.size = Pt(9.0)
        frun1.font.color.rgb = COLOR_MUTED
        add_page_number_to_run(frun1)
        frun2 = fp.add_run(" (Confidential & Proprietary)")
        frun2.font.name = "Calibri"
        frun2.font.size = Pt(9.0)
        frun2.font.color.rgb = COLOR_MUTED

    # Base Normal Style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(10.5)
    style_normal.font.color.rgb = COLOR_DARK
    style_normal.paragraph_format.line_spacing = 1.18
    style_normal.paragraph_format.space_after = Pt(4)

    return doc

# ---------------------------------------------------------------------------
# CONTENT INJECTION HELPERS
# ---------------------------------------------------------------------------
def add_h1(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(16.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY
    return p

def add_h2(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(13)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(13.0)
    run.font.bold = True
    run.font.color.rgb = COLOR_SECONDARY
    return p

def add_h3(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(9)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(11.0)
    run.font.bold = True
    run.font.color.rgb = COLOR_DARK
    return p

def add_p(doc, text: str, bold_prefix: str = None, italic_prefix: str = None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4.5)
    p.paragraph_format.line_spacing = 1.18
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.font.name = "Calibri"
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_DARK
    if italic_prefix:
        r_it = p.add_run(italic_prefix + " ")
        r_it.font.name = "Calibri"
        r_it.font.italic = True
        r_it.font.color.rgb = COLOR_MUTED
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.color.rgb = COLOR_DARK
    return p

def add_bullet(doc, text: str, bold_prefix: str = None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.font.name = "Calibri"
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_DARK
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.color.rgb = COLOR_DARK
    return p

def add_callout(doc, text: str, alert_type="NOTE", bold_title: str = None):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    
    border_color = HEX_PRIMARY if alert_type == "NOTE" else (HEX_WARNING if alert_type == "ALERT" else HEX_SECONDARY)
    bg_color = HEX_LIGHT_BG if alert_type == "NOTE" else (HEX_WARNING_BG if alert_type == "ALERT" else HEX_SUCCESS_BG)
    
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24') # 3pt thick bar
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), border_color)
    tcBorders.append(left)
    
    for b in ['top', 'bottom', 'right']:
        nb = OxmlElement(f'w:{b}')
        nb.set(qn('w:val'), 'none')
        tcBorders.append(nb)
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    title_text = bold_title if bold_title else ("CLINICAL MANDATE / SYSTEM RULE" if alert_type == "ALERT" else "ENGINEERING SPECIFICATION")
    trun = p.add_run(f"[{title_text}]\n")
    trun.font.name = "Calibri"
    trun.font.size = Pt(10.0)
    trun.font.bold = True
    trun.font.color.rgb = COLOR_WARNING if alert_type == "ALERT" else COLOR_PRIMARY
    
    mrun = p.add_run(text)
    mrun.font.name = "Calibri"
    mrun.font.size = Pt(10.0)
    mrun.font.color.rgb = COLOR_DARK
    
    # Empty space after callout
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(2)
    sp.paragraph_format.space_after = Pt(4)

def add_table(doc, headers: list, rows: list, col_widths: list = None):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    set_table_borders(tbl)
    
    # Header row
    hdr_cells = tbl.rows[0].cells
    for i, title in enumerate(headers):
        cell = hdr_cells[i]
        if col_widths and i < len(col_widths):
            cell.width = Inches(col_widths[i])
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        run = p.add_run(title)
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Data rows
    for r_idx, r_data in enumerate(rows):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_hex = HEX_LIGHT_BG if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            cell = row_cells[c_idx]
            if col_widths and c_idx < len(col_widths):
                cell.width = Inches(col_widths[c_idx])
            set_cell_background(cell, bg_hex)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.10
            run = p.add_run(str(val))
            run.font.name = "Calibri"
            run.font.size = Pt(9.0)
            run.font.color.rgb = COLOR_DARK
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(2)
    sp.paragraph_format.space_after = Pt(6)

print("Report generator core loaded successfully.")
