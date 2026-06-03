"""Unit tests for pyxecm.helper.data module."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from pyxecm.helper.data import Data


@pytest.fixture
def sample_data():
    """Return sample list-of-dicts data."""
    return [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "LA"},
        {"name": "Charlie", "age": 35, "city": "NYC"},
    ]


@pytest.fixture
def data_obj(sample_data):
    """Return a Data instance from sample_data."""
    return Data(init_data=sample_data)


class TestDataInit:
    """Tests for Data.__init__() and basic properties."""

    def test_init_from_list_of_dicts(self, sample_data):
        d = Data(init_data=sample_data)
        assert len(d) == 3
        assert list(d.get_data_frame().columns) == ["name", "age", "city"]

    def test_init_from_dataframe(self, sample_data):
        df = pd.DataFrame(sample_data)
        d = Data(init_data=df)
        assert len(d) == 3

    def test_init_from_dict(self):
        d = Data(init_data={"key": "value", "num": 42})
        assert len(d) == 1
        assert "key" in d.get_data_frame().columns

    def test_init_empty_with_columns(self):
        d = Data(columns=["a", "b", "c"])
        assert len(d) == 0
        assert list(d.get_data_frame().columns) == ["a", "b", "c"]

    def test_init_none(self):
        d = Data()
        assert len(d) == 0

    def test_init_invalid_type(self):
        with pytest.raises(TypeError):
            Data(init_data="invalid")

    def test_init_with_dtypes(self):
        data = [{"val": "42"}]
        d = Data(init_data=data, dtypes={"val": "int64"})
        assert d.get_data_frame()["val"].dtype == "int64"


class TestDataDunder:
    """Tests for __len__, __str__, __repr__, __getitem__, __setitem__, __delitem__."""

    def test_len(self, data_obj):
        assert len(data_obj) == 3

    def test_str(self, data_obj):
        result = str(data_obj)
        assert "Alice" in result

    def test_repr(self, data_obj):
        result = repr(data_obj)
        assert "Data" in result

    def test_getitem(self, data_obj):
        series = data_obj["name"]
        assert list(series) == ["Alice", "Bob", "Charlie"]

    def test_setitem(self, data_obj):
        data_obj["country"] = "US"
        assert "country" in data_obj.get_data_frame().columns

    def test_delitem(self, data_obj):
        del data_obj["city"]
        assert "city" not in data_obj.get_data_frame().columns


class TestDataGetSet:
    """Tests for get/set methods."""

    def test_get_data_frame(self, data_obj):
        df = data_obj.get_data_frame()
        assert isinstance(df, pd.DataFrame)

    def test_set_data_frame(self, data_obj):
        new_df = pd.DataFrame({"x": [1, 2]})
        data_obj.set_data_frame(new_df)
        assert len(data_obj) == 2
        assert "x" in data_obj.get_data_frame().columns

    def test_get_columns(self, data_obj):
        cols = data_obj.get_columns()
        assert list(cols) == ["name", "age", "city"]


class TestDataAppend:
    """Tests for Data.append()."""

    def test_append_dict(self, data_obj):
        result = data_obj.append({"name": "Dave", "age": 40, "city": "SF"})
        assert result is True
        assert len(data_obj) == 4

    def test_append_list(self, data_obj):
        result = data_obj.append([{"name": "Eve", "age": 28, "city": "DC"}])
        assert result is True
        assert len(data_obj) == 4

    def test_append_dataframe(self, data_obj):
        df = pd.DataFrame([{"name": "Frank", "age": 50, "city": "CHI"}])
        result = data_obj.append(df)
        assert result is True
        assert len(data_obj) == 4

    def test_append_data_object(self, data_obj):
        other = Data(init_data=[{"name": "Grace", "age": 22, "city": "SEA"}])
        result = data_obj.append(other)
        assert result is True
        assert len(data_obj) == 4


class TestDataMerge:
    """Tests for Data.merge()."""

    def test_merge_inner(self):
        left = Data(init_data=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        right_df = pd.DataFrame([{"id": 1, "score": 90}, {"id": 3, "score": 70}])
        result = left.merge(right_df, on="id", how="inner")
        assert result is not None
        # merge returns a DataFrame with the merged data
        assert len(result) == 1


class TestDataStrip:
    """Tests for Data.strip()."""

    def test_strip_whitespace_object_dtype(self):
        df = pd.DataFrame({"name": ["  Alice  "], "city": ["  NYC  "]})
        # Force object dtype (strip checks for dtype == "object")
        df = df.astype("object")
        d = Data(init_data=df)
        d.strip()
        result = d.get_data_frame()
        assert result["name"].iloc[0] == "Alice"
        assert result["city"].iloc[0] == "NYC"


class TestDataDeduplicate:
    """Tests for Data.deduplicate()."""

    def test_deduplicate(self):
        d = Data(
            init_data=[
                {"name": "Alice", "age": 30},
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
        )
        d.deduplicate(unique_fields=["name"])
        assert len(d) == 2


class TestDataSort:
    """Tests for Data.sort()."""

    def test_sort_ascending(self, data_obj):
        data_obj.sort(sort_fields=["age"], ascending=True)
        ages = list(data_obj["age"])
        assert ages == sorted(ages)

    def test_sort_descending(self, data_obj):
        data_obj.sort(sort_fields=["age"], ascending=False)
        ages = list(data_obj["age"])
        assert ages == sorted(ages, reverse=True)


class TestDataColumns:
    """Tests for column manipulation methods."""

    def test_drop_columns(self, data_obj):
        data_obj.drop_columns(["city"])
        assert "city" not in data_obj.get_data_frame().columns

    def test_keep_columns(self, data_obj):
        data_obj.keep_columns(["name", "age"])
        assert list(data_obj.get_data_frame().columns) == ["name", "age"]

    def test_rename_column(self, data_obj):
        result = data_obj.rename_column("city", "location")
        assert result is True
        assert "location" in data_obj.get_data_frame().columns
        assert "city" not in data_obj.get_data_frame().columns


class TestDataColumnTypes:
    """Tests for column type detection methods."""

    def test_is_string_column(self, data_obj):
        assert data_obj.is_string_column(data_obj["name"]) == True  # noqa: E712

    def test_is_dict_column(self):
        d = Data(init_data=[{"col": {"k": "v"}}, {"col": {"k2": "v2"}}])
        assert d.is_dict_column(d["col"]) == True  # noqa: E712

    def test_is_list_column(self):
        d = Data(init_data=[{"col": [1, 2]}, {"col": [3, 4]}])
        assert d.is_list_column(d["col"]) == True  # noqa: E712


class TestDataJsonIO:
    """Tests for JSON load/save."""

    def test_save_and_load_json(self, data_obj):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = str(Path(tmpdir) / "test.json")
            result = data_obj.save_json_data(filepath)
            assert result is True

            new_data = Data()
            load_result = new_data.load_json_data(filepath)
            assert load_result is True
            assert len(new_data) == 3


class TestDataPartitionate:
    """Tests for Data.partitionate()."""

    def test_partitionate(self, data_obj):
        parts = data_obj.partitionate(2)
        assert len(parts) == 2
        total_rows = sum(len(p) for p in parts)
        assert total_rows == 3


class TestDataFilter:
    """Tests for Data.filter()."""

    def test_filter_by_value(self, data_obj):
        data_obj.filter(conditions=[{"field": "city", "value": "NYC", "operator": "eq"}])
        assert len(data_obj) == 2
        assert all(data_obj["city"] == "NYC")


class TestDataFillNa:
    """Tests for Data.fill_na_in_column()."""

    def test_fill_na(self):
        d = Data(init_data=[{"name": "Alice", "score": None}, {"name": "Bob", "score": 80}])
        d.fill_na_in_column("score", 0)
        scores = list(d["score"])
        assert scores[0] == 0
        assert scores[1] == 80


class TestDataDropRow:
    """Tests for Data.drop_row() and drop_rows()."""

    def test_drop_row(self, data_obj):
        data_obj.drop_row(0)
        assert len(data_obj) == 2

    def test_drop_rows_by_mask(self, data_obj):
        mask = data_obj["city"] == "NYC"
        data_obj.drop_rows(mask)
        assert len(data_obj) == 1
        assert data_obj["city"].iloc[0] == "LA"


class TestDataSetValue:
    """Tests for Data.set_value()."""

    def test_set_value_all(self, data_obj):
        data_obj.set_value("city", "Unknown")
        assert all(data_obj["city"] == "Unknown")

    def test_set_value_with_condition(self, data_obj):
        mask = data_obj["name"] == "Alice"
        data_obj.set_value("city", "Boston", condition=mask)
        df = data_obj.get_data_frame()
        assert df.loc[df["name"] == "Alice", "city"].iloc[0] == "Boston"
        assert df.loc[df["name"] == "Bob", "city"].iloc[0] == "LA"


class TestDataAddColumn:
    """Tests for Data.add_column()."""

    def test_add_column(self, data_obj):
        result = data_obj.add_column("country")
        assert result is True
        assert "country" in data_obj.get_data_frame().columns
