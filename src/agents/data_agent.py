from typing import Dict, Any
from loguru import logger

from utils.load_data import load_dataset
from utils.retry import retry
from utils.summary import dataset_summary


class DataAgent:
    def __init__(self):
        self.log = logger.bind(agent="data")  
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        data_path = config["data"]["path"]
        self.log.info(f"Loading dataset from: {data_path}")
        try:
            df = retry(
                lambda: load_dataset(data_path),
                attempts=self.config.get("retry", {}).get("attempts", 3),
                delay=self.config.get("retry", {}).get("delay", 1.0),
                agent="data"
            )

            self.log.info(f"Dataset loaded successfully. Shape: {df.shape}")
            summary = dataset_summary(df)
            self.log.info("Dataset summary generated.")

            return {"df": df, "summary": summary}

        except Exception as e:
            self.log.error(f"Failed to load or summarize dataset. Error: {e}")
            raise e  
