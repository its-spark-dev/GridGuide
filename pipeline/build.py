import geopandas as gpd, pandas as pd, numpy as np, os

D, OUT = "data/extracted/", "data/processed/"
os.makedirs(OUT, exist_ok=True)
RADIUS_M = 800  # "nearby damage" = within 800 meters of the house

def norm_circ(s):   # "CIR60" or "0000060" -> "0000060"
    return s.astype(str).str.extract(r"(\d+)")[0].fillna("").str.zfill(7)

def clean_prem(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(9)

print("loading...")
cust = gpd.read_file(D + "Data1/Customer_Clip.shp")[["premise_nu", "circuit_id", "critical_c", "geometry"]]
dmg = gpd.read_file(D + "Data1/arcos_prod_damage_09_28_Clip.shp")
cust["premise"] = clean_prem(cust["premise_nu"])
cust["circuit"] = norm_circ(cust["circuit_id"])
dmg["circuit"] = norm_circ(dmg["Circuit"])

# --- storms + historical repair days ---
dmg["report"] = pd.to_datetime(dmg["Report_Tim"], errors="coerce")
dmg["repaired"] = pd.to_datetime(dmg["Repaired_D"], errors="coerce")
dmg["storm"] = np.where(dmg["report"].isna(), "Unknown",
               np.where(dmg["report"] < "2025-01-01", "Sep 2024", "Feb 2025"))
dmg["days"] = (dmg["repaired"] - dmg["report"]).dt.days
dmg.loc[(dmg["days"] < 0) | (dmg["days"] > 30), "days"] = np.nan  # drop bad dates

# --- upstream chains ---
up = {}
with open(D + "matched_upstream/matched_upstream.txt") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            up[parts[0].strip().zfill(9)] = [p.split("*") for p in parts[1:] if p.count("*") == 3]
cust["chain_len"] = cust["premise"].map(lambda p: len(up[p]) if p in up else np.nan)

# --- feature 1: damage near the house ---
utm = cust.estimate_utm_crs()
c_m, d_m = cust.to_crs(utm), dmg.to_crs(utm)
buf = gpd.GeoDataFrame(geometry=d_m.buffer(RADIUS_M), crs=utm)
hits = gpd.sjoin(c_m[["geometry"]], buf, predicate="within")
cust["near_dmg"] = hits.groupby(level=0).size().reindex(cust.index, fill_value=0)

# --- feature 2: how hard the house's circuit was hit ---
circ_dmg = dmg.groupby("circuit").size()
circ_cust = cust.groupby("circuit").size()
cust["circ_dmg"] = cust["circuit"].map(circ_dmg).fillna(0).astype(int)
cust["circ_rate"] = cust["circuit"].map(circ_dmg / circ_cust * 100).fillna(0)  # per 100 houses

# --- risk score + band + confidence ---
pct = lambda s: s.rank(pct=True)
chain = cust["chain_len"].fillna(cust["chain_len"].median())
cust["score"] = 0.5 * pct(cust["near_dmg"]) + 0.3 * pct(cust["circ_rate"]) + 0.2 * pct(chain)
cust["band"] = pd.cut(cust["score"].rank(pct=True), [0, .4, .8, 1],
                      labels=["Low", "Medium", "High"], include_lowest=True)
cust["confidence"] = np.select(
    [cust["chain_len"].isna(), cust["circ_dmg"] >= 30, cust["circ_dmg"] >= 5],
    ["Low", "High", "Medium"], "Low")

# --- historical repair days for the circuit ---
hist = dmg.groupby("circuit")["days"].agg(
    hist_p50="median", hist_p80=lambda x: x.quantile(.8), hist_n="count")
cust = cust.join(hist, on="circuit")

# --- location + declared life-support flag (no addresses kept) ---
g = cust.to_crs(4326)
cust["lat"], cust["lon"] = g.geometry.y.round(5), g.geometry.x.round(5)
cust["life_support"] = cust["critical_c"].astype(str).str.startswith("LS")

keep = ["premise", "circuit", "lat", "lon", "near_dmg", "circ_dmg", "circ_rate", "chain_len",
        "score", "band", "confidence", "hist_p50", "hist_p80", "hist_n", "life_support"]
cust[keep].to_csv(OUT + "customers.csv", index=False)

# damage counts per circuit by type (baseline for the restoration calculator)
dmg.groupby(["circuit", "storm", "Asset_Type"]).agg(
    count=("Asset_Type", "size"), access_issue=("Access_Iss", lambda x: (x == "Yes").mean())
).reset_index().to_csv(OUT + "circuit_damage.csv", index=False)

print("\nbands:\n", cust["band"].value_counts())
print("\nconfidence:\n", cust["confidence"].value_counts())
print("\ndamage by storm:\n", dmg["storm"].value_counts())
print("\nrepair days by storm:\n", dmg.groupby("storm")["days"].describe())
print("\nsample:\n", cust[keep].sample(5, random_state=1).to_string())