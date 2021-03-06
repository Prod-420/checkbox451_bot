import asyncio
from json.decoder import JSONDecodeError

import aiohttp
from aiohttp import ClientResponseError

from checkbox451_bot.checkbox_api.exceptions import (
    CheckboxReceiptError,
    CheckboxShiftError,
)
from checkbox451_bot.checkbox_api.helpers import (
    get,
    log,
    post,
    raise_for_status,
)


async def current_shift(session):
    async with get(session, "/cashier/shift") as response:
        await raise_for_status(response)
        result = await response.json()

    return result


async def open_shift(session):
    async with post(session, "/shifts", lic=True) as response:
        try:
            await raise_for_status(response)
        except ClientResponseError:
            raise CheckboxShiftError("Не вдалось відкрити зміну")
        shift = await response.json()

    shift_id = shift["id"]

    for _ in range(10):
        async with get(session, "/cashier/shift") as response:
            try:
                shift = await response.json()
            except JSONDecodeError:
                pass
            else:
                if shift["status"] == "OPENED":
                    log.info("shift: %s", shift_id)
                    return shift_id

        await asyncio.sleep(1)

    log.error("shift error: %s", shift)
    raise CheckboxShiftError("Не вдалось підписати зміну")


async def service_out(session):
    shift = await current_shift(session)

    if not shift:
        raise CheckboxShiftError("Зміна закрита")

    balance = shift["balance"]["balance"]
    payment = {
        "type": "CASH",
        "value": -balance,
        "label": "Готівка",
    }

    async with post(session, "/receipts/service", payment=payment) as response:
        try:
            await raise_for_status(response)
        except ClientResponseError:
            raise CheckboxReceiptError("Не вдалось здійснити службову видачу")

        receipt = await response.json()

    receipt_id = receipt["id"]
    log.info("service out: %s", receipt_id)

    for _ in range(10):
        async with get(session, f"/receipts/{receipt_id}") as response:
            try:
                receipt = await response.json()
            except JSONDecodeError:
                pass
            else:
                if receipt["status"] == "DONE":
                    return receipt_id

        await asyncio.sleep(1)

    log.error("service out signing error: %s", receipt)
    raise CheckboxReceiptError("Не вдалось підписати службову видачу")


async def shift_balance():
    async with aiohttp.ClientSession() as session:
        shift = await current_shift(session)

    if shift:
        return shift["balance"]["balance"] / 100


async def shift_close():
    async with aiohttp.ClientSession() as session:
        await service_out(session)

        async with post(session, "/shifts/close") as response:
            await raise_for_status(response)
            shift = await response.json()

        shift_id = shift["id"]
        balance = shift["balance"]["service_out"] / 100

        for _ in range(10):
            async with get(session, "/cashier/shift") as response:
                try:
                    shift = await response.json()
                except JSONDecodeError:
                    pass
                else:
                    if shift is None:
                        log.info("shift closed: %s", shift_id)
                        return balance

            await asyncio.sleep(1)

    log.error("shift close error: %s", shift)
    raise CheckboxShiftError("Не вдалось підписати закриття зміни")
