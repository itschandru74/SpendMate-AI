# SpendMate AI — Free Desktop Starter

## Included
- Colourful dark interface (blue, purple, cyan, green, pink, orange)
- Login / Register
- Dashboard
- Income and expense entry
- Monthly category budgets
- Linear Regression next-month estimate
- Basic unusual-expense flagging
- Repeated-expense pattern view
- Savings goal creation
- CSV report export
- Simple finance tips
- Local SQLite database

## Free usage
This starter uses free Python libraries, a local SQLite database, and local ML processing. It does not require a paid API, subscription, cloud account, or internet connection after dependencies are installed. Python and the listed packages are free to use. Normal internet access is needed only to install packages initially.

## Windows setup
1. Install Python 3.10+.
2. Extract this ZIP and open the folder in VS Code.
3. In VS Code Terminal run:
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate
   pip install -r requirements.txt
   python main.py
   ```
4. Create a free account and log in.

## Notes
- Your data is stored locally in `spendmate.db`.
- This is a student-project starter, not a production financial service.
- The prediction is basic Linear Regression and needs multiple months of real entries. Prefer 6–12 months of history and evaluate with MAE/RMSE before presenting results.
- Anomaly detection currently uses a simple statistical threshold; validate flags rather than treating them as fraud.
- The assistant currently gives rule-based suggestions, not generative AI.
- For a stronger final-year version, next add interactive charts, month-wise Excel export, edit transaction, goal contribution, stronger ML comparisons, and tests.
