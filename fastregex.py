import os
import re
import shutil
from multiprocessing import Pool, cpu_count
from docx import Document
from docx.shared import RGBColor
import xlsxwriter
from openpyxl import load_workbook
from tqdm import tqdm

# === CONFIG ===
CHUNK_SIZE = 2000
INPUT_FILE = "input.txt"
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
OUTPUT_DOCX = "output.docx"
OUTPUT_XLSX = "output.xlsx"
TEMP_DIR = "temp_parts"

# === STEP 1: Split input.txt into N chunks ===
def split_file():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as infile:
        lines = []
        part = 0
        total = sum(1 for _ in open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore'))
        with tqdm(total=total, desc="Splitting file", unit="lines") as pbar:
            for i, line in enumerate(infile, 1):
                lines.append(line)
                if i % CHUNK_SIZE == 0:
                    with open(f"{TEMP_DIR}/chunk_{part}.txt", 'w', encoding='utf-8') as out:
                        out.writelines(lines)
                    lines = []
                    part += 1
                pbar.update(1)
            if lines:
                with open(f"{TEMP_DIR}/chunk_{part}.txt", 'w', encoding='utf-8') as out:
                    out.writelines(lines)

# === STEP 2: Process one chunk and write to Word and Excel ===
def process_chunk(chunk_path):
    chunk_id = os.path.splitext(os.path.basename(chunk_path))[0].split('_')[-1]
    pattern = re.compile(EMAIL_REGEX)

    doc = Document()
    excel_path = f"{TEMP_DIR}/chunk_{chunk_id}.xlsx"
    workbook = xlsxwriter.Workbook(excel_path)
    worksheet = workbook.add_worksheet()
    red_format = workbook.add_format({'font_color': 'red'})
    row_num = 0

    with open(chunk_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            matches = list(pattern.finditer(line))
            if not matches:
                continue

            # Word
            para = doc.add_paragraph()
            last_idx = 0
            for match in matches:
                start, end = match.span()
                if start > last_idx:
                    para.add_run(line[last_idx:start])
                red_run = para.add_run(line[start:end])
                red_run.font.color.rgb = RGBColor(255, 0, 0)
                last_idx = end
            if last_idx < len(line):
                para.add_run(line[last_idx:])

            # Excel
            rich_segments = []
            last_idx = 0
            for match in matches:
                start, end = match.span()
                if start > last_idx:
                    rich_segments.append(line[last_idx:start])
                rich_segments.append(red_format)
                rich_segments.append(line[start:end])
                last_idx = end
            if last_idx < len(line):
                rich_segments.append(line[last_idx:])

            for match in matches:
                worksheet.write(row_num, 0, match.group(), red_format)
                worksheet.write_rich_string(row_num, 1, *rich_segments)
                row_num += 1

    doc.save(f"{TEMP_DIR}/chunk_{chunk_id}.docx")
    workbook.close()

# === STEP 3: Merge DOCX files ===
def merge_word():
    merged = Document()
    part_files = sorted(f for f in os.listdir(TEMP_DIR) if f.endswith(".docx"))
    with tqdm(total=len(part_files), desc="Merging Word files") as pbar:
        for file in part_files:
            doc = Document(f"{TEMP_DIR}/{file}")
            for para in doc.paragraphs:
                merged.add_paragraph(para.text)
            pbar.update(1)
    merged.save(OUTPUT_DOCX)

# === STEP 4: Merge XLSX files ===
def merge_excel():
    from openpyxl import Workbook
    merged = Workbook()
    sheet = merged.active
    sheet.title = "Matches"
    row = 1

    part_files = sorted(f for f in os.listdir(TEMP_DIR) if f.endswith(".xlsx"))
    with tqdm(total=len(part_files), desc="Merging Excel files") as pbar:
        for file in part_files:
            wb = load_workbook(f"{TEMP_DIR}/{file}")
            ws = wb.active
            for r in ws.iter_rows(values_only=True):
                sheet.cell(row=row, column=1).value = r[0]
                sheet.cell(row=row, column=2).value = r[1]
                row += 1
            pbar.update(1)

    merged.save(OUTPUT_XLSX)

# === STEP 5: Main execution ===
if __name__ == "__main__":
    print("=== EMAIL REGEX PARALLEL EXTRACTOR ===")
    print("Input file:", INPUT_FILE)
    print("Regex used:", EMAIL_REGEX)

    split_file()

    print("\nProcessing chunks...")
    chunk_files = [f"{TEMP_DIR}/{f}" for f in os.listdir(TEMP_DIR) if f.endswith(".txt")]
    with tqdm(total=len(chunk_files), desc="Processing chunks") as pbar:
        with Pool(min(cpu_count(), len(chunk_files))) as pool:
            for _ in pool.imap_unordered(process_chunk, chunk_files):
                pbar.update(1)

    merge_word()
    merge_excel()

    print("\nCleaning up...")
    shutil.rmtree(TEMP_DIR)

    print("\nDONE!")
    print(f"Word Output : {OUTPUT_DOCX}")
    print(f"Excel Output: {OUTPUT_XLSX}")

    print("\n--- SAMPLE OUTPUT PREVIEW ---")
    print("Excel Column A: Extracted Email (red)")
    print("Excel Column B: Full log line (email(s) highlighted in red)")
    print("Word: Full matching lines with each email in red")
