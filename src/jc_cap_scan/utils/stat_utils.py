import pandas as pd
import numpy as np


def data_to_one_column(data: pd.DataFrame) -> pd.DataFrame:
    """
    Merge all data from a dataframe to one column. Useful for drawing for example histograms
    """
    data_one_column = []
    for col_name in data.columns:
        data_one_column.extend(data[col_name].to_list())
    data_one_column = pd.DataFrame(data_one_column)
    return data_one_column

def normalize_by_buckets(data: pd.DataFrame, buckets: list[tuple[int | float, int | float]]) -> pd.DataFrame:
    """
    Normalize data using min-max normalisation. The data are first split into bucket and each bucket for each row is
    standardized. Then the rows are merged back together.
    :param data: Dataframe to standardize
    :param buckets: List of starts and ends of the buckets
    :return: Resulting dataframe
    """
    data_by_bucket_and_changed_byte = {}
    for col in data.columns:
        for (start, end) in buckets:
            filtered_data = data[col][(data[col] >= start) & (data[col] < end)]
            data_by_bucket_and_changed_byte[f"{col}_{start}_{end}"] = filtered_data.reset_index(drop=True)
    data_by_bucket_and_changed_byte = pd.DataFrame.from_dict(data_by_bucket_and_changed_byte, orient='index')
    data_by_bucket_and_changed_byte = data_by_bucket_and_changed_byte.transpose()


    data_by_bucket = {}
    for (start, end) in buckets:
        columns = data_by_bucket_and_changed_byte.filter(regex=rf'_{start}_{end}')
        one_column = data_to_one_column(columns).dropna()
        data_by_bucket[f'{start}_{end}'] = one_column[0]

    data_by_bucket = pd.DataFrame.from_dict(data_by_bucket)

    normalized_data = {}
    for col in data.columns:
        normalized_column = []
        for (start, end) in buckets:
            if data_by_bucket_and_changed_byte.get(f'{col}_{start}_{end}', None) is not None:
                normalized_bucket = (data_by_bucket_and_changed_byte[f'{col}_{start}_{end}'] - data_by_bucket[f'{start}_{end}'].min()) / (data_by_bucket[f'{start}_{end}'].max() - data_by_bucket[f'{start}_{end}'].min())
                normalized_column.extend(normalized_bucket)
        normalized_data[col] = normalized_column

    data = pd.DataFrame.from_dict(normalized_data, orient='index')
    data = data.transpose()
    for col in data:
        data[col] = data[col].sort_values(ignore_index=True)
    data.dropna(inplace=True, how='all')

    return data

def limit_range(data: pd.DataFrame, minimum: int | float | None, maximum: int | float | None):
    """
    Drop data outside of the specified range
    :param data: Dataframe to process
    :param minimum: Bottom of the range
    :param maximum: Top of the range
    :return: Processed dataframe
    """
    total = len(data)
    if maximum is not None:
        over = np.count_nonzero(data >= maximum)
    else:
        over = 0

    if minimum is not None:
        under = np.count_nonzero(data <= minimum)
    else:
        under = 0

    print(f"Showing: {100 - ((over + under) / total) * 100}% of data")

    if maximum is not None:
        data = data[data < maximum]
    if minimum is not None:
        data = data[data > minimum]
    return data




