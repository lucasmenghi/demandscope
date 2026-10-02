"""Download the public M5 mirror used by Nixtla's datasetsforecast loader."""
from pathlib import Path
import hashlib
import json
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/raw'
RAW.mkdir(parents=True,exist_ok=True)
URL = 'https://github.com/Nixtla/m5-forecasts/raw/main/datasets/m5.zip'
archive = RAW/'m5.zip'
if not archive.exists():
    response = requests.get(URL,timeout=240)
    response.raise_for_status()
    archive.write_bytes(response.content)
required = {'calendar.csv','sales_train_evaluation.csv'}
with zipfile.ZipFile(archive) as z:
    print('Archive files:',z.namelist(),flush=True)
    for name in z.namelist():
        leaf = Path(name).name
        if leaf in required:
            (RAW/leaf).write_bytes(z.read(name))
if any(not (RAW/name).exists() for name in required):
    raise ValueError('Missing expected M5 files')
manifest = {'original_source':'https://www.kaggle.com/competitions/m5-forecasting-accuracy/data',
    'organizer':'https://github.com/Mcompetitions/M5-methods',
    'mirror':URL,'mirror_documentation':'https://github.com/Nixtla/datasetsforecast/blob/main/datasetsforecast/m5.py',
    'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
    'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in RAW.glob('*.csv')},
    'schema_note':'Nixtla mirror omits the redundant id column; item_id and store_id identify each original series.',
    'rights':'Subject to M5 competition rules; no raw data is redistributed.'}
(ROOT/'reports').mkdir(exist_ok=True)
(ROOT/'reports/data_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Original M5 schema extracted and hashes recorded.',flush=True)
