# Project Structure

```text
DEV_AI/
├── app.py
├── hospital_app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   └── services/
│       ├── __init__.py
│       ├── audio_worker.py
│       └── camera.py
├── models/
│   └── best.pt
├── static/
│   └── style.css
├── templates/
│   └── index.html
├── training/
│   ├── 01_extract_frames.py
│   ├── 02_package_dataset.py
│   ├── colab_train.ipynb
│   └── README.md
├── dataset/
│   └── data.yaml
├── data/
│   ├── raw_videos/
│   └── frames/
├── docs/
│   ├── STRUCTURE.md
│   ├── TRAINING_GUIDE.md
│   ├── FILMING_PROTOCOL.md
│   └── PIPELINE_COMPARISON.md
└── requirements.txt
```

- `app.py`: Uvicorn entrypoint.
- `hospital_app/main.py`: FastAPI app, routes, runtime lifecycle.
- `hospital_app/services/camera.py`: YOLO + OpenCV + anti-flicker + dwell logic.
- `hospital_app/services/audio_worker.py`: pyttsx3 queue worker and SOS loop.
- `training/`: pipeline train YOLO (video -> frames -> Roboflow -> Colab -> best.pt).

