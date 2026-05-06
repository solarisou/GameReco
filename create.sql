
--  TER M1 : Système de recommandation mangas & jeux vidéo



CREATE DATABASE IF NOT EXISTS ter_reco
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ter_reco;


-- 1. Table  users

CREATE TABLE IF NOT EXISTS users (
    id           CHAR(36)        NOT NULL DEFAULT (UUID()),
    username     VARCHAR(50)     NOT NULL UNIQUE,
    email        VARCHAR(100)    NOT NULL UNIQUE,
    password_hash VARCHAR(255)   NOT NULL,
    created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_users PRIMARY KEY (id)
) ENGINE=InnoDB;


-- 2. Table genres

CREATE TABLE IF NOT EXISTS genres (
    id   INT          NOT NULL AUTO_INCREMENT,
    name VARCHAR(50)  NOT NULL UNIQUE,
    CONSTRAINT pk_genres PRIMARY KEY (id)
) ENGINE=InnoDB;


-- 3. Table items  (mangas ET jeux vidéo dans la même table)
--    type IN ('manga', 'game')

CREATE TABLE IF NOT EXISTS items (
    id          CHAR(36)        NOT NULL DEFAULT (UUID()),
    title       VARCHAR(255)    NOT NULL,
    type        ENUM('manga','game') NOT NULL,
    synopsis    TEXT,
    cover_url   VARCHAR(512),
    avg_rating  FLOAT           DEFAULT 0.0,
    source_id   VARCHAR(100),               -- ID externe (MAL, IGDB, Steam)
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_items PRIMARY KEY (id),
    INDEX idx_items_type (type),
    INDEX idx_items_source (source_id)
) ENGINE=InnoDB;


-- 4. Table item_genre  

CREATE TABLE IF NOT EXISTS item_genre (
    item_id  CHAR(36) NOT NULL,
    genre_id INT      NOT NULL,
    CONSTRAINT pk_item_genre PRIMARY KEY (item_id, genre_id),
    CONSTRAINT fk_ig_item  FOREIGN KEY (item_id)  REFERENCES items(id)  ON DELETE CASCADE,
    CONSTRAINT fk_ig_genre FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- 5. Table ratings

CREATE TABLE IF NOT EXISTS ratings (
    id        CHAR(36)   NOT NULL DEFAULT (UUID()),
    user_id   CHAR(36)   NOT NULL,
    item_id   CHAR(36)   NOT NULL,
    score     FLOAT      NOT NULL CHECK (score >= 0 AND score <= 10),
    rated_at  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ratings PRIMARY KEY (id),
    CONSTRAINT uq_rating_user_item UNIQUE (user_id, item_id),
    CONSTRAINT fk_rat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rat_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    INDEX idx_ratings_user (user_id),
    INDEX idx_ratings_item (item_id)
) ENGINE=InnoDB;


-- 6. Table history

CREATE TABLE IF NOT EXISTS history (
    id         CHAR(36)  NOT NULL DEFAULT (UUID()),
    user_id    CHAR(36)  NOT NULL,
    item_id    CHAR(36)  NOT NULL,
    viewed_at  DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_history PRIMARY KEY (id),
    CONSTRAINT fk_hist_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_hist_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    INDEX idx_history_user (user_id)
) ENGINE=InnoDB;


-- Table 7. recommendations

CREATE TABLE IF NOT EXISTS recommendations (
    id           CHAR(36)     NOT NULL DEFAULT (UUID()),
    user_id      CHAR(36)     NOT NULL,
    item_id      CHAR(36)     NOT NULL,
    score        FLOAT        NOT NULL,
    method       ENUM('collaborative','content','hybrid') NOT NULL DEFAULT 'hybrid',
    generated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_recommendations PRIMARY KEY (id),
    CONSTRAINT fk_rec_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rec_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    INDEX idx_rec_user (user_id),
    INDEX idx_rec_score (score DESC)
) ENGINE=InnoDB;


-- Premiere données de tests 

INSERT IGNORE INTO genres (name) VALUES
  ('Action'), ('Adventure'), ('Comedy'), ('Drama'), ('Fantasy'),
  ('Horror'), ('Mystery'), ('Romance'), ('Sci-Fi'), ('Slice of Life'),
  ('Sports'), ('Thriller'), ('RPG'), ('FPS'), ('Strategy'),
  ('Simulation'), ('Fighting'), ('Platformer'), ('Puzzle'), ('Sandbox');
