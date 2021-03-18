import json
import unittest

from FugleKLinePlotter import FugleKLinePlotter


class TestFugleKLinePlotter(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_res ="""{
    "apiVersion": "0.1.0",
    "data": {
        "info": {
            "countryCode": "TW",
            "date": "2021-01-19",
            "lastUpdatedAt": "2021-01-19T00:49:07.421Z",
            "mode": "twse-sem",
            "symbolId": "2330",
            "timeZone": "Asia/Taipei"
        },
        "quote": {
            "isCloseDelayed": false,
            "isClosed": false,
            "isHalting": false,
            "isOpenDelayed": false,
            "order": {
                "bestAsks": [
                    {
                        "price": 634,
                        "unit": 5,
                        "volume": 5000
                    },
                    {
                        "price": 635,
                        "unit": 74,
                        "volume": 74000
                    },
                    {
                        "price": 636,
                        "unit": 10,
                        "volume": 10000
                    },
                    {
                        "price": 637,
                        "unit": 38,
                        "volume": 38000
                    },
                    {
                        "price": 638,
                        "unit": 18,
                        "volume": 18000
                    }
                ],
                "bestBids": [
                    {
                        "price": 618,
                        "unit": 7,
                        "volume": 7000
                    },
                    {
                        "price": 620,
                        "unit": 3,
                        "volume": 3000
                    },
                    {
                        "price": 625,
                        "unit": 57,
                        "volume": 57000
                    },
                    {
                        "price": 630,
                        "unit": 40,
                        "volume": 40000
                    },
                    {
                        "price": 633,
                        "unit": 341,
                        "volume": 341000
                    }
                ],
                "at": "2021-01-19T00:49:07.421Z"
            },
            "priceOpen": {},
            "isCurbing": false,
            "isCurbingFall": false,
            "isCurbingRise": false,
            "isTrial": true,
            "total": {
                "at": "2021-01-19T00:49:07.421Z",
                "unit": 0
            },
            "trial": {
                "at": "2021-01-19T00:49:07.421Z",
                "price": 633,
                "unit": 3039,
                "volume": 3039000
            }
        }
    }
}"""

    def test_best_five_quote(self):
        stock_id = 3711
        file_name = 123
        fgk = FugleKLinePlotter(stock_id, file_name)

        res = fgk.get_best_five_quote()
        print(res)
