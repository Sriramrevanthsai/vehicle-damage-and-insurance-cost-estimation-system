from ultralytics import YOLO
from pathlib import Path

# Get absolute path to backend directory
BASE_DIR = Path(__file__).resolve().parent

# Absolute path to model
MODEL_PATH = BASE_DIR / "models" / "best.pt"

print("Loading model from:", MODEL_PATH)

model = YOLO(str(MODEL_PATH))

results = model.predict(
    source=str(Path("test_images/image.png")),
    conf=0.3,
    save=True
)

print("Prediction complete.")
