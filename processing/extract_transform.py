"""
Module processing / extract_transform : extraction des événements d'authentification
à partir des lignes brutes d'auth.log grâce aux expressions régulières (re).

Lignes reconnues :
  Failed password for root from 1.2.3.4 port 5555 ssh2
  Failed password for invalid user test from 1.2.3.4 port 5555 ssh2
  Failed none for invalid user  from 1.2.3.4 port 5555 ssh2
  message repeated 4 times: [ Failed password for root from 1.2.3.4 port 5555 ssh2]
  Accepted password for adminesisa from 10.10.33.81 port 59176 ssh2

Chaque événement est un dictionnaire :
  month, day, time, status ("failed" / "success"), method, user, ip, port,
  invalid_user (bool), count (nombre de tentatives représentées par la ligne)
"""
import re

from utils.logger import get_logger

logger = get_logger("extract_transform")

EVENT_PATTERN = re.compile(
    r'^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s(?P<time>\d{2}:\d{2}:\d{2})\s\S+\ssshd\[\d+\]:\s'
    r'(?:message repeated (?P<repeat>\d+) times: \[\s)?'
    r'(?P<result>Failed|Accepted)\s(?P<method>\S+)\sfor\s'
    r'(?P<invalid>invalid user\s)?(?P<user>\S*)\s+from\s'
    r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\sport\s(?P<port>\d+)'
)

# Détection large : une ligne qui "ressemble" à un événement d'authentification.
# Si elle ne passe pas EVENT_PATTERN, on la signale dans les logs (format inattendu).
CANDIDATE_PATTERN = re.compile(r'sshd\[\d+\]:\s.*(?:Failed|Accepted)\s\S+\sfor\s')


def extract(row: str):
    """Transforme une ligne en événement (dict). Retourne None si la ligne n'est pas un événement."""
    try:
        match = re.search(EVENT_PATTERN, row)
    except TypeError:
        logger.error("Ligne invalide (type %s au lieu de str) : %r", type(row).__name__, row)
        return None

    if not match:
        if re.search(CANDIDATE_PATTERN, row):
            logger.warning("Ligne d'authentification non reconnue : %s", row.strip())
        return None

    data = match.groupdict()
    try:
        port = int(data["port"])
        # "message repeated N times" = N tentatives supplémentaires déjà comptées par sshd
        count = int(data["repeat"]) if data["repeat"] else 1
    except ValueError:
        logger.error("Port ou compteur illisible : %s", row.strip())
        return None

    return {
        "month": data["month"],
        "day": int(data["day"]),
        "time": data["time"],
        "status": "failed" if data["result"] == "Failed" else "success",
        "method": data["method"],
        "user": data["user"],
        "ip": data["ip"],
        "port": port,
        "invalid_user": data["invalid"] is not None,
        "count": count,
    }


def extract_all(rows: list[str]) -> list[dict]:
    """Applique extract() à toutes les lignes et retourne la liste des événements."""
    events = []
    for row in rows:
        event = extract(row)
        if event:
            events.append(event)

    failed = sum(e["count"] for e in events if e["status"] == "failed")
    success = sum(e["count"] for e in events if e["status"] == "success")
    logger.info("%d lignes analysées -> %d événements (%d échecs, %d succès)",
                len(rows), len(events), failed, success)
    if not events:
        logger.warning("Aucun événement d'authentification trouvé")
    return events


def filter_failed(rows: list[str]) -> list[str]:
    return [row for row in rows if "Failed" in row or "Invalid" in row]