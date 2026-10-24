import geopandas as gpd, glob

for f in glob.glob("data/extracted/**/*.shp", recursive=True):
    g = gpd.read_file(f)
    print("\n==", f, "| rows:", len(g))
    print(list(g.columns))
    print(g.head(3).drop(columns="geometry", errors="ignore"))

with open(glob.glob("data/extracted/matched_upstream/**/*.txt", recursive=True)[0]) as t:
    for _ in range(10):
        print(t.readline().rstrip())