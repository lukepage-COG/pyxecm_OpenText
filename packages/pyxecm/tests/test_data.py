"""Tests for the Data helper class."""

import pandas as pd
import pytest
from pyxecm.helper.data import Data


class TestDataInit:
    def test_from_dataframe(self):
        df = pd.DataFrame({"name": ["A", "B"], "value": [1, 2]})
        data = Data(init_data=df)
        assert len(data) == 2

    def test_from_list(self):
        items = [{"name": "A", "value": 1}, {"name": "B", "value": 2}]
        data = Data(init_data=items)
        assert len(data) == 2

    def test_empty_data(self):
        data = Data()
        assert len(data) == 0


class TestDataOperations:
    def _sample_data(self):
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "department": ["HR", "IT", "HR"],
        })
        return Data(init_data=df)

    def test_len(self):
        data = self._sample_data()
        assert len(data) == 3

    def test_get_columns(self):
        data = self._sample_data()
        columns = data.get_columns()
        assert "id" in columns
        assert "name" in columns
        assert "department" in columns

    def test_str_representation(self):
        data = self._sample_data()
        result = str(data)
        assert "Alice" in result

    def test_getitem(self):
        data = self._sample_data()
        names = data["name"]
        assert isinstance(names, pd.Series)
        assert len(names) == 3

    def test_setitem(self):
        data = self._sample_data()
        data["new_col"] = "default"
        df = data.get_data_frame()
        assert "new_col" in df.columns

    def test_delitem(self):
        data = self._sample_data()
        del data["department"]
        columns = data.get_columns()
        assert "department" not in columns

    def test_get_data_frame(self):
        data = self._sample_data()
        df = data.get_data_frame()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_set_data_frame(self):
        data = Data()
        new_df = pd.DataFrame({"x": [1, 2]})
        data.set_data_frame(new_df)
        assert len(data) == 2

    def test_append_list(self):
        data = Data(init_data=[{"a": 1}], columns=["a"])
        result = data.append({"a": 2})
        assert result is True
        assert len(data) == 2


class TestDataCSV:
    def test_load_csv_from_file(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,value\nAlice,1\nBob,2")
        data = Data()
        result = data.load_csv_data(csv_path=str(csv_file))
        assert result is True
        assert len(data) == 2
