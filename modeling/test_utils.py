import numpy as np
import pandas as pd

import utils


def test_download_preprocessed_data_range(mocker):
    read_preprocessed_data = mocker.patch('utils.download_preprocessed_data', return_value=None)

    gcs = "GCS"
    symbol = "symbol"
    data_directory = "./dir"
    utils.download_preprocessed_data_range(
        gcs, symbol, 2019, 10, 2020, 2, data_directory
    )

    assert read_preprocessed_data.call_args_list == [
        mocker.call(gcs, symbol, 2019, 10, data_directory),
        mocker.call(gcs, symbol, 2019, 11, data_directory),
        mocker.call(gcs, symbol, 2019, 12, data_directory),
        mocker.call(gcs, symbol, 2020, 1, data_directory),
        mocker.call(gcs, symbol, 2020, 2, data_directory),
    ]


def test_read_preprocessed_data_range(mocker):
    read_preprocessed_data = mocker.patch('utils.read_preprocessed_data', return_value=pd.DataFrame())

    symbol = "symbol"
    data_directory = "./dir"
    returned = utils.read_preprocessed_data_range(
        symbol, 2019, 10, 2020, 2, data_directory
    )

    assert isinstance(returned, pd.DataFrame)

    assert read_preprocessed_data.call_args_list == [
        mocker.call(symbol, 2019, 10, data_directory),
        mocker.call(symbol, 2019, 11, data_directory),
        mocker.call(symbol, 2019, 12, data_directory),
        mocker.call(symbol, 2020, 1, data_directory),
        mocker.call(symbol, 2020, 2, data_directory),
    ]


def test_aggregate_time():
    s = pd.Series(
        data=np.arange(15),
        index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:14:00", freq="1min")
    )
    actual_result = utils.aggregate_time(s, "5min", "min")
    expected_result = pd.Series(
        data=np.array([0, 5, 10]),
        index=pd.DatetimeIndex([
            "2022-01-01 00:00:00",
            "2022-01-01 00:05:00",
            "2022-01-01 00:10:00",
        ])
    )
    pd.testing.assert_series_equal(actual_result, expected_result, check_freq=False)

    s = pd.Series(
        data=np.arange(15),
        index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:14:00", freq="1min")
    )
    actual_result = utils.aggregate_time(s, "5min", "max")
    expected_result = pd.Series(
        data=np.array([4, 9, 14]),
        index=pd.DatetimeIndex([
            "2022-01-01 00:00:00",
            "2022-01-01 00:05:00",
            "2022-01-01 00:10:00",
        ])
    )
    pd.testing.assert_series_equal(actual_result, expected_result, check_freq=False)


def test_merge_bid_ask():
    index = pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:03:00", freq="1min")
    df = pd.DataFrame({
        "bid_open": [0, 1, 2, 3],
        "ask_open": [2, 3, 4, 5],
        "bid_high": [0, 2, 4, 6],
        "ask_high": [2, 4, 6, 8],
        "bid_low": [0, 3, 6, 9],
        "ask_low": [2, 5, 8, 11],
        "bid_close": [0, 4, 8, 12],
        "ask_close": [2, 6, 10, 14],
    }, index=index)
    actual_result = utils.merge_bid_ask(df)
    expected_result = pd.DataFrame({
        "open": [1, 2, 3, 4],
        "high": [1, 3, 5, 7],
        "low": [1, 4, 7, 10],
        "close": [1, 5, 9, 13],
    }, index=index)
    pd.testing.assert_frame_equal(actual_result, expected_result, check_dtype=False)


