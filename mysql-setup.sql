CREATE DATABASE IF NOT EXISTS secure_auth_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'secure_user'@'localhost'
  IDENTIFIED BY 'CHANGE_ME_STRONG_PASSWORD';

GRANT ALL PRIVILEGES ON secure_auth_db.* TO 'secure_user'@'localhost';

FLUSH PRIVILEGES;
