"""Notebook-compatible input features and exported model loading."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / 'kc_house_data_NaN.csv'

def load_data():
    raw = pd.read_csv(DATA_PATH).drop(columns=['Unnamed: 0', 'id'], errors='ignore')
    raw['date'] = pd.to_datetime(raw['date'], format='%Y%m%dT%H%M%S')
    clean = raw.drop_duplicates().copy()
    return raw, clean.loc[~(clean.bedrooms.gt(15) | clean.bathrooms.le(0))].copy()

def engineer(frame):
    x = frame.copy()
    x['sale_year'] = x.date.dt.year
    x['sale_month'] = x.date.dt.month
    x['house_age'] = (x.sale_year - x.yr_built).clip(lower=0)
    x['is_renovated'] = (x.yr_renovated > 0).astype(int)
    x['years_since_renovation'] = np.where(x.is_renovated, (x.sale_year-x.yr_renovated).clip(lower=0), x.house_age)
    x['total_rooms'] = x.bedrooms + x.bathrooms
    x['has_basement'] = (x.sqft_basement > 0).astype(int)
    x['living_to_lot_ratio'] = x.sqft_living / x.sqft_lot.clip(lower=1)
    x = x.drop(columns=['price','date','sqft_above','sqft_basement','yr_built','yr_renovated'], errors='ignore')
    x['zipcode'] = x.zipcode.astype(str)
    return x

def get_artifacts(clean):
    """Load only models exported by a successful execution of the source notebook."""
    import json
    path = ROOT / 'artifacts' / 'notebook_models.joblib'
    manifest_path = ROOT / 'artifacts' / 'notebook_manifest.json'
    if not path.exists() or not manifest_path.exists():
        raise RuntimeError('Run python run_notebook.py first to execute the notebook and export its models and plots.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    notebook = json.loads((ROOT / manifest['notebook']).read_text(encoding='utf-8'))
    code = '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code')
    if hashlib.sha256(DATA_PATH.read_bytes()).hexdigest() != manifest['data_sha256'] or hashlib.sha256(code.encode()).hexdigest() != manifest['source_sha256']:
        raise RuntimeError('The dataset or notebook changed. Run python run_notebook.py to refresh the dashboard analysis.')
    saved = joblib.load(path)
    saved['manifest'] = manifest
    return saved
