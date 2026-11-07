from pathlib import Path
from ingestion import read
from processing import extract_transform

DATA_DIR = Path(__file__).parent / "data"

if __name__ == "__main__":
    rows = read.ingest(str(DATA_DIR))
    failed = extract_transform.filter_failed(rows)
    print(f"{len(failed)} lignes Failed/Invalid sur {len(rows)} lignes")
    for row in failed[:3]:
        print(row.strip())