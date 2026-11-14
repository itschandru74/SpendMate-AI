import csv, os
from database import list_transactions

def export_transactions_csv(uid):
    os.makedirs("reports",exist_ok=True)
    path=os.path.abspath(f"reports/spendmate_transactions_{uid}.csv")
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f)
        writer.writerow(["ID","Date","Type","Category","Description","Amount"])
        for r in list_transactions(uid): writer.writerow([r[0],r[2],r[3],r[4],r[5],r[6]])
    return path
