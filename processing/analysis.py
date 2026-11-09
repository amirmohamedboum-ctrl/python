"""
Module processing / analysis : statistiques demandées pour le dashboard.
Un événement "repeated N times" compte pour N tentatives (champ count).
"""
from collections import Counter

from utils.logger import get_logger

logger = get_logger("analysis")

EMPTY_USER = "<vide>"


def failed_by_country(events: list[dict], countries: dict) -> Counter:
    """Nombre de tentatives échouées par pays."""
    counter = Counter()
    for e in events:
        if e["status"] == "failed":
            country = countries.get(e["ip"])
            if country is None:
                logger.warning("IP sans pays dans le dictionnaire : %s", e["ip"])
                country = "Inconnu"
            counter[country] += e["count"]
    logger.info("Échecs par pays : %d pays, %d tentatives", len(counter), sum(counter.values()))
    return counter


def success_by_user(events: list[dict]) -> Counter:
    """Nombre de tentatives réussies par utilisateur."""
    counter = Counter()
    for e in events:
        if e["status"] == "success":
            counter[e["user"] or EMPTY_USER] += e["count"]
    logger.info("Succès par utilisateur : %d utilisateurs, %d connexions", len(counter), sum(counter.values()))
    if not counter:
        logger.warning("Aucune connexion réussie trouvée dans les logs")
    return counter


def failed_invalid_user(events: list[dict]) -> Counter:
    """Tentatives échouées avec un utilisateur invalide ('invalid user'), par nom d'utilisateur."""
    counter = Counter()
    for e in events:
        if e["status"] == "failed" and e["invalid_user"]:
            counter[e["user"] or EMPTY_USER] += e["count"]
    logger.info("Échecs 'invalid user' : %d noms, %d tentatives", len(counter), sum(counter.values()))
    return counter