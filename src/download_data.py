"""Download the public Olist Kaggle dataset and keep the three tables used here."""

from __future__ import annotations

from pathlib import Path
from shutil import copyfileobj
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
TABLES = {
    "olist_orders_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_order_reviews_dataset.csv",
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    archive_path = RAW / "olist_dataset.zip"

    print("Downloading the Kaggle dataset...")
    with urlopen(URL, timeout=90) as response, archive_path.open("wb") as archive_file:
        copyfileobj(response, archive_file)

    with ZipFile(archive_path) as archive:
        found = set()
        for member in archive.namelist():
            name = Path(member).name
            if name not in TABLES:
                continue
            target = RAW / name
            with archive.open(member) as source, target.open("wb") as output:
                copyfileobj(source, output)
            found.add(name)

    missing = TABLES - found
    archive_path.unlink(missing_ok=True)
    if missing:
        raise FileNotFoundError(f"The Kaggle archive is missing: {', '.join(sorted(missing))}")
    print(f"Saved {len(TABLES)} CSV tables in {RAW}")


if __name__ == "__main__":
    main()
