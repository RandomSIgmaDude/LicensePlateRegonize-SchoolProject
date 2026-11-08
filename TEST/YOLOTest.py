import sys
import re
import statistics
from difflib import SequenceMatcher
from pprint import pprint

import cv2
import numpy as np
import easyocr
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# ทำให้ print ภาษาไทยในเทอร์มินัลไม่เพี้ยน (Python 3.7+)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ----------------------------------------------------------------------
# ตั้งค่า
# ----------------------------------------------------------------------
IMAGE_PATH = "image2.jpg"
OUTPUT_PATH = "result.png"

FONT_CANDIDATES = [
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/LeelawUI.ttf",
    "C:/Windows/Fonts/leelawad.ttf",
    "/usr/share/fonts/truetype/tlwg/Loma.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Ayuthaya.ttf",
]

THAI_PROVINCES = [
    "กรุงเทพมหานคร", "กระบี่", "กาญจนบุรี", "กาฬสินธุ์", "กำแพงเพชร",
    "ขอนแก่น", "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ชัยนาท", "ชัยภูมิ",
    "ชุมพร", "เชียงราย", "เชียงใหม่", "ตรัง", "ตราด", "ตาก", "นครนายก",
    "นครปฐม", "นครพนม", "นครราชสีมา", "นครศรีธรรมราช", "นครสวรรค์",
    "นนทบุรี", "นราธิวาส", "น่าน", "บึงกาฬ", "บุรีรัมย์", "ปทุมธานี",
    "ประจวบคีรีขันธ์", "ปราจีนบุรี", "ปัตตานี", "พระนครศรีอยุธยา", "พะเยา",
    "พังงา", "พัทลุง", "พิจิตร", "พิษณุโลก", "เพชรบุรี", "เพชรบูรณ์", "แพร่",
    "ภูเก็ต", "มหาสารคาม", "มุกดาหาร", "แม่ฮ่องสอน", "ยโสธร", "ยะลา",
    "ร้อยเอ็ด", "ระนอง", "ระยอง", "ราชบุรี", "ลพบุรี", "ลำปาง", "ลำพูน",
    "เลย", "ศรีสะเกษ", "สกลนคร", "สงขลา", "สตูล", "สมุทรปราการ",
    "สมุทรสงคราม", "สมุทรสาคร", "สระแก้ว", "สระบุรี", "สิงห์บุรี", "สุโขทัย",
    "สุพรรณบุรี", "สุราษฎร์ธานี", "สุรินทร์", "หนองคาย", "หนองบัวลำภู",
    "อ่างทอง", "อำนาจเจริญ", "อุดรธานี", "อุตรดิตถ์", "อุทัยธานี",
    "อุบลราชธานี",
]


# ----------------------------------------------------------------------
# ฟังก์ชันช่วย
# ----------------------------------------------------------------------
def load_thai_font(size=24):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise RuntimeError(
        "ไม่พบฟอนต์ภาษาไทย กรุณาแก้ FONT_CANDIDATES ให้ชี้ไปที่ไฟล์ .ttf ที่รองรับภาษาไทย"
    )


def draw_thai_labels(frame_bgr, labels, font, color_rgb=(0, 255, 0)):
    """วาดข้อความหลายอันลงภาพในครั้งเดียว (cv2.putText วาดภาษาไทยไม่ได้)"""
    if not labels:
        return frame_bgr
    img_pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    for text, (x, y) in labels:
        draw.text((x, max(y, 0)), text, font=font, fill=color_rgb)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def group_into_lines(res):
    """จัดผล OCR เป็นบรรทัด (บนลงล่าง) และเรียงซ้ายไปขวาในแต่ละบรรทัด"""
    items = []
    for bbox, text, conf in res:
        ys = [p[1] for p in bbox]
        xs = [p[0] for p in bbox]
        items.append({
            "cy": sum(ys) / len(ys),
            "h": max(ys) - min(ys),
            "top": min(ys),
            "bottom": max(ys),
            "x": min(xs),
            "text": text,
            "conf": conf,
        })
    items.sort(key=lambda i: i["cy"])

    threshold = 0.5 * max(i["h"] for i in items)
    lines = []
    for it in items:
        if lines and abs(it["cy"] - lines[-1]["cy"]) < threshold:
            lines[-1]["items"].append(it)
            lines[-1]["cy"] = statistics.mean(i["cy"] for i in lines[-1]["items"])
        else:
            lines.append({"cy": it["cy"], "items": [it]})

    result = []
    for ln in lines:
        ln["items"].sort(key=lambda i: i["x"])
        result.append({
            "text": " ".join(i["text"] for i in ln["items"]),
            "top": min(i["top"] for i in ln["items"]),
            "bottom": max(i["bottom"] for i in ln["items"]),
        })
    return result


