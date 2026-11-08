from pathlib import Path

from utils.logger import get_logger
from ingestion import read
from processing import extract_transform

DATA_DIR = Path(__file__).parent / "data"
logger = get_logger("main")


def main():
    logger.info("Démarrage du pipeline")
    rows = read.ingest(DATA_DIR)
    if not rows:
        logger.error("Aucune ligne lue : arrêt du pipeline")
        return

    events = extract_transform.extract_all(rows)
    failed = [e for e in events if e["status"] == "failed"]
    success = [e for e in events if e["status"] == "success"]
    print(f"{len(rows)} lignes lues")
    print(f"{sum(e['count'] for e in failed)} tentatives échouées")
    print(f"{sum(e['count'] for e in success)} tentatives réussies")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Erreur inattendue dans le pipeline")