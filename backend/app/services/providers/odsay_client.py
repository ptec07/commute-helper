from __future__ import annotations

import httpx


class ODsayClient:
    base_url = 'https://api.odsay.com/v1/api'

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get(self, endpoint: str, **params: str | int) -> dict:
        try:
            response = httpx.get(
                f'{self.base_url}/{endpoint}',
                params={'apiKey': self.api_key, **params},
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OSError(f'Failed to fetch ODsay endpoint: {endpoint}') from exc

        error = payload.get('error') or payload.get('errorMessage')
        if error:
            raise OSError(str(error))
        if 'result' not in payload:
            raise OSError(f'ODsay endpoint returned an invalid payload: {endpoint}')
        return payload