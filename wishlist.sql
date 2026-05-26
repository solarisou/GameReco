CREATE TABLE IF NOT EXISTS wishlist (
    id         CHAR(36)  NOT NULL DEFAULT (UUID()),
    user_id    CHAR(36)  NOT NULL,
    item_id    CHAR(36)  NOT NULL,
    added_at   DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_wishlist PRIMARY KEY (id),
    CONSTRAINT uq_wishlist_user_item UNIQUE (user_id, item_id),
    CONSTRAINT fk_wl_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_wl_item FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    INDEX idx_wishlist_user (user_id)
) ENGINE=InnoDB;