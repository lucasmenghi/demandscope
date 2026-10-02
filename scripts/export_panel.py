from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data import load_panel,DEV_END

panel,calendar,_ = load_panel(ROOT/'data/raw')
target = ROOT/'data/processed'
target.mkdir(parents=True,exist_ok=True)
panel.loc[panel.day.le(DEV_END)].to_csv(target/'history.csv',index=False)
calendar.to_csv(target/'calendar.csv',index=False)
print('Local development history and calendar exported; neither is versioned.')
