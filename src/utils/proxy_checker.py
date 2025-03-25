import requests

from ..schemas.proxy import PostProxyModel


def check_active_proxy(proxy_model: PostProxyModel) -> tuple[int, str]:
    with requests.get(
        url="https://www.google.com/", proxies=proxy_model.get_url()
    ) as r:
        return r.status_code, r.text

