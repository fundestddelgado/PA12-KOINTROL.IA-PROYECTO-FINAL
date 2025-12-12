import pandas as pd
import ast


class SolarDatasetBuilder:

    def __init__(self, dt1_path, dt2_path, dt3_path):
        self.dt1_path = dt1_path
        self.dt2_path = dt2_path
        self.dt3_path = dt3_path

    def _load_csv(self, path):
        df = pd.read_csv(path)
        return df

    def _extract_lon_lat(self, df):
        import ast
        import json

        def fix_geo_string(s):
            if not isinstance(s, str):
                return None
            # Arregla comillas duplicadas
            s = s.replace('""', '"').strip()
            # Remueve comillas externas
            if s.startswith('"') and s.endswith('"'):
                s = s[1:-1]
            # Intenta JSON
            try:
                return json.loads(s)
            except:
                pass
            # Intenta literal_eval
            try:
                return ast.literal_eval(s)
            except:
                return None

        def parse_geo(value):
            geo = fix_geo_string(value)
            if not isinstance(geo, dict):
                return pd.Series({"lon": None, "lat": None})
            coords = geo.get("coordinates", [None, None])
            return pd.Series({"lon": coords[0], "lat": coords[1]})

        coords = df[".geo"].apply(parse_geo)
        df = pd.concat([df, coords], axis=1)

        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")

        df["lon"] = df["lon"].round(7)
        df["lat"] = df["lat"].round(7)

        # Si TODO queda NaN, ese es el motivo de dataset vacio
        print("Coordenadas validas:", df[["lon", "lat"]].notna().all(axis=1).sum())

        df = df.dropna(subset=["lon", "lat"])
        return df



    def _normalize_dates(self, df):
        df["date"] = pd.to_datetime(df["date"])
        return df

    def _clean_columns(self, df):
        if "system:index" in df.columns:
            df = df.drop(columns=["system:index"])
        return df

    def _merge_all(self, d1, d2, d3):
        # Merge entre dt1 y dt2
        m12 = pd.merge(
            d1,
            d2,
            on=["lon", "lat", "date"],
            how="inner",
            suffixes=("_dt1", "_dt2")
        )

        # Merge con dt3 (domina dt3)
        merged = pd.merge(
            m12,
            d3,
            on=["lon", "lat", "date"],
            how="inner",
            suffixes=("", "_dup")
        )

        # Remover duplicados de dt1 y dt2
        cols_to_drop = [c for c in merged.columns if c.endswith("_dt1") or c.endswith("_dt2")]

        # Remover duplicados respecto a dt3
        cols_to_drop += [c for c in merged.columns if c.endswith("_dup")]

        merged = merged.drop(columns=cols_to_drop)

        return merged

    def build(self, save_path="./solar_merged.csv"):
        print("Loading datasets...")
        dt1 = self._load_csv(self.dt1_path)
        dt2 = self._load_csv(self.dt2_path)
        dt3 = self._load_csv(self.dt3_path)

        print("Extracting lon/lat...")
        dt1 = self._extract_lon_lat(dt1)
        dt2 = self._extract_lon_lat(dt2)
        dt3 = self._extract_lon_lat(dt3)

        print("Normalizing dates...")
        dt1 = self._normalize_dates(dt1)
        dt2 = self._normalize_dates(dt2)
        dt3 = self._normalize_dates(dt3)

        print("Cleaning columns...")
        dt1 = self._clean_columns(dt1)
        dt2 = self._clean_columns(dt2)
        dt3 = self._clean_columns(dt3)

        print("Merging datasets (inner, removing pixels that do not match)...")
        merged = self._merge_all(dt1, dt2, dt3)

        print("Removing rows with missing coordinates...")
        merged = merged.dropna(subset=["lon", "lat"])

        print("Sorting...")
        merged = merged.sort_values(by=["lon", "lat", "date"]).reset_index(drop=True)

        print(f"Saving final dataset: {save_path}")
        merged.to_csv(save_path, index=False)

        print("Done.")
        return merged


if __name__ == "__main__":
    builder = SolarDatasetBuilder(
        r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\SolarKointrol\Panama_AgERA5_JanJun2025.csv",
        r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\SolarKointrol\Panama_ClimateVars_Clean_JanJun2025.csv",
        r"C:\Users\alan7\OneDrive\Documentos\Codigo\Python\Proyectos\SolarKointrol\Panama_ERA5Land_JanJun2025.csv"
    )

    builder.build("./solar_merged.csv")
