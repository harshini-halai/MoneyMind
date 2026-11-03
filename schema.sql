-- MoneyMind database schema (fresh install, includes Dream Goals).
-- Run this ONCE on a NEW, EMPTY database (for example the cloud one).
-- Do NOT run it on your local database: your local tables already exist.

CREATE TABLE users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE transactions (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL,
  description VARCHAR(255) NOT NULL,
  category    VARCHAR(50)  NOT NULL,
  amount      DECIMAL(12,2) NOT NULL,
  date        DATE NOT NULL,
  type        ENUM('income','expense') NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_transactions_user_date (user_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE goals (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT NOT NULL,
  name          VARCHAR(100) NOT NULL,
  target_amount DECIMAL(12,2) NOT NULL,
  target_date   DATE NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_goals_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Savings can optionally be put towards a goal.
-- If a goal is deleted, the money stays in savings.
CREATE TABLE savings (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL,
  amount      DECIMAL(12,2) NOT NULL,
  description VARCHAR(255) NOT NULL,
  date        DATE NOT NULL,
  goal_id     INT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL,
  INDEX idx_savings_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE emergency_fund (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL,
  amount      DECIMAL(12,2) NOT NULL,
  description VARCHAR(255) NOT NULL,
  date        DATE NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_emergency_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE upcoming_expenses (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL,
  amount      DECIMAL(12,2) NOT NULL,
  description VARCHAR(255) NOT NULL,
  due_date    DATE NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_upcoming_user_due (user_id, due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE budgets (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  category   VARCHAR(50) NOT NULL,
  amount     DECIMAL(12,2) NOT NULL,
  month      DATE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uq_budget_user_cat_month (user_id, category, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- What each user has taught the categorizer (see backend/categorizer.py).
CREATE TABLE category_memory (
  user_id         INT NOT NULL,
  merchant_key    VARCHAR(100) NOT NULL,
  category        VARCHAR(50)  NOT NULL,
  times_confirmed INT NOT NULL DEFAULT 1,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, merchant_key),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;