from pathlib import Path

from utils.logger import get_logger
from ingestion import read
from processing import extract_transform, geolocation, analysis
from dashboard import dashboard

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = BASE_DIR / "output" / "dashboard.png"
logger = get_logger("main")


def main():
    logger.info("Démarrage du pipeline")

    # 1. Ingestion
    rows = read.ingest(DATA_DIR)
    if not rows:
        logger.error("Aucune ligne lue : arrêt du pipeline")
        return

    # 2. Extraction / transformation
    events = extract_transform.extract_all(rows)
    if not events:
        logger.error("Aucun événement extrait : arrêt du pipeline")
        return

    # 3. Géolocalisation des IP à l'origine des échecs
    failed_ips = {e["ip"] for e in events if e["status"] == "failed"}
    countries = geolocation.resolve_countries(failed_ips)

    # 4. Statistiques
    by_country = analysis.failed_by_country(events, countries)
    by_user = analysis.success_by_user(events)
    invalid_users = analysis.failed_invalid_user(events)

    # 5. Dashboard
    dashboard.build_dashboard(by_country, by_user, invalid_users, str(OUTPUT_FILE))
    logger.info("Pipeline terminé")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Erreur inattendue dans le pipeline")