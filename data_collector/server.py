"""
Urdu Child Speech Data Collector — Local Server with TAAPU & Excel Export

Runs a local web server at http://localhost:8000.
Endpoints:
1. POST /api/save_audio: Saves .webm/.wav audio recording for a child word.
2. POST /api/save_evaluation: Saves pronunciation correctness, response type, error reasons & phoneme details.
3. POST /api/export_excel: Generates & saves a formatted Excel (.xlsx) file with child info and word evaluations.
4. GET /api/download_excel: Downloads the Excel file for a child session.
"""

import os
import sys
import json
import re
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import urllib.parse

# Add project root to sys.path for model imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RECORDINGS_DIR = BASE_DIR / "recordings"

# Try loading openpyxl for Excel generation
EXCEL_AVAILABLE = False
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    EXCEL_AVAILABLE = True
    print("[+] openpyxl loaded successfully for Excel export!")
except Exception as e:
    print(f"[!] openpyxl import warning: {e}")

# Try loading GOP pipeline
GOP_AVAILABLE = False
ENABLE_ML_GOP = True  # Can be toggled via CLI (--no-gop) or per-request from web UI
try:
    from testing.gop import run_gop_pipeline
    GOP_AVAILABLE = True
    print("[+] ML GOP & Forced Alignment Model loaded successfully!")
except Exception as e:
    print(f"[!] GOP Model import warning: {e}")

def get_take_folder(child_dir, take_no):
    """
    Returns Path object for recordings/{child_id}/take {take_no}
    """
    take_str = str(take_no).strip()
    folder_name = f"take {take_str}"
    save_folder = RECORDINGS_DIR / child_dir / folder_name
    save_folder.mkdir(parents=True, exist_ok=True)
    return save_folder

