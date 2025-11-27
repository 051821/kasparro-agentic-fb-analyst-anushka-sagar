from typing import Dict, Any

from utils.load_data import load_dataset
from utils.summary import dataset_summary


class DataAgent:
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        data_path = config["data"]["path"]
        df = load_dataset(data_path)
        summary = dataset_summary(df)
        return {"df": df, "summary": summary}
