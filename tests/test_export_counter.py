import os
import shutil
import sys
# Ensure project root is on sys.path so `processing` package can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from processing.counter import VehicleLogger

OUTPUT_DIR = "outputs/test_reports"


def setup_dir():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_export():
    setup_dir()

    logger = VehicleLogger(fps=30.0)

    # Thêm một số bản ghi mẫu
    logger.add_log(track_id=1, class_id=2, direction="Entry", frame_number=30, confidence=0.95)
    logger.add_log(track_id=2, class_id=3, direction="Exit", frame_number=60, confidence=0.88)
    logger.add_log(track_id=3, class_id=5, direction="Entry", frame_number=90, confidence=0.80)
    logger.add_log(track_id=4, class_id=7, direction="Exit", frame_number=120, confidence=0.70)

    excel_path = os.path.join(OUTPUT_DIR, "report_test.xlsx")
    csv_path = os.path.join(OUTPUT_DIR, "report_test.csv")

    out_xlsx = logger.export_to_excel(excel_path)
    out_csv = logger.export_to_csv(csv_path)

    assert os.path.isfile(out_xlsx), f"Excel file not created: {out_xlsx}"
    assert os.path.isfile(out_csv), f"CSV file not created: {out_csv}"

    print("Export produced:", out_xlsx, out_csv)


if __name__ == "__main__":
    test_export()
    print("Done")
