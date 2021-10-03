from itertools import chain
from collections import defaultdict
from itertools import zip_longest


def _update_key_counter(idx, key, same, opposite):
    """
    Deletes intersection elements.

    Inplace modifications.

    Parameters
    ----------
    idx : int
    key : tuple
        key belong to `same`.  same : dict
        is the set from `row` comes from.
    opposite : dict
        is the set where `row` doesn't belong to.
    """
    # - Si key está en opposite hay que reducir uno para eliminar el elemento.
    # - Si key no está en opposite entonces hay que aumentar same porque es
    #   una diferencia.
    if key is None:
        # early stop
        return key

    if opposite.get(key):
        opposite[key].pop(0)  # FIFO
    else:
        same[key].append(idx)

    return key


def dict2dataframe(dict_idx, df):
    # convierte el diccionario de frecuencias en un dataframe.
    idx_list = sorted(chain.from_iterable(dict_idx.values()))
    if not idx_list:
        # early stop
        return df.iloc[0:0]  # empty

    max_idx = max(idx_list)

    if max_idx > (len(df) - 1):
        max_idx_pos = idx_list.index(max_idx)
        idx_list = idx_list[:max_idx_pos]

    out = df.iloc[idx_list]
    return out


def distinct(left, right, subset=None):
    # for the sake of efficiency
    right_dict = defaultdict(list)
    left_dict = defaultdict(list)

    if subset is not None:
        left_gen = left[subset].itertuples(index=False, name="left")
        right_gen = right[subset].itertuples(index=False, name="right")
        fillvalue = None
    else:
        left_gen = left.itertuples(index=False, name="left")
        right_gen = right.itertuples(index=False, name="right")
        fillvalue = None

    union_gen = zip_longest(left_gen, right_gen, fillvalue=fillvalue)

    for i, (left_row, right_row) in enumerate(union_gen):

        # si ambas row son iguales, se anulan y no se hace nada.
        if left_row == right_row:
            continue

        # SI SON DISTINTAS:
        # - si ya se ha visto se reduce el numero del conjunto opuesto
        # - si no se ha visto se aumenta el propio
        _update_key_counter(i, right_row, right_dict, left_dict)
        _update_key_counter(i, left_row, left_dict, right_dict)

    out_left = dict2dataframe(left_dict, left)
    out_right = dict2dataframe(right_dict, right)

    return out_left, out_right


import pandas as pd


def distinct_groupby(left, right, subset=None):

    # add label of set source
    left = left.copy()
    right = right.copy()

    left["source"] = "A"
    right["source"] = "B"

    _all = pd.concat([left, right], axis=0)
    _all["n"] = 1
    freq_table = _all.pivot_table(
            columns=["source"],
            index=subset,
            aggfunc="count"
    )
    a_subs_b = freq_table["n"].fillna(0).eval("A - B").to_frame("AsubsB")

    a_distinct = a_subs_b.query("AsubsB>0")
    out_a = []
    for i, n in a_distinct.itertuples():
        out_a.extend([i]*int(n))
    a_distinct_df = pd.DataFrame(out_a)

    b_distinct = (-a_subs_b).query("AsubsB>0")
    out_b = []
    for i, n in b_distinct.itertuples():
        out_b.extend([i]*int(n))
    b_distinct_df = pd.DataFrame(out_b)

    return a_distinct_df, b_distinct_df

