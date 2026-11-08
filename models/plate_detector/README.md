---
license: mit
tags:
- yolov11
- license-plate
- object-detection
- computer-vision
- ultralytics
---

# License Plate Detector

YOLOv11-based license plate detector used in **Project Argus**, a vehicle recognition pipeline.

## Description

This model detects license plates within cropped vehicle images. It is designed to be used after vehicle detection and tracking, before OCR.

Pipeline:

Vehicle Detection → Vehicle Tracking → License Plate Detection → OCR → Vehicle Classification

## Usage

Download:

```bash
hf download Nuurrr66/license-plate-detector \
    --local-dir models/plate_detector
```

The downloaded file should be:

```
models/
└── plate_detector/
    └── license-plate-finetune-v1n.pt
```

## Used in

Project Argus – Vehicle Recognition System