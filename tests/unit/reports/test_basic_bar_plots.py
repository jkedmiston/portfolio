from views.reports_bp import basic_bar_plots_for_categorical_features, basic_grouping_plots
import pandas as pd
import numpy as np


def test_basic_grouping_plots():
    fake_data = pd.DataFrame.from_dict({'cat1': ['Really-long-species-name', 'Dog', 'Dog', 'Cat', 'Cat', 'Dog', 'Horse', np.nan],
                                        'weight': [10, np.nan, 45, 10, 11, 40, 100, np.nan]})
    info, dgs = basic_grouping_plots(fake_data, "123", "abc", "sh1")
    expected = pd.DataFrame({'cat1': ["Dog"] * 3,
                             'weight': [np.nan, 45, 40],
                             'index': [1, 2, 5]}).set_index('index')
    expected.index.name = None
    actual = dgs[("cat1", "Dog")]
    pd.testing.assert_frame_equal(actual, expected)

    expected = pd.DataFrame({'cat1': ["Really-long-species-name"] * 1,
                             'weight': [10.0],
                             'index': [0]}).set_index('index')
    expected.index.name = None
    actual = dgs[("cat1", "Really-long-species-name")]
    pd.testing.assert_frame_equal(actual, expected)


def test_basic_bar_plots():
    fake_data = pd.DataFrame.from_dict({'cat1': ['Really-long-species-name', 'Dog', 'Dog', 'Cat', 'Cat', 'Dog', 'Horse', np.nan],
                                        'weight': [10, np.nan, 45, 10, 11, 40, 100, np.nan]})
    info = basic_bar_plots_for_categorical_features(
        fake_data, "123", "abc", "sh1")


if __name__ == "__main__":
    gkeys = globals().copy()
    for key in gkeys.keys():
        if key[0:5] == "test_":
            gkeys[key]()
