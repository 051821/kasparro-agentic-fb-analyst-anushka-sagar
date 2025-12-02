import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","src")))
from utils.data_schema import SchemaValidator
import pandas as pd
import pytest

def test_schema_validator_missing_column():
    cfg={"schema":{"expected_columns":["a","b"]}}
    v = SchemaValidator(cfg)
    df = pd.DataFrame({"a":[1,2]})
    with pytest.raises(Exception):
        v.validate(df)

def test_detect_drift_small_dataset_no_date():
    cfg={"schema":{}}
    v = SchemaValidator(cfg)
    df=pd.DataFrame({"x":[1,2]})
    assert v.detect_drift(df)==[]
