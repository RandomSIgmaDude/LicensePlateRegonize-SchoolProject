install YOLO

opent terminal powerchell -> run these commmands

1. ตรวจ Python และสร้าง virtual environment (แยกสภาพแวดล้อมไว้ ไลบรารีจะได้ไม่ตีกัน)
---
py --version
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
---

2. ติดตั้ง PyTorch แบบ CPU ก่อน เพราะ README ของ EasyOCR แนะนำให้ผู้ใช้ Windows ติดตั้ง torch และ torchvision ก่อน
และถ้าจะรันโหมด CPU อย่างเดียวให้เลือก CUDA = None บนหน้าเว็บ PyTorch
---
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
---

3. ติดตั้ง YOLO (ผ่าน Ultralytics) และ EasyOCR
---
pip install ultralytics easyocr
---