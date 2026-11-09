
import psycopg2
from utils.logger import get_logger

logger = get_logger("database")

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5000",
    "dbname": "log_analysis",
    "user": "postgres",
    "password": "Amir",
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def save_events(events, countries):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO auth_events
            (month, day, log_time, event_type, method,
             username, ip, country, invalid_user, attempts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for event in events:
            ip = event["ip"]
            country = countries.get(ip)

            cursor.execute(query, (
                event["month"],
                event["day"],
                event["time"],
                event["status"],
                event["method"],
                event["user"],
                ip,
                country,
                event["invalid_user"],
                event["count"]
            ))

        conn.commit()

        logger.info(
            "%d événements enregistrés dans PostgreSQL",
            len(events)
        )

    except Exception:
        if conn:
            conn.rollback()
        logger.exception("Erreur d'enregistrement PostgreSQL")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