def create_excel_report(child_info, evaluations, save_path):
    """
    Generates a beautifully styled TAAPU Excel (.xlsx) file organized by Consonant & Word Position (Start/Middle/End).
    """
    if not EXCEL_AVAILABLE:
        print("[!] openpyxl is not available to generate Excel file.")
        return False

    wb = openpyxl.Workbook()
    
    # ----------------------------------------------------
    # Sheet 1: Session Overview & Child Profile
    # ----------------------------------------------------
    ws_summary = wb.active
    ws_summary.title = "Child Session Summary"
    ws_summary.views.sheetView[0].showGridLines = True

    # Header styling
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Blue
    header_font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    
    ws_summary.merge_cells("A1:F1")
    cell_title = ws_summary["A1"]
    cell_title.value = "Urdu TAAPU Child Speech Assessment Report (Consonant & Position Breakdown)"
    cell_title.font = header_font
    cell_title.fill = header_fill
    cell_title.alignment = Alignment(horizontal="center", vertical="center")
    ws_summary.row_dimensions[1].height = 40

    # Meta Section
    meta_label_fill = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")
    label_font = Font(name="Calibri", size=11, bold=True, color="0F172A")
    val_font = Font(name="Calibri", size=11, color="1E293B")
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    child_name = child_info.get("name", "N/A")
    child_age = child_info.get("age", "N/A")
    child_id = child_info.get("id", "Child_001")
    take_no = child_info.get("take", "1")
    session_date = child_info.get("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    metadata_items = [
        ("Child ID:", child_id),
        ("Child Name:", child_name),
        ("Child Age:", str(child_age)),
        ("Session Take:", f"Take {take_no}"),
        ("Assessment Date:", session_date)
    ]

    for idx, (lbl, val) in enumerate(metadata_items, start=3):
        ws_summary.cell(row=idx, column=1, value=lbl).font = label_font
        ws_summary.cell(row=idx, column=1).fill = meta_label_fill
        ws_summary.cell(row=idx, column=1).border = border_thin
        ws_summary.cell(row=idx, column=2, value=val).font = val_font
        ws_summary.cell(row=idx, column=2).border = border_thin

    # ----------------------------------------------------
    # Metrics calculation: SLP Clinician vs ML GOP Model Weighted Hybrid
    # Ensemble Weights: 70% SLP Clinician + 30% ML GOP Model
    # ----------------------------------------------------
    total_words = len(evaluations) if len(evaluations) > 0 else 58
    recorded_count = sum(1 for e in evaluations.values() if e.get("recorded"))
    evaluated_count = sum(1 for e in evaluations.values() if e.get("status") in ["correct", "incorrect"])

    W_SLP = 0.70
    W_ML = 0.30

    def calc_position_stats(word_list):
        if not word_list:
            return (0.0, 100.0, 0.0, 100.0, 0.0, 100.0, 0)
        
        c_eval = [e for e in word_list if e.get("status") in ["correct", "incorrect"]]
        if not c_eval:
            return (0.0, 100.0, 0.0, 100.0, 0.0, 100.0, 0)

        slp_corr = sum(1 for e in c_eval if e.get("status") == "correct")
        slp_acc = (slp_corr / len(c_eval)) * 100.0
        slp_err = 100.0 - slp_acc

        ml_clean = 0
        ml_cnt = 0
        w_sum = 0.0

        for e in c_eval:
            s_slp = 1.0 if e.get("status") == "correct" else 0.0
            
            gop_res = e.get("gop_results", {})
            gop_flag = str(e.get("gopFlag", ""))
            
            s_ml = s_slp
            has_ml = False
            
            if isinstance(gop_res, dict) and "incorrect_count" in gop_res:
                has_ml = True
                ml_cnt += 1
                if gop_res.get("incorrect_count", 0) == 0:
                    ml_clean += 1
                    s_ml = 1.0
                else:
                    s_ml = 0.0
            elif "Mispronounced" in gop_flag:
                has_ml = True
                ml_cnt += 1
                s_ml = 0.0
            elif "Clean" in gop_flag or "GOP:" in gop_flag:
                has_ml = True
                ml_cnt += 1
                ml_clean += 1
                s_ml = 1.0

            w_word = (W_SLP * s_slp) + (W_ML * s_ml) if has_ml else s_slp
            w_sum += w_word

        ml_acc = (ml_clean / ml_cnt * 100.0) if ml_cnt > 0 else slp_acc
        ml_err = 100.0 - ml_acc

        hybrid_acc = (w_sum / len(c_eval)) * 100.0
        hybrid_err = 100.0 - hybrid_acc

        return (round(slp_acc, 1), round(slp_err, 1), round(ml_acc, 1), round(ml_err, 1), round(hybrid_acc, 1), round(hybrid_err, 1), len(c_eval))

    all_eval_words = list(evaluations.values())
    init_words = [e for e in all_eval_words if "Start" in str(e.get("position", ""))]
    med_words = [e for e in all_eval_words if "Middle" in str(e.get("position", ""))]
    fin_words = [e for e in all_eval_words if "End" in str(e.get("position", ""))]

    overall_stats = calc_position_stats(all_eval_words)
    init_stats = calc_position_stats(init_words)
    med_stats = calc_position_stats(med_words)
    fin_stats = calc_position_stats(fin_words)

    # Write Metadata & Hybrid Settings
    metadata_items = [
        ("Child ID:", child_id),
        ("Child Name:", child_name),
        ("Child Age:", str(child_age)),
        ("Session Take:", f"Take {take_no}"),
        ("Assessment Date:", session_date),
        ("Audio Recordings Completed:", f"{recorded_count} / {total_words}"),
        ("Ensemble Model Weighting:", "70% SLP Clinician + 30% ML GOP Model")
    ]

    for idx, (lbl, val) in enumerate(metadata_items, start=3):
        ws_summary.cell(row=idx, column=1, value=lbl).font = label_font
        ws_summary.cell(row=idx, column=1).fill = meta_label_fill
        ws_summary.cell(row=idx, column=1).border = border_thin
        ws_summary.cell(row=idx, column=2, value=val).font = val_font
        ws_summary.cell(row=idx, column=2).border = border_thin

    # Hybrid Summary Table Title
    ws_summary.cell(row=11, column=1, value="CLINICIAN + ML GOP HYBRID ACCURACY & FAILURE ANALYSIS").font = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
    
    # Table Headers
    table_headers = ["Assessment Metric / Position", "SLP Clinician Score", "ML GOP Model Score", "Weighted Hybrid Score (70% SLP + 30% ML)"]
    ws_summary.row_dimensions[12].height = 26
    for col_idx, th in enumerate(table_headers, start=1):
        c = ws_summary.cell(row=12, column=col_idx, value=th)
        c.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin

    # Rows Data
    metrics_table_rows = [
        ("Overall Accuracy Rate", f"{overall_stats[0]}%", f"{overall_stats[2]}%", f"{overall_stats[4]}%"),
        ("Overall Failure / Error Rate", f"{overall_stats[1]}%", f"{overall_stats[3]}%", f"{overall_stats[5]}%"),
        ("Initial Position (Start) Accuracy", f"{init_stats[0]}%", f"{init_stats[2]}%", f"{init_stats[4]}%"),
        ("Initial Position (Start) Failure Rate", f"{init_stats[1]}%", f"{init_stats[3]}%", f"{init_stats[5]}%"),
        ("Medial Position (Middle) Accuracy", f"{med_stats[0]}%", f"{med_stats[2]}%", f"{med_stats[4]}%"),
        ("Medial Position (Middle) Failure Rate", f"{med_stats[1]}%", f"{med_stats[3]}%", f"{med_stats[5]}%"),
        ("Final Position (End) Accuracy", f"{fin_stats[0]}%", f"{fin_stats[2]}%", f"{fin_stats[4]}%"),
        ("Final Position (End) Failure Rate", f"{fin_stats[1]}%", f"{fin_stats[3]}%", f"{fin_stats[5]}%")
    ]

    for row_offset, row_data in enumerate(metrics_table_rows, start=13):
        ws_summary.row_dimensions[row_offset].height = 22
        for col_idx, val in enumerate(row_data, start=1):
            c = ws_summary.cell(row=row_offset, column=col_idx, value=val)
            c.border = border_thin
            c.font = Font(name="Calibri", size=10, bold=(col_idx==4))
            if col_idx == 1:
                c.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
                c.alignment = Alignment(horizontal="left", vertical="center")
            else:
                if "Failure" in row_data[0] or "Error" in row_data[0]:
                    c.fill = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
                    c.font = Font(name="Calibri", size=10, bold=(col_idx==4), color="991B1B")
                else:
                    c.fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
                    c.font = Font(name="Calibri", size=10, bold=(col_idx==4), color="166534")
                c.alignment = Alignment(horizontal="center", vertical="center")

    ws_summary.column_dimensions['A'].width = 38
    ws_summary.column_dimensions['B'].width = 24
    ws_summary.column_dimensions['C'].width = 24
    ws_summary.column_dimensions['D'].width = 36

    # ----------------------------------------------------
    # Sheet 2: Word-by-Word TAAPU Evaluation Details
    # ----------------------------------------------------
    ws_detail = wb.create_sheet(title="TAAPU Word Evaluations")
    ws_detail.views.sheetView[0].showGridLines = True

    columns = [
        "Word ID",
        "Urdu Word",
        "Transliteration",
        "English Meaning",
        "Target Consonant",
        "Phonetic Position (Start/Middle/End)",
        "Response Type",
        "Audio Recorded",
        "Pronunciation Status",
        "Incorrect Phonemes",
        "Error Type / Reason",
        "Substituted Sound",
        "Phonological Processes",
        "SLP Clinician Notes",
        "ML GOP Analysis",
        "Audio File Path"
    ]

    ws_detail.row_dimensions[1].height = 28
    for col_num, col_title in enumerate(columns, start=1):
        cell = ws_detail.cell(row=1, column=col_num, value=col_title)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid") # Royal Blue
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Styles for status rows
    correct_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Soft Green
    incorrect_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # Soft Red

    for w_id in range(1, total_words + 1):
        e_data = evaluations.get(str(w_id), evaluations.get(w_id, {}))
        
        urdu = e_data.get("urdu", "")
        trans = e_data.get("transliteration", "")
        meaning = e_data.get("meaning", "")
        consonant = e_data.get("consonant", e_data.get("target", ""))
        position = e_data.get("position", "Initial (Start)")
        resp_type = (e_data.get("responseType") or "spontaneous").capitalize()
        recorded = "Yes" if e_data.get("recorded") else "No"
        status = e_data.get("status", "correct").capitalize()
        
        incorrect_ph = e_data.get("incorrectPhonemes", [])
        if isinstance(incorrect_ph, list):
            incorrect_str = ", ".join(incorrect_ph) if incorrect_ph else ("None" if status == "Correct" else "")
        else:
            incorrect_str = str(incorrect_ph)

        error_reasons = e_data.get("errorReasons", [])
        if isinstance(error_reasons, list):
            error_reason_str = ", ".join(error_reasons) if error_reasons else ("None" if status == "Correct" else "")
        else:
            error_reason_str = str(error_reasons)

        subst_sound = e_data.get("substitutedSound", "")
        
        phono_processes = e_data.get("phonologicalProcesses", [])
        if isinstance(phono_processes, list):
            phono_proc_str = ", ".join(phono_processes) if phono_processes else ""
        else:
            phono_proc_str = str(phono_processes)

        notes = e_data.get("notes", "")
        gop_flag = e_data.get("gopFlag", "")
        audio_file = e_data.get("audioFile", "")

        row_num = w_id + 1
        ws_detail.row_dimensions[row_num].height = 22

        row_values = [
            w_id,
            urdu,
            trans,
            meaning,
            consonant,
            position,
            resp_type,
            recorded,
            status,
            incorrect_str,
            error_reason_str,
            subst_sound,
            phono_proc_str,
            notes,
            gop_flag,
            audio_file
        ]

        for col_num, val in enumerate(row_values, start=1):
            cell = ws_detail.cell(row=row_num, column=col_num, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.border = border_thin

            if col_num in [1, 5, 6, 7, 8, 9]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            # Color coding status cell
            if col_num == 9:
                if status == "Correct":
                    cell.fill = correct_fill
                    cell.font = Font(name="Calibri", size=10, bold=True, color="166534")
                elif status == "Incorrect":
                    cell.fill = incorrect_fill
                    cell.font = Font(name="Calibri", size=10, bold=True, color="991B1B")

    # Auto-fit column widths for Sheet 2
    for col in ws_detail.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            max_len = max(max_len, len(val_str))
        ws_detail.column_dimensions[col_letter].width = max(max_len + 4, 14)

    # ----------------------------------------------------
    # Sheet 3: ML GOP Phoneme Breakdown & Forced Alignment Metrics
    # ----------------------------------------------------
    ws_gop = wb.create_sheet(title="ML GOP Detailed Analysis")
    ws_gop.views.sheetView[0].showGridLines = True

    gop_cols = ["Word ID", "Urdu Word", "Transliteration", "Target Phoneme", "GOP Margin Score", "ML Status"]
    ws_gop.row_dimensions[1].height = 28
    for col_num, col_title in enumerate(gop_cols, start=1):
        cell = ws_gop.cell(row=1, column=col_num, value=col_title)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="475569", end_color="475569", fill_type="solid") # Slate Gray
        cell.alignment = Alignment(horizontal="center", vertical="center")

    gop_row_idx = 2
    for w_id in range(1, total_words + 1):
        e_data = evaluations.get(str(w_id), evaluations.get(w_id, {}))
        urdu = e_data.get("urdu", "")
        trans = e_data.get("transliteration", "")
        gop_res = e_data.get("gop_results", {})
        ph_details = gop_res.get("phoneme_details", []) if isinstance(gop_res, dict) else []

        if ph_details:
            for p in ph_details:
                phone = p.get("phone", "")
                margin = p.get("gop_margin", None)
                incorrect = p.get("incorrect", False)
                status_str = "⚠️ MISPRONOUNCED" if incorrect else "✅ OK"
                margin_str = f"{margin:.3f}" if margin is not None else "N/A"

                ws_gop.row_dimensions[gop_row_idx].height = 20
                ws_gop.cell(row=gop_row_idx, column=1, value=w_id).border = border_thin
                ws_gop.cell(row=gop_row_idx, column=2, value=urdu).border = border_thin
                ws_gop.cell(row=gop_row_idx, column=3, value=trans).border = border_thin
                ws_gop.cell(row=gop_row_idx, column=4, value=phone).border = border_thin
                ws_gop.cell(row=gop_row_idx, column=5, value=margin_str).border = border_thin
                
                st_cell = ws_gop.cell(row=gop_row_idx, column=6, value=status_str)
                st_cell.border = border_thin
                st_cell.alignment = Alignment(horizontal="center", vertical="center")
                if incorrect:
                    st_cell.fill = incorrect_fill
                    st_cell.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
                else:
                    st_cell.fill = correct_fill
                    st_cell.font = Font(name="Calibri", size=10, bold=True, color="166534")

                gop_row_idx += 1
        else:
            # Word evaluated manually without GOP
            ws_gop.row_dimensions[gop_row_idx].height = 20
            ws_gop.cell(row=gop_row_idx, column=1, value=w_id).border = border_thin
            ws_gop.cell(row=gop_row_idx, column=2, value=urdu).border = border_thin
            ws_gop.cell(row=gop_row_idx, column=3, value=trans).border = border_thin
            ws_gop.cell(row=gop_row_idx, column=4, value="-").border = border_thin
            ws_gop.cell(row=gop_row_idx, column=5, value="-").border = border_thin
            ws_gop.cell(row=gop_row_idx, column=6, value="Manual SLP Mode (No ML GOP)").border = border_thin
            gop_row_idx += 1

    for col in ws_gop.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            max_len = max(max_len, len(val_str))
        ws_gop.column_dimensions[col_letter].width = max(max_len + 4, 16)

    wb.save(save_path)
    print(f"[+] Saved TAAPU Excel Report: {save_path}")
    return True

class DataCollectorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/download_excel":
            self.handle_download_excel(parsed_url.query)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/save_audio":
            self.handle_save_audio()
        elif self.path == "/api/save_evaluation":
            self.handle_save_evaluation()
        elif self.path == "/api/export_excel":
            self.handle_export_excel()
        else:
            self.send_error(404, "Endpoint Not Found")

    def handle_save_audio(self):
        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Expected multipart/form-data"}')
                return

            boundary = content_type.split("boundary=")[-1].encode("utf-8")
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            parts = body.split(b"--" + boundary)
            fields = {}
            file_data = None
            filename = "recording.webm"

            for part in parts:
                if not part or part == b"--\r\n":
                    continue
                header_data, _, body_data = part.partition(b"\r\n\r\n")
                body_data = body_data.rstrip(b"\r\n")
                header_str = header_data.decode("utf-8", errors="ignore")

                if 'name="audio"' in header_str:
                    match = re.search(r'filename="([^"]+)"', header_str)
                    if match:
                        filename = match.group(1)
                    file_data = body_data
                else:
                    match = re.search(r'name="([^"]+)"', header_str)
                    if match:
                        field_name = match.group(1)
                        fields[field_name] = body_data.decode("utf-8", errors="ignore")

            child_id = fields.get("child_id", "Child_001").strip()
            take_no = fields.get("take_no", "1").strip()
            word_id = fields.get("word_id", "1").strip()
            word_urdu = fields.get("word_urdu", "").strip()
            transliteration = fields.get("transliteration", "word").strip()

            child_dir = re.sub(r'[^\w\-]', '_', child_id)
            save_folder = get_take_folder(child_dir, take_no)

            out_filename = f"{int(word_id):02d}_{transliteration}.webm"
            out_path = save_folder / out_filename

            if file_data:
                with open(out_path, "wb") as f:
                    f.write(file_data)
                print(f"[+] Saved audio recording: {out_path}")

            # GOP Analysis if enabled
            gop_results = None
            req_enable_gop = fields.get("enable_gop", "true").strip().lower() in ("true", "1", "yes")
            if GOP_AVAILABLE and ENABLE_ML_GOP and req_enable_gop and word_urdu and out_path.exists():
                try:
                    raw_gop = run_gop_pipeline(str(out_path), word_urdu, is_raw_phonemes=False)
                    incorrect_phonemes = []
                    phoneme_details = []
                    for r in raw_gop:
                        phone = r["phone"]
                        gop_margin = r["gop_margin"]
                        is_mispronounced = "MISPRONOUNCED" in r.get("flag", "") or (gop_margin is not None and gop_margin < 0.0)
                        if is_mispronounced:
                            incorrect_phonemes.append(phone)
                        phoneme_details.append({
                            "phone": phone,
                            "gop_margin": round(gop_margin, 3) if gop_margin is not None else None,
                            "incorrect": is_mispronounced
                        })
                    gop_results = {
                        "word_id": int(word_id),
                        "incorrect_phonemes": incorrect_phonemes,
                        "phoneme_details": phoneme_details,
                        "incorrect_count": len(incorrect_phonemes)
                    }
                except Exception as ex:
                    print(f"[!] Real-time GOP warning: {ex}")

            response_data = json.dumps({
                "status": "success",
                "saved_path": str(out_path.relative_to(BASE_DIR)),
                "gop_results": gop_results
            }, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data)

        except Exception as e:
            print(f"[!] Error saving audio: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode("utf-8"))

    def handle_save_evaluation(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            child_info = payload.get("child_info", {})
            evaluations = payload.get("evaluations", {})

            child_id = child_info.get("id", "Child_001")
            take_no = child_info.get("take", "1")

            child_dir = re.sub(r'[^\w\-]', '_', child_id)
            save_folder = get_take_folder(child_dir, take_no)

            # Save Excel Report (.xlsx) only (JSON file creation disabled)
            excel_filename = f"Session_{child_dir}_take_{take_no}.xlsx"
            excel_path = save_folder / excel_filename
            excel_created = create_excel_report(child_info, evaluations, excel_path)

            rel_excel_path = str(excel_path.relative_to(BASE_DIR)) if excel_created else None

            response_data = json.dumps({
                "status": "success",
                "excel_path": rel_excel_path,
                "excel_download_url": f"/api/download_excel?child_id={urllib.parse.quote(child_id)}&take={take_no}"
            }, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(response_data)

        except Exception as e:
            print(f"[!] Error saving evaluation: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode("utf-8"))

    def handle_export_excel(self):
        self.handle_save_evaluation()

    def handle_download_excel(self, query_string):
        try:
            params = urllib.parse.parse_qs(query_string)
            child_id = params.get("child_id", ["Child_001"])[0]
            take_no = params.get("take", ["1"])[0]

            child_dir = re.sub(r'[^\w\-]', '_', child_id)
            save_folder = get_take_folder(child_dir, take_no)
            excel_path = save_folder / f"Session_{child_dir}_take_{take_no}.xlsx"

            if not excel_path.exists():
                self.send_error(404, "Excel file not found. Please save evaluation first.")
                return

            with open(excel_path, "rb") as f:
                excel_bytes = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", f'attachment; filename="{excel_path.name}"')
            self.send_header("Content-Length", str(len(excel_bytes)))
            self.end_headers()
            self.wfile.write(excel_bytes)

        except Exception as e:
            print(f"[!] Error serving download: {e}")
            self.send_error(500, str(e))

def run_server(port=8000, enable_gop=True):
    global ENABLE_ML_GOP
    ENABLE_ML_GOP = enable_gop
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    server_address = ("", port)
    httpd = HTTPServer(server_address, DataCollectorHandler)
    print("=" * 70)
    print(f"🎙️  Urdu Child Speech Data Collector & TAAPU Excel Assessment Server!")
    print(f"👉 Open in browser: http://localhost:{port}")
    print(f"📂 Record & Excel output path: {RECORDINGS_DIR}")
    print(f"🤖 Real-time ML GOP Analysis: {'ENABLED' if ENABLE_ML_GOP and GOP_AVAILABLE else 'DISABLED'}")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    port = 8000
    enable_gop = True
    for arg in sys.argv[1:]:
        if arg.isdigit():
            port = int(arg)
        elif arg.lower() in ("--no-gop", "--disable-gop", "--manual"):
            enable_gop = False
        elif arg.lower() in ("--gop", "--enable-gop"):
            enable_gop = True
    run_server(port=port, enable_gop=enable_gop)
