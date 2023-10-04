import requests

from .models import PostProxyModel


def check_active_proxy(proxy_model: PostProxyModel) -> tuple[int, str]:
    with requests.get(
        url="https://www.google.com/", proxies=proxy_model.get_url()
    ) as r:
        return r.status_code, r.text

#  scp -r /Users/racing/PycharmProjects/tgapi3/tgAPI2.0/src/main.py comments@85.234.107.149:/home/comments/projects/tgAPI2.0/src
