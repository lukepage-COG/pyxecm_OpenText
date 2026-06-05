"""Tests for the Data helper class."""


from pyxecm.helper.data import Data


class TestDataInit:
    def test_empty_init(self):
        data = Data()
        assert data is not None
        assert len(data) == 0

    def test_init_with_columns(self):
        data = Data(columns=["name", "age", "city"])
        assert len(data) == 0
        assert list(data.columns) == ["name", "age", "city"]

    def test_init_with_list_of_dicts(self):
        records = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        data = Data(init_data=records)
        assert len(data) == 2

    def test_init_with_dtypes(self):
        records = [{"count": "10", "label": "a"}]
        data = Data(init_data=records, dtypes={"count": "int64"})
        assert len(data) == 1


class TestDataLen:
    def test_len_empty(self):
        data = Data()
        assert len(data) == 0

    def test_len_with_data(self):
        records = [{"a": 1}, {"a": 2}, {"a": 3}]
        data = Data(init_data=records)
        assert len(data) == 3


class TestDataGetSetItem:
    def test_getitem(self):
        records = [{"name": "Alice", "age": 30}]
        data = Data(init_data=records)
        col = data["name"]
        assert col.iloc[0] == "Alice"

    def test_setitem(self):
        data = Data(init_data=[{"a": 1}])
        data["b"] = [99]
        assert data["b"].iloc[0] == 99

    def test_delitem(self):
        data = Data(init_data=[{"a": 1, "b": 2}])
        del data["b"]
        assert "b" not in data.columns


class TestDataContains:
    def test_contains_existing_column(self):
        data = Data(init_data=[{"x": 1, "y": 2}])
        assert "x" in data.columns
        assert "z" not in data.columns


class TestDataColumns:
    def test_columns(self):
        data = Data(columns=["col1", "col2"])
        cols = data.columns
        assert "col1" in cols
        assert "col2" in cols


class TestDataAppend:
    def test_append_dict(self):
        data = Data(columns=["name", "value"])
        data.append({"name": "test", "value": 42})
        assert len(data) == 1

    def test_append_multiple(self):
        data = Data(columns=["x"])
        data.append({"x": 1})
        data.append({"x": 2})
        data.append({"x": 3})
        assert len(data) == 3

    def test_append_list_of_dicts(self):
        data = Data(columns=["x"])
        data.append([{"x": 1}, {"x": 2}])
        assert len(data) == 2


class TestDataStr:
    def test_str_representation(self):
        data = Data(init_data=[{"a": 1}])
        s = str(data)
        assert isinstance(s, str)
        assert len(s) > 0


class TestDataGetDataFrame:
    def test_get_data_frame(self):
        import pandas as pd

        data = Data(init_data=[{"a": 1}])
        df = data.get_data_frame()
        assert isinstance(df, pd.DataFrame)


class TestDataFromDict:
    def test_init_with_single_dict(self):
        data = Data(init_data={"name": "Alice", "age": 30})
        assert len(data) == 1


class TestDataCopy:
    def test_init_from_data_object(self):
        original = Data(init_data=[{"a": 1}, {"a": 2}])
        copy = Data(init_data=original)
        assert len(copy) == 2

    def test_init_from_dataframe(self):
        import pandas as pd

        df = pd.DataFrame([{"x": 10}])
        data = Data(init_data=df)
        assert len(data) == 1
