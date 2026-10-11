"""Create temporary labelled contact sheets for independent visual review."""
from pathlib import Path

from PIL import Image, ImageDraw

from phase1d_visual_manifest import ROOT, SCREENSHOTS, STATE_NAMES


OUTPUT = Path("/tmp/ampyan_phase1d_review_sheets")
VIEWPORTS = ("360x800", "390x844", "768x1024", "1024x768", "1440x900")
CELL_WIDTH = 700
LABEL_HEIGHT = 42


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for state_number, state in enumerate(STATE_NAMES, 1):
        panels = []
        for viewport in VIEWPORTS:
            source = SCREENSHOTS / f"{state}-{viewport}.png"
            with Image.open(source) as image:
                rendered = image.convert("RGB")
                height = round(rendered.height * CELL_WIDTH / rendered.width)
                rendered = rendered.resize((CELL_WIDTH, height))
            panel = Image.new("RGB", (CELL_WIDTH, LABEL_HEIGHT + height), "white")
            ImageDraw.Draw(panel).text(
                (12, 12), f"{state} — {viewport}", fill="black"
            )
            panel.paste(rendered, (0, LABEL_HEIGHT))
            panels.append(panel)
        sheet_height = max(panel.height for panel in panels)
        sheet = Image.new(
            "RGB", (CELL_WIDTH * len(panels), sheet_height), "#777777"
        )
        for index, panel in enumerate(panels):
            sheet.paste(panel, (index * CELL_WIDTH, 0))
        sheet.save(OUTPUT / f"{state_number:02d}-{state}.jpg", quality=88)
    state_sheets = sorted(OUTPUT.glob("[0-9][0-9]-*.jpg"))
    for group_number, offset in enumerate(range(0, len(state_sheets), 5), 1):
        images = []
        for path in state_sheets[offset:offset + 5]:
            with Image.open(path) as image:
                rendered = image.convert("RGB")
                rendered = rendered.resize(
                    (1750, round(rendered.height * 1750 / rendered.width))
                )
                images.append(rendered)
        combined = Image.new(
            "RGB",
            (max(image.width for image in images), sum(image.height for image in images)),
            "#555555",
        )
        top = 0
        for image in images:
            combined.paste(image, (0, top))
            top += image.height
        combined.save(OUTPUT / f"group-{group_number}.jpg", quality=86)
    print(
        f"review_sheets={len(state_sheets)} "
        f"groups={len(list(OUTPUT.glob('group-*.jpg')))} output={OUTPUT}"
    )


if __name__ == "__main__":
    build()
