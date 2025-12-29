PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id           INTEGER PRIMARY KEY,
    lifetime_farmed   INTEGER NOT NULL DEFAULT 0,
    lifetime_tokens   INTEGER NOT NULL DEFAULT 0,
    tokens            INTEGER NOT NULL DEFAULT 0,
    last_farmed_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servers (
    server_id          INTEGER PRIMARY KEY,
    farm_channel_id    INTEGER NOT NULL,
    daily_goal         INTEGER DEFAULT 0,
    last_farmer_id     INTEGER DEFAULT NULL,
    lifetime_farmed    INTEGER NOT NULL DEFAULT 0,
    best_daily         INTEGER NOT NULL DEFAULT 0,
    best_weekly        INTEGER NOT NULL DEFAULT 0,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_server_stats (
    server_id        INTEGER NOT NULL,
    stat_date        DATE NOT NULL,
    daily_count      INTEGER NOT NULL DEFAULT 0,
    goal_reached     BOOLEAN NOT NULL DEFAULT FALSE,
    goal_snapshot    INTEGER NOT NULL,

    PRIMARY KEY (server_id, stat_date),
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);

CREATE TABLE IF NOT EXISTS daily_user_stats (
    server_id    INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    stat_date    DATE NOT NULL,
    farmed       INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (server_id, user_id, stat_date),
    FOREIGN KEY (server_id) REFERENCES servers(server_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_daily_user_date
    ON daily_user_stats (stat_date);

CREATE INDEX IF NOT EXISTS idx_daily_server_date
    ON daily_server_stats (stat_date);