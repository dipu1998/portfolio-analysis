from fastapi import FastAPI, HTTPException
from datetime import date, datetime
import random, math

app = FastAPI(title="WealthTech Portfolio Service", version="1.0.0")

FUND_NAV_DB = {
    "HDFC Top 100 Fund":       892.45,
    "SBI Bluechip Fund":        78.32,
    "Mirae Asset Emerging":    105.67,
    "ICICI Pru Liquid Fund":   345.12,
    "Axis Long Duration Bond":  22.45,
    "Nippon India Gold Fund":   28.90,
    "Parag Parikh Flexi Cap":   68.15,
    "Nifty 50 Index Fund":     245.80,
}

CLIENTS_DB = {
    "CLT001": {"client_id":"CLT001","name":"Ramesh Sharma","email":"ramesh@email.com","phone":"+91-9876543210","city":"Mumbai","risk_profile":"Moderate","aum":5130000.0,"onboarded_date":"2020-03-15"},
    "CLT002": {"client_id":"CLT002","name":"Priya Patel","email":"priya@email.com","phone":"+91-9876543211","city":"Ahmedabad","risk_profile":"Aggressive","aum":12500000.0,"onboarded_date":"2019-07-01"},
    "CLT003": {"client_id":"CLT003","name":"Suresh Mehta","email":"suresh@email.com","phone":"+91-9876543212","city":"Pune","risk_profile":"Conservative","aum":2800000.0,"onboarded_date":"2021-11-20"},
}

HOLDINGS_DB = {
    "CLT001": [
        {"fund":"HDFC Top 100 Fund","units":2000,"buy_price":750.0,"type":"Equity"},
        {"fund":"Parag Parikh Flexi Cap","units":5000,"buy_price":55.0,"type":"Equity"},
        {"fund":"ICICI Pru Liquid Fund","units":1000,"buy_price":320.0,"type":"Debt"},
        {"fund":"Nippon India Gold Fund","units":3000,"buy_price":25.0,"type":"Gold"},
    ],
    "CLT002": [
        {"fund":"Mirae Asset Emerging","units":15000,"buy_price":85.0,"type":"Equity"},
        {"fund":"Nifty 50 Index Fund","units":8000,"buy_price":210.0,"type":"Equity"},
        {"fund":"Axis Long Duration Bond","units":20000,"buy_price":20.0,"type":"Debt"},
    ],
    "CLT003": [
        {"fund":"SBI Bluechip Fund","units":5000,"buy_price":72.0,"type":"Equity"},
        {"fund":"ICICI Pru Liquid Fund","units":3000,"buy_price":310.0,"type":"Debt"},
    ],
}

SIP_ORDERS_DB = []

def calculate_xirr(invested, current_value, years):
    if invested <= 0 or years <= 0:
        return 0.0
    return round((math.pow(current_value / invested, 1.0 / years) - 1) * 100, 2)

def calculate_risk_score(raw_holdings):
    risk_weights = {"Equity": 8, "Hybrid": 5, "Gold": 4, "Debt": 2}
    total_value = 0
    weighted_risk = 0
    for h in raw_holdings:
        nav = FUND_NAV_DB.get(h["fund"], h["buy_price"])
        value = h["units"] * nav
        risk = risk_weights.get(h["type"], 5)
        weighted_risk += value * risk
        total_value += value
    if total_value == 0:
        return 5.0
    return round(weighted_risk / total_value, 1)

