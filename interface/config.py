from pathlib import Path


BACKENDS = ["python", "rust", "cpp", "java", "csharp", "js"]
IMAGE_EXTS = {".png", ".pgm", ".ppm", ".jpg", ".jpeg"}
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT_DIR / "sample_series" / "IM-0001-0001.dcm"
DEFAULT_SERIES = ROOT_DIR / "sample_series"
OUTPUT_DIR = ROOT_DIR / "output"
