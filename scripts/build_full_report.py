"""Master Builder Script for DocAssistIQ Comprehensive Project Report.

Orchestrates all sections 1 to 19 and generates the final .docx file.
"""

import os
import sys
import time

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.generate_docx_report import init_document
from scripts.report_sections_part1 import (
    build_cover_and_section1,
    build_section2_abstract,
    build_section3_introduction,
    build_section4_literature_review,
    build_section5_problem_statement,
    build_section6_objectives,
)
from scripts.report_sections_part2 import (
    build_section7_existing_system,
    build_section8_proposed_system,
    build_section9_system_architecture,
    build_section10_methodology_workflow,
    build_section11_technologies_used,
    build_section12_modules,
)
from scripts.report_sections_part3 import (
    build_section13_implementation,
    build_section14_results_output,
    build_section15_future_scope,
    build_section16_conclusion,
    build_section17_references,
    build_section18_publication,
    build_section19_thank_you,
)

def build_full_report():
    print("=" * 70)
    print("DocAssistIQ — Building Comprehensive Professional Report (.docx)")
    print("=" * 70)
    start_time = time.time()
    
    doc = init_document()
    print("[1/3] Initialized document with custom typography, margins, header & footer.")
    
    # Part 1: Sections 1 to 6
    print("[2/3] Generating Part 1: Sections 1 to 6...")
    build_cover_and_section1(doc)
    build_section2_abstract(doc)
    build_section3_introduction(doc)
    build_section4_literature_review(doc)
    build_section5_problem_statement(doc)
    build_section6_objectives(doc)
    
    # Part 2: Sections 7 to 12
    print("      Generating Part 2: Sections 7 to 12...")
    build_section7_existing_system(doc)
    build_section8_proposed_system(doc)
    build_section9_system_architecture(doc)
    build_section10_methodology_workflow(doc)
    build_section11_technologies_used(doc)
    build_section12_modules(doc)
    
    # Part 3: Sections 13 to 19
    print("      Generating Part 3: Sections 13 to 19...")
    build_section13_implementation(doc)
    build_section14_results_output(doc)
    build_section15_future_scope(doc)
    build_section16_conclusion(doc)
    build_section17_references(doc)
    build_section18_publication(doc)
    build_section19_thank_you(doc)
    
    # Output path
    output_filename = "DocAssistIQ_Comprehensive_Project_Report.docx"
    output_path = os.path.abspath(output_filename)
    
    print(f"[3/3] Saving document to: {output_path}")
    doc.save(output_path)
    
    elapsed = time.time() - start_time
    file_size_kb = os.path.getsize(output_path) / 1024.0
    
    # Compute stats
    para_count = len(doc.paragraphs)
    table_count = len(doc.tables)
    total_words = sum(len(p.text.split()) for p in doc.paragraphs)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                total_words += sum(len(p.text.split()) for p in c.paragraphs)
                
    print("=" * 70)
    print("REPORT GENERATION SUCCESSFUL!")
    print(f"  Target File       : {output_path}")
    print(f"  File Size         : {file_size_kb:.2f} KB")
    print(f"  Total Paragraphs  : {para_count}")
    print(f"  Total Tables      : {table_count}")
    print(f"  Estimated Words   : {total_words:,} words")
    print(f"  Time Elapsed      : {elapsed:.2f} seconds")
    print("=" * 70)
    
    return output_path

if __name__ == "__main__":
    build_full_report()