def build_holdings(client_id):
    result = []
    for h in HOLDINGS_DB.get(client_id, []):
        current_nav = FUND_NAV_DB.get(h["fund"], h["buy_price"])
        current_value = h["units"] * current_nav
        invested = h["units"] * h["buy_price"]
        gain_loss = current_value - invested
        gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0
        result.append({
            "fund_name": h["fund"],
            "fund_type": h["type"],
            "units": h["units"],
            "buy_price": h["buy_price"],
            "current_nav": round(current_nav, 2),
            "current_value": round(current_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_pct": round(gain_loss_pct, 2),
        })
    return result

@app.get("/")
def root():
    return {"service":"WealthTech Portfolio Service","version":"1.0.0","status":"running","total_clients":len(CLIENTS_DB),"docs_url":"/docs"}

@app.get("/health")
def health_check():
    return {"status":"healthy","timestamp":datetime.now().isoformat()}

@app.get("/clients")
def get_all_clients():
    return {"clients":list(CLIENTS_DB.values()),"total":len(CLIENTS_DB)}

@app.get("/clients/{client_id}")
def get_client(client_id: str):
    client = CLIENTS_DB.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    return client

@app.get("/clients/{client_id}/portfolio")
def get_portfolio(client_id: str):
    client = CLIENTS_DB.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    holdings = build_holdings(client_id)
    total_invested = sum(h["units"] * h["buy_price"] for h in HOLDINGS_DB.get(client_id, []))
    current_value = sum(h["current_value"] for h in holdings)
    gain_loss = current_value - total_invested
    gain_loss_pct = (gain_loss / total_invested * 100) if total_invested > 0 else 0
    onboarded = date.fromisoformat(client["onboarded_date"])
    years = (date.today() - onboarded).days / 365.0
    return {
        "client_id": client_id,
        "client_name": client["name"],
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "total_gain_loss": round(gain_loss, 2),
        "gain_loss_pct": round(gain_loss_pct, 2),
        "xirr_pct": calculate_xirr(total_invested, current_value, years),
        "risk_score": calculate_risk_score(HOLDINGS_DB.get(client_id, [])),
        "holdings": holdings,
        "last_updated": datetime.now().isoformat(),
    }

@app.get("/clients/{client_id}/holdings")
def get_holdings(client_id: str):
    if client_id not in CLIENTS_DB:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    return {"client_id": client_id, "holdings": build_holdings(client_id)}

@app.get("/nav")
def get_all_navs():
    return {"nav_date": date.today().isoformat(), "funds": [{"fund_name": k, "nav": v} for k, v in FUND_NAV_DB.items()]}

@app.put("/nav/update")
def update_nav(body: dict):
    fund_name = body.get("fund_name")
    new_nav = body.get("new_nav")
    if not fund_name or not new_nav:
        raise HTTPException(status_code=400, detail="fund_name and new_nav required")
    if fund_name not in FUND_NAV_DB:
        raise HTTPException(status_code=404, detail=f"Fund '{fund_name}' not found")
    old_nav = FUND_NAV_DB[fund_name]
    FUND_NAV_DB[fund_name] = new_nav
    return {"message":"NAV updated","fund":fund_name,"old_nav":old_nav,"new_nav":new_nav,"change_pct":round((new_nav-old_nav)/old_nav*100,2),"updated_at":datetime.now().isoformat()}

@app.post("/clients/{client_id}/sip", status_code=201)
def create_sip(client_id: str, body: dict):
    if client_id not in CLIENTS_DB:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    fund_name = body.get("fund_name")
    monthly_amount = body.get("monthly_amount", 0)
    if fund_name not in FUND_NAV_DB:
        raise HTTPException(status_code=400, detail=f"Fund '{fund_name}' not found")
    if monthly_amount < 500:
        raise HTTPException(status_code=400, detail="Minimum SIP is Rs500/month")
    order = {"sip_id":f"SIP{len(SIP_ORDERS_DB)+1:04d}","client_id":client_id,"fund_name":fund_name,"monthly_amount":monthly_amount,"start_date":body.get("start_date"),"status":"ACTIVE","created_at":datetime.now().isoformat()}
    SIP_ORDERS_DB.append(order)
    return {"message":"SIP created","sip":order}

@app.get("/clients/{client_id}/sip")
def get_sip_orders(client_id: str):
    if client_id not in CLIENTS_DB:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    return {"client_id":client_id,"sip_orders":[s for s in SIP_ORDERS_DB if s["client_id"]==client_id]}

@app.get("/dashboard/summary")
def get_dashboard_summary():
    total_aum = sum(c["aum"] for c in CLIENTS_DB.values())
    risk_dist = {}
    city_dist = {}
    for c in CLIENTS_DB.values():
        risk_dist[c["risk_profile"]] = risk_dist.get(c["risk_profile"], 0) + 1
        city_dist[c["city"]] = city_dist.get(c["city"], 0) + 1
    return {"total_clients":len(CLIENTS_DB),"total_aum_crore":round(total_aum/10_000_000,2),"avg_aum_per_client_lakh":round((total_aum/len(CLIENTS_DB))/100_000,2),"risk_distribution":risk_dist,"city_distribution":city_dist,"total_funds_tracked":len(FUND_NAV_DB),"generated_at":datetime.now().isoformat()}

@app.post("/dev/simulate-market")
def simulate_market():
    changes = {}
    for fund in FUND_NAV_DB:
        pct = random.uniform(-0.03, 0.03)
        old = FUND_NAV_DB[fund]
        new = round(old * (1 + pct), 2)
        FUND_NAV_DB[fund] = new
        changes[fund] = {"old":old,"new":new,"change_pct":round(pct*100,2)}
    return {"message":"Market simulated","nav_changes":changes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)