def clean_plate_number(text):
    # เหลือเฉพาะ ตัวเลข, ตัวอักษรไทย, ช่องว่าง
    text = re.sub(r"[^0-9\u0E00-\u0E7F ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


PROVINCE_MIN_SCORE = 0.45  # ความคล้ายขั้นต่ำที่ยอมรับว่าเป็นจังหวัดนั้น ๆ
PROVINCE_CHARS = "".join(sorted(set("".join(THAI_PROVINCES))))
PLATE_CHARS = "0123456789กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"
PLATE_PATTERN = re.compile(r"^\d?[\u0E01-\u0E2E]{1,3} ?\d{1,4}$")


def match_province(raw):
    """คืน (ชื่อจังหวัดที่ใกล้ที่สุด, คะแนนความคล้าย 0-1)"""
    thai_only = re.sub(r"[^\u0E00-\u0E7F]", "", raw)
    if not thai_only:
        return "", 0.0
    name, score = max(
        ((p, SequenceMatcher(None, thai_only, p).ratio()) for p in THAI_PROVINCES),
        key=lambda x: x[1],
    )
    if score >= PROVINCE_MIN_SCORE:
        return name, score
    return thai_only, score  # ไม่คล้ายจังหวัดไหนพอ -> คืนข้อความที่อ่านได้


def make_variants(crop_gray, scale=3):
    """สร้างภาพหลายแบบ (ขยาย / เพิ่มคอนทราสต์ / ขาวดำ / กลับสี) ให้ OCR ลองอ่าน"""
    big = cv2.resize(crop_gray, None, fx=scale, fy=scale,
                     interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(big)
    _, otsu = cv2.threshold(clahe, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return [big, clahe, otsu, cv2.bitwise_not(otsu)]


def ocr_line(img, allowlist):
    """OCR ภาพบรรทัดเดียวด้วย allowlist คืน (ข้อความเรียงซ้ายไปขวา, ค่าเฉลี่ย conf)"""
    out = reader.readtext(img, allowlist=allowlist)
    if not out:
        return "", 0.0
    out.sort(key=lambda o: min(p[0] for p in o[0]))
    text = " ".join(t for _, t, _ in out)
    conf = sum(c for _, _, c in out) / len(out)
    return text, conf


def crop_rows(gray, top, bottom):
    h = gray.shape[0]
    pad = int(0.15 * max(bottom - top, 10))
    top = max(int(top) - pad, 0)
    bottom = min(int(bottom) + pad, h)
    return gray[top:bottom, :]


def read_province(gray, lines, province_raw):
    """อ่านจังหวัดซ้ำจากแถบล่างของป้าย แล้วเลือกผลที่คล้ายชื่อจังหวัดจริงที่สุด"""
    h = gray.shape[0]
    if len(lines) > 1:
        top = min(l["top"] for l in lines[1:])
        bottom = max(l["bottom"] for l in lines[1:])
    else:  # OCR รอบแรกไม่เจอบรรทัดจังหวัด -> เดาว่าอยู่ล่างสุดของป้าย
        top, bottom = h * 0.65, h

    crop = crop_rows(gray, top, bottom)
    candidates = [province_raw]
    if crop.size:
        for v in make_variants(crop):
            text, _ = ocr_line(v, PROVINCE_CHARS)
            candidates.append(text)

    best_name, best_score = "", -1.0
    for c in candidates:
        name, score = match_province(c)
        if score > best_score:
            best_name, best_score = name, score
    return best_name, best_score


def read_plate_number(gray, lines):
    """อ่านเลขทะเบียนซ้ำ โดยจำกัดให้เป็นตัวเลข + พยัญชนะไทย (ป้ายไม่มีสระ/วรรณยุกต์)"""
    first_pass = clean_plate_number(lines[0]["text"])
    crop = crop_rows(gray, lines[0]["top"], lines[0]["bottom"])
    if crop.size == 0:
        return first_pass

    best_text, best_conf = "", 0.0
    for v in make_variants(crop):
        text, conf = ocr_line(v, PLATE_CHARS)
        text = re.sub(r"\s+", " ", text).strip()
        if PLATE_PATTERN.match(text) and conf > best_conf:
            best_text, best_conf = text, conf
    return best_text or first_pass


# ----------------------------------------------------------------------
# โหลดโมเดล (โหลดครั้งเดียวนอกลูป)
# ----------------------------------------------------------------------
car_model = YOLO("yolov10n.pt")
plate_model = YOLO("models/plate_detector/license-plate-finetune-v1n.pt")
reader = easyocr.Reader(["th", "en"], gpu=False)
thai_font = load_thai_font(24)

best = {}  # {car_id: {...ข้อมูลป้ายที่ดีที่สุด...}}

# ----------------------------------------------------------------------
# ประมวลผล
# ----------------------------------------------------------------------
for r in car_model.predict(source=IMAGE_PATH, classes=[2, 5, 7],
                           device="cpu", verbose=False):

    frame = r.orig_img.copy()
    labels = []  # เก็บข้อความไว้วาดทีเดียวตอนท้าย

    for car_id, box in enumerate(r.boxes.xyxy):
        x1, y1, x2, y2 = map(int, box)
        car = frame[y1:y2, x1:x2]

        if car.size == 0:
            continue

        # ตรวจหาป้ายทะเบียนในรถ
        pr = plate_model(car, device="cpu", conf=0.3, verbose=False)[0]

        for pb in pr.boxes:
            px1, py1, px2, py2 = map(int, pb.xyxy[0])
            plate = car[py1:py2, px1:px2]

            if plate.size == 0:
                continue

            # เตรียมภาพก่อน OCR
            plate = cv2.resize(plate, None, fx=2, fy=2,
                               interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
            res = reader.readtext(gray, add_margin=0.2)

            if not res:
                continue

            conf = float(sum(c for _, _, c in res) / len(res))

            # แยกบรรทัด: บรรทัดแรก = เลขทะเบียน, บรรทัดที่เหลือ = จังหวัด
            lines = group_into_lines(res)
            province_raw = " ".join(l["text"] for l in lines[1:])
            plate_number = read_plate_number(gray, lines)
            province, province_score = read_province(gray, lines, province_raw)

            if car_id not in best or conf > best[car_id]["confidence"]:
                best[car_id] = {
                    "plate_number": plate_number,
                    "province": province,
                    "province_raw": province_raw,
                    "province_score": round(province_score, 3),
                    "confidence": round(conf, 4),
                    "plate_detect_conf": round(float(pb.conf[0]), 4),
                    "car_box": [x1, y1, x2, y2],
                    "plate_box": [x1 + px1, y1 + py1, x1 + px2, y1 + py2],
                }

            # วาดกรอบป้ายทะเบียน
            cv2.rectangle(frame, (x1 + px1, y1 + py1),
                          (x1 + px2, y1 + py2), (0, 255, 0), 2)

            label = f"{plate_number} {province}".strip()
            labels.append((label, (x1 + px1, y1 + py1 - 35)))

        # วาดกรอบรถ
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # วาดข้อความภาษาไทยด้วย Pillow
    frame = draw_thai_labels(frame, labels, thai_font)

    cv2.imwrite(OUTPUT_PATH, frame)

    print("\n===== RESULT (dict) =====")
    pprint(best, sort_dicts=False)

    cv2.imshow("License Plate Recognition", frame)
    cv2.waitKey(0)


cv2.destroyAllWindows()

# ----------------------------------------------------------------------
# พิมพ์ผลลัพธ์เป็น dictionary
# ----------------------------------------------------------------------
