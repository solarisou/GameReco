import time
import requests
import mysql.connector
from utils import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, logger

# ── Config ───────────────────────────────────────────────────
JIKAN_BASE   = "https://api.jikan.moe/v4"
RATE_LIMIT_S = 0.5   # 2 requêtes/seconde max (limite Jikan)
MAX_PAGES    = 20    # 25 mangas par page → 500 mangas max


# ── Connexion MySQL ──────────────────────────────────────────
def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ── Récupération des genres existants ────────────────────────
def get_genre_map(cursor):
    cursor.execute("SELECT name, id FROM genres")
    return {row[0]: row[1] for row in cursor.fetchall()}


def insert_genre_if_missing(cursor, genre_name, genre_map):
    if genre_name not in genre_map:
        cursor.execute(
            "INSERT IGNORE INTO genres (name) VALUES (%s)", (genre_name,)
        )
        cursor.execute("SELECT id FROM genres WHERE name = %s", (genre_name,))
        row = cursor.fetchone()
        if row:
            genre_map[genre_name] = row[0]
            logger.info(f"Nouveau genre ajouté : {genre_name}")
    return genre_map.get(genre_name)


# ── Insertion d'un manga ─────────────────────────────────────
def insert_manga(cursor, manga, genre_map):
    mal_id    = str(manga.get("mal_id", ""))
    title     = manga.get("title", "")[:255]
    synopsis  = manga.get("synopsis") or ""
    cover_url = ""
    images    = manga.get("images", {})
    if images.get("jpg", {}).get("image_url"):
        cover_url = images["jpg"]["image_url"][:512]
    avg_rating = float(manga.get("score") or 0.0)

    # Vérifie si déjà en BDD via source_id
    cursor.execute("SELECT id FROM items WHERE source_id = %s", (mal_id,))
    existing = cursor.fetchone()
    if existing:
        return existing[0]

    cursor.execute("""
        INSERT INTO items (title, type, synopsis, cover_url, avg_rating, source_id)
        VALUES (%s, 'manga', %s, %s, %s, %s)
    """, (title, synopsis, cover_url, avg_rating, mal_id))

    cursor.execute("SELECT id FROM items WHERE source_id = %s", (mal_id,))
    item_id = cursor.fetchone()[0]

    # Genres
    genres = manga.get("genres", []) + manga.get("themes", [])
    for g in genres:
        genre_name = g.get("name", "")
        if not genre_name:
            continue
        genre_id = insert_genre_if_missing(cursor, genre_name, genre_map)
        if genre_id:
            cursor.execute("""
                INSERT IGNORE INTO item_genre (item_id, genre_id)
                VALUES (%s, %s)
            """, (item_id, genre_id))

    return item_id


# ── Fetch une page de mangas ─────────────────────────────────
def fetch_manga_page(page: int):
    url = f"{JIKAN_BASE}/manga"
    params = {
        "page":    page,
        "limit":   25,
        "order_by": "score",
        "sort":    "desc",
        "sfw":     "true"
    }
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 429:
                logger.warning("Rate limit Jikan — attente 2s")
                time.sleep(2)
                continue
            resp.raise_for_status()
            return resp.json().get("data", [])
        except requests.RequestException as e:
            logger.error(f"Erreur page {page} tentative {attempt+1} : {e}")
            time.sleep(1)
    return []


# ── Script principal ─────────────────────────────────────────
def main():
    conn   = get_conn()
    cursor = conn.cursor()
    genre_map = get_genre_map(cursor)

    total_inserted = 0

    for page in range(1, MAX_PAGES + 1):
        logger.info(f"Récupération page {page}/{MAX_PAGES}...")
        mangas = fetch_manga_page(page)

        if not mangas:
            logger.warning(f"Page {page} vide ou erreur — arrêt")
            break

        for manga in mangas:
            try:
                insert_manga(cursor, manga, genre_map)
                total_inserted += 1
            except Exception as e:
                logger.error(f"Erreur insertion manga {manga.get('mal_id')}: {e}")
                conn.rollback()
                continue

        conn.commit()
        logger.info(f"Page {page} — {total_inserted} mangas insérés au total")
        time.sleep(RATE_LIMIT_S)

    cursor.close()
    conn.close()
    logger.info(f"Terminé — {total_inserted} mangas insérés en BDD")


if __name__ == "__main__":
    main()