def test_resample():
    df_1min = pd.DataFrame({
        "open": [0, 1, 2, 3, 4, 5, 6, 7],
        "high": [0, 10, 20, 30, 40, 50, 60, 70],
        "low": [0, -10, -20, -30, -40, -50, -60, -70],
        "close": [0, -1, -2, -3, -4, -5, -6, -7],
    }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="1min"))
    actual_result = utils.resample(df_1min, freqs=["1min", "2min", "4min"])
    expected_result = {
        "1min": pd.DataFrame({
            "open": [0, 1, 2, 3, 4, 5, 6, 7],
            "high": [0, 10, 20, 30, 40, 50, 60, 70],
            "low": [0, -10, -20, -30, -40, -50, -60, -70],
            "close": [0, -1, -2, -3, -4, -5, -6, -7],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="1min")),
        "2min": pd.DataFrame({
            "open": [0, 2, 4, 6],
            "high": [10, 30, 50, 70],
            "low": [-10, -30, -50, -70],
            "close": [-1, -3, -5, -7],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="2min")),
        "4min": pd.DataFrame({
            "open": [0, 4],
            "high": [30, 70],
            "low": [-30, -70],
            "close": [-3, -7],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="4min")),
    }
    # assert actual_result.keys() == expected_result.keys()
    # for freq in expected_result:
    #     pd.testing.assert_frame_equal(expected_result[freq], actual_result[freq])
    assert_df_dict_equal(actual_result, expected_result)


def test_align_frequency():
    base_index = pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="1min")
    df_dict = {
        "1min": pd.DataFrame({
            "open": [0, 1, 2, 3, 4, 5, 6, 7],
            "high": [0, 10, 20, 30, 40, 50, 60, 70],
            "low": [0, -10, -20, -30, -40, -50, -60, -70],
            "close": [0, -1, -2, -3, -4, -5, -6, -7],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="1min")),
        "2min": pd.DataFrame({
            "open": [0, 2, 4, 6],
            "high": [10, 30, 50, 70],
            "low": [-10, -30, -50, -70],
            "close": [-1, -3, -5, -7],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="2min")),
        "4min": pd.DataFrame({
            "open": [0, 4],
            "high": [30, 70],
            "low": [-30, -70],
            "close": [-3, -7],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="4min")),
    }
    actual_result = utils.align_frequency(base_index, df_dict)
    expected_result = pd.DataFrame({
        "open_1min": [0, 1, 2, 3, 4, 5, 6, 7],
        "high_1min": [0, 10, 20, 30, 40, 50, 60, 70],
        "low_1min": [0, -10, -20, -30, -40, -50, -60, -70],
        "close_1min": [0, -1, -2, -3, -4, -5, -6, -7],
        "open_2min": [0, 0, 2, 2, 4, 4, 6, 6],
        "high_2min": [10, 10, 30, 30, 50, 50, 70, 70],
        "low_2min": [-10, -10, -30, -30, -50, -50, -70, -70],
        "close_2min": [-1, -1, -3, -3, -5, -5, -7, -7],
        "open_4min": [0, 0, 0, 0, 4, 4, 4, 4],
        "high_4min": [30, 30, 30, 30, 70, 70, 70, 70],
        "low_4min": [-30, -30, -30, -30, -70, -70, -70, -70],
        "close_4min": [-3, -3, -3, -3, -7, -7, -7, -7],
    }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="1min"))
    pd.testing.assert_frame_equal(expected_result, actual_result)


def test_create_time_features():
    pass


def test_compute_sma():
    s = pd.Series([0, 4, 2, 3, 6, 4, 6, 9])
    actual_result = utils.compute_sma(s, sma_window_size=4)
    expected_result = pd.Series([
        np.nan,
        np.nan,
        np.nan,
        (0+4+2+3)/4,
        (4+2+3+6)/4,
        (2+3+6+4)/4,
        (3+6+4+6)/4,
        (6+4+6+9)/4,
    ], dtype=np.float32)
    pd.testing.assert_series_equal(expected_result, actual_result)


def test_compute_fraction():
    s = pd.Series([100.123, 104.456, 90.789])
    actual_result = utils.compute_fraction(s, base=0.01)
    expected_result = pd.Series([12.3, 45.6, 78.9])
    pd.testing.assert_series_equal(expected_result, actual_result)


