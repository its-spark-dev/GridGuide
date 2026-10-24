import geopandas as gpd, pandas as pd
D = "data/extracted/"

def clean_id(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(9)

dmg  = gpd.read_file(D + "Data1/arcos_prod_damage_09_28_Clip.shp")
cust = gpd.read_file(D + "Data1/Customer_Clip.shp")
xfmr = gpd.read_file(D + "Data2/Transformer_Clip.shp")

print("===== DAMAGE: what values look like =====")
for c in ["Event", "Circuit", "Asset_Type", "Status", "Repaired", "Access_Iss",
          "Special_Eq", "Report_Tim", "Repaired_D"]:
    print(f"\n-- {c}")
    print(dmg[c].value_counts(dropna=False).head(8))

print("\n===== CUSTOMER sample =====")
print(cust[["premise_nu", "circuit_id", "aep_xfmr_l", "critical_c"]].head())
print(cust["critical_c"].value_counts().head())

print("\n===== TRANSFORMER circuit fields =====")
print(xfmr[["id", "location_n", "circuit_id", "circuit__1", "aep_circui", "aep_statio"]].head())

# Parse upstream chains
up = {}
with open(D + "matched_upstream/matched_upstream.txt") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        chain = []
        for p in parts[1:]:
            b = p.split("*")
            if len(b) == 4:
                chain.append({"table": b[0], "id": b[1], "type": b[2], "loc": b[3]})
        up[parts[0].strip().zfill(9)] = chain

prem = clean_id(cust["premise_nu"])
print("\n===== UPSTREAM =====")
print("premises in upstream file:", len(up))
print("customers that match an upstream chain:", prem.isin(up).sum(), "of", len(cust))
print("chain length stats:")
print(pd.Series([len(v) for v in up.values()]).describe())

print("\n===== DOES DAMAGE CONNECT TO CUSTOMERS BY CIRCUIT? =====")
cust_circ = set(cust["circuit_id"].astype(str))
dmg_circ = dmg["Circuit"].astype(str)
print("damage Circuit samples:  ", list(dmg_circ.unique()[:10]))
print("customer circuit samples:", list(cust_circ)[:10])
print("damage rows matching a customer circuit_id:", dmg_circ.isin(cust_circ).sum(), "of", len(dmg))