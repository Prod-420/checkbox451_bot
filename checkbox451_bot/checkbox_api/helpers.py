import os
from contextlib import asynccontextmanager
from logging import getLogger

import cachetools.func
import requests
from aiohttp import ClientResponse, ClientTimeout

import checkbox451_bot

log = getLogger(__name__)
dev_mode = bool(os.environ.get("DEV_MODE"))
api_url = "https://{}api.checkbox.in.ua/".format("dev-" if dev_mode else "")
api_url = os.environ.get("API_URL") or api_url
log.info(f"{ api_url=}")

print_width = os.environ.get("PRINT_WIDTH")
receipt_params = (
    {
        "width": int(print_width),
    }
    if print_width and print_width.isnumeric()
    else {}
)
log.info(f"{ receipt_params=}")


def endpoint(path: str):
    return os.path.join(api_url, "api/v1", path.lstrip("/"))


@cachetools.func.ttl_cache(ttl=86400)
def _auth():
    login = os.environ["LOGIN"]
    password = os.environ["PASSWORD"]

    url = endpoint("/cashier/signin")
    r = requests.post(url, json=dict(login=login, password=password))
    r.raise_for_status()
    data = r.json()

    return f"{data['token_type']} {data['access_token']}"


def headers(lic=False):
    _headers = {
        "X-Client-Name": "checkbox451",
        "X-Client-Version": checkbox451_bot.__version__,
        "Authorization": _auth(),
    }

    if lic:
        _headers["X-License-Key"] = os.environ["LICENSE_KEY"]

    return _headers


def get(session, path, **kwargs):
    url = endpoint(path)
    return session.get(url, headers=headers(), params=kwargs)


@asynccontextmanager
async def get_retry(session, path, **kwargs):
    url = endpoint(path)

    err = None
    for attempt in range(6):
        try:
            async with session.get(
                url,
                headers=headers(),
                params=kwargs,
                timeout=ClientTimeout(total=0.5 * 1.5 ** attempt),
            ) as response:
                yield response
        except Exception as e:
            err = e
            log.warning("retry attempt: %s", attempt + 1)
            continue
        else:
            return

    raise err


def post(session, path, lic=False, **kwargs):
    url = endpoint(path)
    return session.post(url, headers=headers(lic), json=kwargs)


async def raise_for_status(response: ClientResponse):
    if response.ok:
        return response

    try:
        result = await response.json()
        message = result["message"]
        detail = result["detail"]
        message = f"{message}: {detail}"
    except Exception:
        message = await response.text() or response.reason
        log.exception(message)
    else:
        log.error(message)

    response.raise_for_status()
