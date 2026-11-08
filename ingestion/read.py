"""
Module ingestion : lecture des fichiers auth.log (texte ou .gz).

in  : dossier data
out : liste de lignes (str)
"""
import gzip
import os
import os.path as pt

from utils.logger import get_logger

logger = get_logger("ingestion")

LOG_PREFIX = "auth.log"


def read_file(file_path: str) -> list[str]:
    """Lit un fichier (texte ou .gz) et retourne ses lignes. Retourne [] en cas d'erreur."""
    try:
        if file_path.endswith(".gz"):
            opener = gzip.open(file_path, mode="rt", encoding="utf-8", errors="replace")
        else:
            opener = open(file_path, mode="r", encoding="utf-8", errors="replace")
        with opener as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        logger.error("Fichier introuvable : %s", file_path)
        return []
    except PermissionError:
        logger.error("Permission refusée : %s", file_path)
        return []
    except gzip.BadGzipFile:
        logger.error("Fichier .gz invalide ou corrompu : %s", file_path)
        return []
    except EOFError:
        logger.error("Fichier .gz tronqué (fin de fichier inattendue) : %s", file_path)
        return []
    except OSError as e:
        logger.error("Erreur d'entrée/sortie sur %s : %s", file_path, e)
        return []

    logger.info("%s : %d lignes lues", pt.basename(file_path), len(lines))
    return lines


def ingest(path) -> list[str]:
    """Lit tous les fichiers auth.log* du dossier et retourne toutes les lignes."""
    path = str(path)
    if not pt.isdir(path):
        logger.error("Le dossier de données n'existe pas : %s", path)
        return []

    try:
        files = sorted(f for f in os.listdir(path) if f.startswith(LOG_PREFIX))
    except OSError as e:
        logger.error("Impossible de lister le dossier %s : %s", path, e)
        return []

    if not files:
        logger.warning("Aucun fichier '%s*' trouvé dans %s", LOG_PREFIX, path)
        return []

    rows: list[str] = []
    for file in files:
        file_path = pt.join(path, file)
        if not pt.isfile(file_path):
            logger.warning("Ignoré (n'est pas un fichier) : %s", file_path)
            continue
        rows.extend(read_file(file_path))

    logger.info("Ingestion terminée : %d lignes au total (%d fichiers)", len(rows), len(files))
    return rows


if __name__ == "__main__":
    data = ingest("./data")
    if data:
        print(data[:10])