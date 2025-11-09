import httpx

class AlpacaClient:
    def __init__(self, key: str, secret: str, base_url: str):
        self.key = key
        self.secret = secret
        self.base_url = base_url.rstrip("/")

    def _headers(self):
        return {
            "APCA-API-KEY-ID": self.key,
            "APCA-API-SECRET-KEY": self.secret,
            "Accept": "application/json"
        }

    async def get_account(self):
        url = f"{self.base_url}/v2/account"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def get_positions(self):
        url = f"{self.base_url}/v2/positions"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self._headers())
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json()

    async def market_order(self, symbol: str, side: str, qty: float):
        url = f"{self.base_url}/v2/orders"
        payload = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": "day"
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()