from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pytest import approx

from auto_trader.modeling import data


def test_read_cleansed_data(tmp_path: Path) -> None:
    df_202301 = pd.DataFrame({"x": [1, 2, 3]})
    df_202302 = pd.DataFrame({"x": [4, 5]})
    (tmp_path / "usdjpy").mkdir()
    df_202301.to_parquet(tmp_path / "usdjpy" / "202301.parquet")
    df_202302.to_parquet(tmp_path / "usdjpy" / "202302.parquet")

    df_actual = data.read_cleansed_data(
        cleansed_data_dir=tmp_path,
        symbol="usdjpy",
        yyyymm_begin=202301,
        yyyymm_end=202302,
    )

    df_expected = pd.concat([df_202301, df_202302], axis=0)
    pd.testing.assert_frame_equal(df_actual, df_expected)


def test_merge_bid_ask() -> None:
    index = pd.date_range("2022-01-01 00:00:00", "2022-01-01 00:03:00", freq="1min")
    df = pd.DataFrame(
        {
            "bid_open": [0, 1, 2, 3],
            "ask_open": [2, 3, 4, 5],
            "bid_high": [0, 2, 4, 6],
            "ask_high": [2, 4, 6, 8],
            "bid_low": [0, 3, 6, 9],
            "ask_low": [2, 5, 8, 11],
            "bid_close": [0, 4, 8, 12],
            "ask_close": [2, 6, 10, 14],
        },
        index=index,
    )
    actual_result = data.merge_bid_ask(df)
    expected_result = pd.DataFrame(
        {
            "open": [1, 2, 3, 4],
            "high": [1, 3, 5, 7],
            "low": [1, 4, 7, 10],
            "close": [1, 5, 9, 13],
        },
        index=index,
    )
    pd.testing.assert_frame_equal(actual_result, expected_result, check_dtype=False)


def test_calc_sma() -> None:
    s = pd.Series([0.0, 4.0, 2.0, 3.0, 6.0, 4.0, 6.0, 9.0], dtype=np.float32)
    actual_result = data.calc_sma(s, window_size=4)
    expected_result = pd.Series(
        [
            np.nan,
            np.nan,
            np.nan,
            (0 + 4 + 2 + 3) / 4,
            (4 + 2 + 3 + 6) / 4,
            (2 + 3 + 6 + 4) / 4,
            (3 + 6 + 4 + 6) / 4,
            (6 + 4 + 6 + 9) / 4,
        ],
        dtype=np.float32,
    )
    pd.testing.assert_series_equal(expected_result, actual_result)


def test_calc_moving_max() -> None:
    s = pd.Series([0.0, 4.0, 2.0, 3.0, 6.0, 4.0, 6.0, 9.0], dtype=np.float32)
    actual_result = data.calc_moving_max(s, window_size=4)
    expected_result = pd.Series(
        [
            np.nan,
            np.nan,
            np.nan,
            max(0.0, 4.0, 2.0, 3.0),
            max(4.0, 2.0, 3.0, 6.0),
            max(2.0, 3.0, 6.0, 4.0),
            max(3.0, 6.0, 4.0, 6.0),
            max(6.0, 4.0, 6.0, 9.0),
        ],
        dtype=np.float32,
    )
    pd.testing.assert_series_equal(expected_result, actual_result)


def test_calc_moving_min() -> None:
    s = pd.Series([0.0, 4.0, 2.0, 3.0, 6.0, 4.0, 6.0, 9.0], dtype=np.float32)
    actual_result = data.calc_moving_min(s, window_size=4)
    expected_result = pd.Series(
        [
            np.nan,
            np.nan,
            np.nan,
            min(0.0, 4.0, 2.0, 3.0),
            min(4.0, 2.0, 3.0, 6.0),
            min(2.0, 3.0, 6.0, 4.0),
            min(3.0, 6.0, 4.0, 6.0),
            min(6.0, 4.0, 6.0, 9.0),
        ],
        dtype=np.float32,
    )
    pd.testing.assert_series_equal(expected_result, actual_result)


