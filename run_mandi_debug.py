import sys
from pathlib import Path
from requests import Request, Session
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.mandi import get_mandi_prices


def fake_get(url, params=None, headers=None, timeout=None):
    req = Request('GET', url, params=params, headers=headers)
    prepared = Session().prepare_request(req)
    print("[fake_get] prepared url:", prepared.url)
    print("[fake_get] headers:", dict(prepared.headers))

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"records": []}

        @property
        def text(self):
            return "{}"

    return FakeResp()


def main():
    orig_get = requests.get
    requests.get = fake_get
    try:
        result = get_mandi_prices(state="Kerala", district="Kannur", commodity="Tomato", offset=0, limit=10)
        print("[main] result type:", type(result))
        print("[main] result:", result)
    finally:
        requests.get = orig_get


if __name__ == '__main__':
    main()
