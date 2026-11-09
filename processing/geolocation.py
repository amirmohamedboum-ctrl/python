"""
Module processing / geolocation : pays d'origine d'une adresse IP via l'API ipinfo.io.

- Les résultats sont gardés dans un cache (cache/geo_cache.json) : une IP n'est
  interrogée qu'une seule fois, même après plusieurs exécutions.
- Si l'API est inaccessible ou si la limite de requêtes est atteinte, on arrête
  d'interroger et les IP restantes sont classées "Inconnu".
- Un token gratuit peut être fourni via la variable d'environnement IPINFO_TOKEN.
"""
import json
import os
from pathlib import Path

import requests as http

from utils.logger import get_logger

logger = get_logger("geolocation")

API_URL = "https://ipinfo.io/{ip}/json/?token=1c3733ad8e7859"
CACHE_FILE = Path(__file__).parent.parent / "cache" / "geo_cache.json"
TIMEOUT = 5                  # secondes
MAX_CONSECUTIVE_ERRORS = 5   # on arrête l'API après 5 erreurs de suite
SAVE_EVERY = 50              # sauvegarde du cache toutes les 50 nouvelles IP

UNKNOWN = "Inconnu"
PRIVATE = "Réseau privé"


class RateLimitError(Exception):
    """Limite de requêtes de l'API atteinte (HTTP 429)."""


def is_private(ip: str) -> bool:
    """True si l'IP est locale/privée (10.x, 127.x, 192.168.x, 172.16-31.x, 169.254.x)."""
    try:
        a, b = (int(x) for x in ip.split(".")[:2])
    except ValueError:
        return False
    return (a in (0, 10, 127)
            or (a == 192 and b == 168)
            or (a == 172 and 16 <= b <= 31)
            or (a == 169 and b == 254))


def load_cache() -> dict:
    try:
        with open(CACHE_FILE, mode="r", encoding="utf-8") as f:
            cache = json.load(f)
        logger.info("Cache chargé : %d IP", len(cache))
        return cache
    except FileNotFoundError:
        logger.info("Pas de cache existant, il sera créé")
    except json.JSONDecodeError as e:
        logger.error("Cache illisible (JSON invalide), il est ignoré : %s", e)
    except OSError as e:
        logger.error("Erreur de lecture du cache : %s", e)
    return {}


def save_cache(cache: dict) -> None:
    try:
        os.makedirs(CACHE_FILE.parent, exist_ok=True)
        with open(CACHE_FILE, mode="w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1)
    except OSError as e:
        logger.error("Impossible d'enregistrer le cache : %s", e)


def geolocation(ip: str):
    """
    Retourne le code pays (ex: 'FR') d'une IP, ou None si la requête a échoué.
    Lève RateLimitError si l'API refuse (429).
    """
    params = {}
    token = os.environ.get("IPINFO_TOKEN")
    if token:
        params["token"] = token

    try:
        response = http.get(API_URL.format(ip=ip), params=params, timeout=TIMEOUT)
    except http.exceptions.Timeout:
        logger.error("Timeout pour l'IP %s", ip)
        return None
    except http.exceptions.ConnectionError:
        logger.error("Connexion impossible à ipinfo.io (IP %s)", ip)
        return None
    except http.exceptions.RequestException as e:
        logger.error("Erreur de requête pour l'IP %s : %s", ip, e)
        return None

    if response.status_code == 429:
        raise RateLimitError("HTTP 429 : limite de requêtes ipinfo.io atteinte")
    if response.status_code != 200:
        logger.error("Réponse HTTP %s pour l'IP %s", response.status_code, ip)
        return None

    try:
        data = response.json()
    except ValueError:
        logger.error("Réponse non-JSON pour l'IP %s", ip)
        return None

    if data.get("bogon"):
        return PRIVATE
    country = data.get("country")
    if not country:
        logger.warning("Pas de pays dans la réponse pour l'IP %s : %s", ip, data)
        return None
    return country


def resolve_countries(ips) -> dict:
    """Retourne {ip: pays} pour un ensemble d'IP (cache -> API)."""
    cache = load_cache()
    result = {}
    new_lookups = 0
    errors_in_a_row = 0
    stopped = False
    ips = sorted(ips)

    try:
        for i, ip in enumerate(ips, start=1):
            if is_private(ip):
                result[ip] = PRIVATE
            elif ip in cache:
                result[ip] = cache[ip]
            elif stopped:
                result[ip] = UNKNOWN
            else:
                try:
                    country = geolocation(ip)
                except RateLimitError as e:
                    logger.error("%s : arrêt des requêtes, relancer plus tard (le cache est conservé)", e)
                    stopped = True
                    result[ip] = UNKNOWN
                    continue

                if country is None:
                    errors_in_a_row += 1
                    result[ip] = UNKNOWN
                    if errors_in_a_row >= MAX_CONSECUTIVE_ERRORS:
                        logger.error("%d erreurs consécutives : arrêt des requêtes à l'API", errors_in_a_row)
                        stopped = True
                    continue

                errors_in_a_row = 0
                cache[ip] = country
                result[ip] = country
                new_lookups += 1
                if new_lookups % SAVE_EVERY == 0:
                    save_cache(cache)
                    print(f"Géolocalisation : {i}/{len(ips)} IP parcourues")
    finally:
        save_cache(cache)   # sauvegarde même si on interrompt avec Ctrl+C

    unknown = sum(1 for c in result.values() if c == UNKNOWN)
    logger.info("%d IP traitées, %d nouvelles requêtes API, %d inconnues", len(result), new_lookups, unknown)
    if unknown:
        logger.warning("%d IP sans pays (API indisponible ou limite atteinte)", unknown)
    return result


if __name__ == '__main__':
    print(geolocation("88.147.152.239"))