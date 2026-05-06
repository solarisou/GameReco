import pandas as pd
from sqlalchemy import create_engine
from utils import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, logger


def get_connection():
    url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def load_ratings() -> pd.DataFrame:
    engine = get_connection()
    with engine.connect() as conn:
        df = pd.read_sql("SELECT user_id, item_id, score FROM ratings", conn)
    logger.info(f"Ratings chargés : {len(df)} lignes")
    return df


def load_items() -> pd.DataFrame:
    engine = get_connection()
    with engine.connect() as conn:
        items_df  = pd.read_sql("SELECT id, title, type, synopsis, avg_rating FROM items", conn)
        genres_df = pd.read_sql(
            "SELECT ig.item_id, g.name AS genre FROM item_genre ig JOIN genres g ON ig.genre_id = g.id",
            conn
        )

    genres_grouped = genres_df.groupby("item_id")["genre"].apply(
        lambda x: " ".join(x)
    ).reset_index()
    genres_grouped.columns = ["id", "genres"]

    items_df = items_df.merge(genres_grouped, on="id", how="left")
    items_df["genres"]  = items_df["genres"].fillna("")
    items_df["content"] = (items_df["title"] + " " +
                           items_df["type"] + " " +
                           items_df["genres"] + " " +
                           items_df["synopsis"].fillna(""))

    logger.info(f"Items chargés : {len(items_df)} lignes")
    return items_df


def load_history(user_id: str) -> list:
    engine = get_connection()
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT item_id FROM history WHERE user_id = %(uid)s",
            conn, params={"uid": user_id}
        )
    return df["item_id"].tolist()