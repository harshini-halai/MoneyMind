# MoneyMind

MoneyMind is an AI-powered personal finance platform, with Khata as its intelligent financial assistant.

## Setup

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
   pip install -r requirements.txt
   ```

2. Create the database: run `schema.sql` in MySQL (review it first - see the note at the top of the file).

3. Copy `.env.example` to `.env` and fill it in. Generate the JWT secret with:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. Start the app **from the project root** (the folder that contains `backend/` and `frontend/`):

   ```bash
   uvicorn backend.main:app --reload
   ```

5. Open <http://127.0.0.1:8000>, create an account, and log in.

Interactive API docs are at <http://127.0.0.1:8000/docs>.

## Features & Roadmap

### Core Finance

- [x] User Account & Authentication
- [x] Income Management
- [x] Expense Management
- [x] Transaction Management
- [x] Financial Dashboard
- [x] Spending Analysis
- [x] Savings Management
- [ ] Dream Goals
- [x] Safe-to-Spend
- [x] Budget Management
- [ ] Recurring Expenses
- [ ] Subscription Tracker

### Khata — AI & ML Intelligence

- [x] Smart Expense Categorization
- [x] User Feedback & Learning
- [ ] Merchant Recognition
- [ ] Confidence-Based Categorization
- [ ] Smart Spending Insights
- [ ] Spending Anomaly Detection
- [ ] Future Spending Prediction
- [ ] Smart Alerts & Notifications
- [ ] Personalized Recommendations
- [ ] Proactive Khata Insights

### Financial Decision Making

- [ ] What-If Simulator
- [ ] Goal Impact & Consequence Engine
- [ ] Alternative Purchase Analyzer
- [ ] AI Budget Builder
- [ ] Savings Score

### Financial Intelligence

- [ ] Teach Me / Financial Education
- [ ] Insurance Intelligence
- [ ] IPO Intelligence

### Data, Reports & Analysis

- [ ] Bank Statement Import & Analysis
- [ ] Financial Reports
- [ ] Long-Term Financial Trends
- [ ] Indian & UPI Transaction Support

### Platform & Security

- [ ] Privacy & Data Security
- [ ] PWA / App-like Web Experience
- [ ] Push Notifications

### Future Integrations

- [ ] Direct Bank Integration
- [ ] Payment App Integration
- [ ] Automatic Transaction Sync

To run it:

pip install -r requirements.txt
Put a new JWT_SECRET_KEY (32+ characters) in .env.
From the project root, run uvicorn backend.main:app --reload.
Open <http://127.0.0.1:8000>, register, and log in.

If something errors, paste the message here and I’ll fix it.
