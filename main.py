from pathlib import Path

from utils.logger import get_logger
from ingestion import read

DATA_DIR = Path(__file__).parent / "data"
logger = get_logger("main")


def main():
    logger.info("Démarrage du pipeline")
    rows = read.ingest(DATA_DIR)
    if not rows:
        logger.error("Aucune ligne lue : arrêt du pipeline")
        return
    print(f"{len(rows)} lignes lues")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Erreur inattendue dans le pipeline")