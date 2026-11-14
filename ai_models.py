from collections import defaultdict
from database import list_transactions

def monthly_expenses(uid):
    totals=defaultdict(float)
    for r in list_transactions(uid):
        if r[3]=="expense": totals[r[2][:7]] += r[6]
    return sorted(totals.items())

def predict_next_month(uid):
    data=monthly_expenses(uid)
    if len(data)<2:
        return "Add expenses in at least 2 different months to get a first estimate. 6–12 months of data is better for a meaningful model."
    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression
        X=np.arange(len(data)).reshape(-1,1)
        y=np.array([v for _,v in data])
        model=LinearRegression().fit(X,y)
        prediction=max(0,float(model.predict([[len(data)]])[0]))
        return f"Estimated next-month expense: ₹{prediction:,.2f}\\nModel: Linear Regression\\nMonths used: {len(data)}\\nThis is an estimate, not a guarantee."
    except ImportError:
        average=sum(v for _,v in data)/len(data)
        return f"Estimated next-month expense: ₹{average:,.2f}\\nInstall scikit-learn to use Linear Regression."

def detect_anomalies(uid):
    rows=[r for r in list_transactions(uid) if r[3]=="expense"]
    if len(rows)<5: return []
    values=[r[6] for r in rows]
    avg=sum(values)/len(values)
    sd=(sum((x-avg)**2 for x in values)/len(values))**0.5
    return [r for r in rows if sd and r[6]>avg+2*sd]