def test_calc_sigma() -> None:
    s = pd.Series([0.0, 4.0, 2.0, 3.0, 6.0, 4.0, 6.0, 9.0], dtype=np.float32)
    actual_result = data.calc_sigma(s, window_size=4)
    expected_result = pd.Series(
        [
            np.nan,
            np.nan,
            np.nan,
            ((0**2 + 4**2 + 2**2 + 3**2) / 4 - ((0 + 4 + 2 + 3) / 4) ** 2) ** 0.5,
            ((4**2 + 2**2 + 3**2 + 6**2) / 4 - ((4 + 2 + 3 + 6) / 4) ** 2) ** 0.5,
            ((2**2 + 3**2 + 6**2 + 4**2) / 4 - ((2 + 3 + 6 + 4) / 4) ** 2) ** 0.5,
            ((3**2 + 6**2 + 4**2 + 6**2) / 4 - ((3 + 6 + 4 + 6) / 4) ** 2) ** 0.5,
            ((6**2 + 4**2 + 6**2 + 9**2) / 4 - ((6 + 4 + 6 + 9) / 4) ** 2) ** 0.5,
        ],
        dtype=np.float32,
    )
    pd.testing.assert_series_equal(expected_result, actual_result)


def test_calc_fraction() -> None:
    values = pd.Series([12345.67, 9876.54])

    actual = data.calc_fraction(values, unit=100)
    expected = pd.Series([45.67, 76.54], dtype=np.float32)
    pd.testing.assert_series_equal(expected, actual)

    actual = data.calc_fraction(values, unit=1000)
    expected = pd.Series([345.67, 876.54], dtype=np.float32)
    pd.testing.assert_series_equal(expected, actual)


def test_create_features() -> None:
    values = pd.DataFrame(
        {
            "open": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "high": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110],
            "low": [0, -10, -20, -30, -40, -50, -60, -70, -80, -90, -100, -110],
            "close": [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11],
        },
        index=pd.date_range("2023-01-01 00:00:00", "2023-01-01 00:11:00", freq="1min"),
    ).astype(np.float32)

    # center = False
    actual = data.create_features(
        values=values,
        base_timing="close",
        window_sizes=[3, 6],
        window_size_center=9,
        use_sma_frac=True,
        sma_frac_unit=100,
        use_hour=True,
        use_dow=True,
        center=False,
    )
    expected = pd.DataFrame(
        {
            "open": values["open"].shift(1),
            "high": values["high"].shift(1),
            "low": values["low"].shift(1),
            "close": values["close"].shift(1),
            "sma3": data.calc_sma(values["close"].shift(1), window_size=3),
            "moving_max3": data.calc_moving_max(
                values["close"].shift(1), window_size=3
            ),
            "moving_min3": data.calc_moving_min(
                values["close"].shift(1), window_size=3
            ),
            "sigma3": data.calc_sigma(values["close"].shift(1), window_size=3),
            "sma6": data.calc_sma(values["close"].shift(1), window_size=6),
            "moving_max6": data.calc_moving_max(
                values["close"].shift(1), window_size=6
            ),
            "moving_min6": data.calc_moving_min(
                values["close"].shift(1), window_size=6
            ),
            "sigma6": data.calc_sigma(values["close"].shift(1), window_size=6),
            "sma9_frac": data.calc_fraction(
                data.calc_sma(values["close"].shift(1), window_size=9), unit=100
            ),
            "hour": np.full(12, 0),
            "dow": np.full(12, date(2023, 1, 1).weekday()),
        }
    )
    pd.testing.assert_frame_equal(actual, expected)

    # center = True
    actual = data.create_features(
        values=values,
        base_timing="close",
        window_sizes=[3, 6],
        window_size_center=9,
        use_sma_frac=True,
        sma_frac_unit=100,
        use_hour=True,
        use_dow=True,
        center=True,
    )
    sma_center = data.calc_sma(values["close"].shift(1), window_size=9)
    for col in expected.columns:
        if col not in ("sigma3", "sigma6", "sma9_frac", "hour", "dow"):
            expected[col] -= sma_center

    pd.testing.assert_frame_equal(actual, expected)


def test_get_feature_stats() -> None:
    actual = data.get_feature_stats(
        pd.DataFrame(
            {
                "x": np.array([np.nan, 0.0, 1.0], dtype=np.float32),
                "y": np.array([0, 1, 1], dtype=np.int64),
            }
        )
    )
    assert set(actual.keys()) == {"x", "y"}
    assert isinstance(actual["x"], data.ContinuousFeatureStats)
    assert approx(actual["x"].mean) == 0.5
    assert approx(actual["x"].std) == 0.5
    assert isinstance(actual["y"], data.CategoricalFeatureStats)
    assert actual["y"].vocab_counts == {0: 1, 1: 2}


