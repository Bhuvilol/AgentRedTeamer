from pathlib import Path

from flask_frozen import Freezer

from app import app

BUILD_DIR = Path(__file__).resolve().parent / "build"

app.config["FREEZER_DESTINATION"] = str(BUILD_DIR)
app.config["FREEZER_REMOVE_EXTRA_FILES"] = True
app.config["FREEZER_RELATIVE_URLS"] = True

freezer = Freezer(app)

if __name__ == "__main__":
    freezer.freeze()
    pages = sorted(p.relative_to(BUILD_DIR) for p in BUILD_DIR.rglob("*.html"))
    print(f"froze {len(pages)} pages -> {BUILD_DIR}")
    for page in pages:
        print(f"  {page}")