def test_create_lagged_features():
    index = pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:07:00", freq="1min")
    df = pd.DataFrame({
        "open": [0, 1, 2, 3, 4, 5, 6, 7],
        "high": [0, 10, 20, 30, 40, 50, 60, 70],
        "low": [0, -10, -20, -30, -40, -50, -60, -70],
        "close": [0, -1, -2, -3, -4, -5, -6, -7],
    }, index=index)
    actual_result = utils.create_lagged_features(df, lag_max=2)
    expected_result = pd.DataFrame({
        "open_lag1": [np.nan, 0, 1, 2, 3, 4, 5, 6],
        "open_lag2": [np.nan, np.nan, 0, 1, 2, 3, 4, 5],
        "high_lag1": [np.nan, 0, 10, 20, 30, 40, 50, 60],
        "high_lag2": [np.nan, np.nan, 0, 10, 20, 30, 40, 50],
        "low_lag1": [np.nan, 0, -10, -20, -30, -40, -50, -60],
        "low_lag2": [np.nan, np.nan, 0, -10, -20, -30, -40, -50],
        "close_lag1": [np.nan, 0, -1, -2, -3, -4, -5, -6],
        "close_lag2": [np.nan, np.nan, 0, -1, -2, -3, -4, -5],
    }, index=index)
    pd.testing.assert_frame_equal(expected_result, actual_result)


def test_create_features():
    actual_base_index, actual_data = utils.create_features(
        df = pd.DataFrame({
            "open": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "high": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110],
            "low": [0, -10, -20, -30, -40, -50, -60, -70, -80, -90, -100, -110],
            "close": [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11],
        }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:11:00", freq="1min")),
        symbol = "usdjpy",
        timings = ["open", "low"],
        freqs = ["1min", "2min"],
        lag_max = 2,
        sma_timing = "open",
        sma_window_sizes = [2, 4],
        sma_window_size_center = 2
    )
    expected_base_index = pd.date_range("2022-01-01 00:10:00", "2022-01-01 00:11:00", freq="1min")
    expected_data = {
        "sequential": {
            "1min": pd.DataFrame({
                "open": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "low": [0, -10, -20, -30, -40, -50, -60, -70, -80, -90, -100, -110],
                "sma2": [np.nan, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5],
                "sma4": [np.nan, np.nan, np.nan, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
            }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:11:00", freq="1min")),
            "2min": pd.DataFrame({
                "open": [0, 2, 4, 6, 8, 10],
                "low": [-10, -30, -50, -70, -90, -110],
                "sma2": [np.nan, 1, 3, 5, 7, 9],
                "sma4": [np.nan, np.nan, np.nan, 3, 5, 7],
            }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:11:00", freq="2min")),
        },
        "continuous": {
            "1min": pd.DataFrame({
                "sma2_frac_lag1": [np.nan, np.nan, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
                "hour": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "day_of_week": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
                "month": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:11:00", freq="1min")),
            "2min": pd.DataFrame({
                "sma2_frac_lag1": [np.nan, np.nan, 0, 0, 0, 0],
            }, index=pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:11:00", freq="2min")),
        }
    }
    assert (actual_base_index == expected_base_index).all()
    assert_df_dict_equal(actual_data, expected_data, check_dtype=False)


def test_compute_ctirical_idxs():
    actual_critical_idxs = utils.compute_critical_idxs(
        values = np.array([1., 2., 3., 0., 2., 1., 4., 3., 1.]),
        thresh_hold = 1.5
    )
    expected_critical_idxs = np.array([2, 3, 6, 8])
    np.testing.assert_equal(actual_critical_idxs, expected_critical_idxs)

    actual_critical_idxs = utils.compute_critical_idxs(
        values = np.array([3., 2., 1., 0., 1., 2., 1., 0.9, 0.8]),
        thresh_hold = 1.5
    )
    expected_critical_idxs = np.array([0, 3, 5])
    np.testing.assert_equal(actual_critical_idxs, expected_critical_idxs)


def assert_df_dict_equal(df_dict1, df_dict2, **kwargs):
    if isinstance(df_dict1, pd.DataFrame):
        pd.testing.assert_frame_equal(df_dict1, df_dict2, **kwargs)
    else:
        assert df_dict1.keys() == df_dict2.keys()
        for key in df_dict1:
            assert_df_dict_equal(df_dict1[key], df_dict2[key], **kwargs)