def test_calc_lift() -> None:
    value = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    pd.testing.assert_series_equal(
        data.calc_lift(value, alpha=0.1),
        pd.Series(
            [
                np.nan,
                (2 * 0.1 + 3 * 0.1 * 0.9 + 4 * 0.1 * 0.9**2 + 5 * 0.9**3) - 1,
                (3 * 0.1 + 4 * 0.1 * 0.9 + 5 * 0.9**2) - 2,
                (4 * 0.1 + 5 * 0.9**1) - 3,
                5 * 0.9**0 - 4,
            ],
            dtype=np.float32,
        ),
    )


def test_create_label() -> None:
    EPS = 0.01
    lift = pd.Series([-1 - EPS, -1 + EPS, 1 - EPS, 1 + EPS], dtype=np.float32)
    pd.testing.assert_series_equal(
        data.create_label(lift, bin_boundary=1),
        pd.Series([0, 1, 1, 2], dtype=np.int64),
    )


def test_calc_available_index() -> None:
    features = pd.DataFrame(
        {"x": [0] * 10, "y": [np.nan] * 2 + [10] * 8},
        index=pd.date_range("2023-1-1 00:00", "2023-1-1 00:09", freq="1min"),
    )
    actual = data.calc_available_index(
        features=features,
        hist_len=2,
    )
    expected = pd.date_range("2023-1-1 00:03", "2023-1-1 00:09", freq="1min")
    pd.testing.assert_index_equal(actual, expected)


def test_split_block_idxs() -> None:
    idxs_train, idxs_valid = data.split_block_idxs(
        size=10,
        block_size=2,
        valid_ratio=0.2,
    )
    assert len(idxs_train) == 8
    assert len(idxs_valid) == 2
    assert set(idxs_train) | set(idxs_valid) == set(range(10))
    assert abs(idxs_valid[0] - idxs_valid[1]) == 1
    assert (0 in idxs_train and 1 in idxs_train) or (
        0 in idxs_valid and 1 in idxs_valid
    )
    assert (2 in idxs_train and 3 in idxs_train) or (
        2 in idxs_valid and 3 in idxs_valid
    )
    assert (4 in idxs_train and 5 in idxs_train) or (
        4 in idxs_valid and 5 in idxs_valid
    )
    assert (6 in idxs_train and 7 in idxs_train) or (
        6 in idxs_valid and 7 in idxs_valid
    )
    assert (8 in idxs_train and 9 in idxs_train) or (
        8 in idxs_valid and 9 in idxs_valid
    )

    idxs_train, idxs_valid = data.split_block_idxs(
        size=7,
        block_size=3,
        valid_ratio=0.5,
    )
    assert set(idxs_train) | set(idxs_valid) == set(range(7))
    assert (0 in idxs_train and 1 in idxs_train and 2 in idxs_train) or (
        0 in idxs_valid and 1 in idxs_valid and 2 in idxs_valid
    )
    assert (3 in idxs_train and 4 in idxs_train and 5 in idxs_train) or (
        3 in idxs_valid and 4 in idxs_valid and 5 in idxs_valid
    )
    assert (6 in idxs_train) or (6 in idxs_valid)


def test_sequential_loader() -> None:
    available_index = pd.date_range("2023-1-1 00:02", "2023-1-1 00:05", freq="1min")
    features = pd.DataFrame(
        {
            "x": np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32),
            "y": np.array([0, 1, 2, 3, 4, 5], dtype=np.int64),
        },
        index=pd.date_range("2023-1-1 00:00", "2023-1-1 00:05", freq="1min"),
    )
    label = pd.Series(
        [0, 1, 2, 0, 1, 2],
        index=pd.date_range("2023-1-1 00:00", "2023-1-1 00:05", freq="1min"),
        dtype=np.int64,
    )

    loader = data.SequentialLoader(
        available_index=available_index,
        features=features,
        label=label,
        hist_len=3,
        batch_size=2,
    )

    expected_features_list = [
        {
            "x": np.array([[0.0, 0.1, 0.2], [0.1, 0.2, 0.3]]),
            "y": np.array([[0, 1, 2], [1, 2, 3]]),
        },
        {
            "x": np.array([[0.2, 0.3, 0.4], [0.3, 0.4, 0.5]]),
            "y": np.array([[2, 3, 4], [3, 4, 5]]),
        },
    ]
    expected_lift_list = [
        np.array([2, 0]),
        np.array([1, 2]),
    ]

    for batch_idx, (actual_features, actual_label) in enumerate(loader):
        for feature_name in ["x", "y"]:
            np.testing.assert_allclose(
                actual_features[feature_name],
                expected_features_list[batch_idx][feature_name],
            )
        np.testing.assert_allclose(actual_label, expected_lift_list[batch_idx])
