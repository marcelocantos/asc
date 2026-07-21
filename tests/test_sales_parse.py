# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

from asc.sales import FIRST_TIME, _parse_tsv, filter_rows, sum_units


SAMPLE = """\
Provider\tProvider Country\tSKU\tDeveloper\tTitle\tVersion\tProduct Type Identifier\tUnits\tDeveloper Proceeds\tBegin Date\tEnd Date\tCustomer Currency\tCountry Code\tCurrency of Proceeds\tApple Identifier\tCustomer Price\tPromo Code\tParent Identifier\tSubscription\tPeriod\tCategory\tCMB\tDevice\tSupported Platforms\tProceeds Reason\tPreserved Pricing\tClient\tOrder Type
APPLE\tUS\t201002090\tSquz\tMultiMaze\t3.1.0\t1F\t2\t0\t07/19/2026\t07/19/2026\tUSD\tUS\tUSD\t355300331\t0\t\t\t\t\tGames\t\tiPhone\tiOS\t\t\t\t
APPLE\tUS\t201002090\tSquz\tMultiMaze\t3.1.0\t7F\t5\t0\t07/19/2026\t07/19/2026\tUSD\tUS\tUSD\t355300331\t0\t\t\t\t\tGames\t\tiPhone\tiOS\t\t\t\t
APPLE\tUS\t999\tSquz\tOther\t1.0\t1F\t1\t0\t07/19/2026\t07/19/2026\tUSD\tFR\tUSD\t1\t0\t\t\t\t\tGames\t\tiPhone\tiOS\t\t\t\t
"""


def test_parse_and_filter_downloads():
    rows = _parse_tsv(SAMPLE, "2026-07-19")
    assert len(rows) == 3
    mm = filter_rows(rows, sku="201002090", kinds=frozenset({"download"}))
    assert sum_units(mm) == 2
    assert mm[0].kind == "download"
    assert mm[0].product_type in FIRST_TIME

    updates = filter_rows(rows, sku="201002090", kinds=frozenset({"update"}))
    assert sum_units(updates) == 5
