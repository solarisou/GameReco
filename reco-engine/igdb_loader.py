import time
import requests
import mysql.connector
from utils import (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
                   IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, logger)

# ── Config ───────────────────────────────────────────────────
IGDB_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_API_URL   = "https://api.igdb.com/v4"
RATE_LIMIT_S   = 0.25   # 4 requêtes/seconde max (limite IGDB)
BATCH_SIZE     = 500    # max par requête IGDB
MAX_GAMES      = 5000   # nombre total de jeux à charger


# ── Authentification Twitch → token IGDB ─────────────────────
def get_access_token():
    resp = requests.post(IGDB_TOKEN_URL, params={
        "client_id":     IGDB_CLIENT_ID,
        "client_secret": IGDB_CLIENT_SECRET,
        "grant_type":    "client_credentials"
    })
    resp.raise_for_status()
    token = resp.json()["access_token"]
    logger.info("Token IGDB obtenu")
    return token


# ── Headers IGDB ─────────────────────────────────────────────
def get_headers(token):
    return {
        "Client-ID":     IGDB_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }


# ── Connexion MySQL ──────────────────────────────────────────
def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ── Genres existants ─────────────────────────────────────────
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


# ── Insertion d'un jeu ───────────────────────────────────────
def insert_game(cursor, game, genre_map):
    igdb_id   = str(game.get("id", ""))
    title     = game.get("name", "")[:255]
    synopsis  = game.get("summary", "") or ""
    cover_url = ""

    # URL de couverture
    cover = game.get("cover")
    if cover and cover.get("url"):
        url = cover["url"]
        # IGDB retourne des URLs en //images... → on force https
        if url.startswith("//"):
            url = "https:" + url
        # Remplace la taille thumb par cover_big
        cover_url = url.replace("t_thumb", "t_cover_big")[:512]

    # Note : IGDB donne une note sur 100 → on ramène sur 10
    raw_rating = game.get("total_rating") or game.get("rating") or 0.0
    avg_rating = round(float(raw_rating) / 10, 2)

    # Vérifie si déjà en BDD
    cursor.execute("SELECT id FROM items WHERE source_id = %s", (igdb_id,))
    existing = cursor.fetchone()
    if existing:
        return existing[0]

    cursor.execute("""
        INSERT INTO items (title, type, synopsis, cover_url, avg_rating, source_id)
        VALUES (%s, 'game', %s, %s, %s, %s)
    """, (title, synopsis, cover_url, avg_rating, igdb_id))

    cursor.execute("SELECT id FROM items WHERE source_id = %s", (igdb_id,))
    item_id = cursor.fetchone()[0]

    # Genres
    genres = game.get("genres", [])
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


# ── Fetch une page de jeux IGDB ──────────────────────────────
def fetch_games(token, offset: int):
    headers = get_headers(token)
    # Requête Apicalypse : jeux avec note, triés par popularité
    body = f"""
        fields name, summary, total_rating, rating,
                cover.url, genres.name, first_release_date;
        where total_rating != null
            & total_rating_count > 20
            & version_parent = null;
        sort total_rating_count desc;
        limit {BATCH_SIZE};
        offset {offset};
    """
    for attempt in range(3):
        try:
            resp = requests.post(
                f"{IGDB_API_URL}/games",
                headers=headers,
                data=body,
                timeout=15
            )
            if resp.status_code == 429:
                logger.warning("Rate limit IGDB — attente 2s")
                time.sleep(2)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Erreur offset {offset} tentative {attempt+1} : {e}")
            time.sleep(1)
    return []


# ── Script principal ─────────────────────────────────────────
def main():
    logger.info("Démarrage ingestion IGDB...")

    # Obtenir le token
    token = get_access_token()

    conn      = get_conn()
    cursor    = conn.cursor()
    genre_map = get_genre_map(cursor)

    total_inserted = 0
    offset         = 0

    while total_inserted < MAX_GAMES:
        logger.info(f"Récupération offset {offset} — {total_inserted}/{MAX_GAMES} jeux insérés")
        games = fetch_games(token, offset)

        if not games:
            logger.warning(f"Aucun jeu retourné à l'offset {offset} — arrêt")
            break

        for game in games:
            try:
                insert_game(cursor, game, genre_map)
                total_inserted += 1
            except Exception as e:
                logger.error(f"Erreur insertion jeu {game.get('id')}: {e}")
                conn.rollback()
                continue

        conn.commit()
        logger.info(f"Offset {offset} — {total_inserted} jeux insérés au total")

        offset += BATCH_SIZE
        time.sleep(RATE_LIMIT_S)

    cursor.close()
    conn.close()
    logger.info(f"Terminé — {total_inserted} jeux insérés en BDD")


if __name__ == "__main__":
    main()