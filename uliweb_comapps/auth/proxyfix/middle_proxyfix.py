from uliweb import settings


class ProxyFixMiddle:
    """
    ASGI 中间件：处理 X-Forwarded-For 头部，将代理IP转换为客户端真实IP

    参考 Werkzeug ProxyFix 中间件实现：
    - http://en.wikipedia.org/wiki/X-Forwarded-For
    - https://github.com/pallets/werkzeug/commit/cdf680222af293a2c118d8d52eecfd7b0c566e14
    """

    def __init__(self, app):
        self.app = app
        # 获取配置，默认为1
        self.num_proxies = settings.get_var('XFORWARDED/num_proxies', 1, default=1)

    async def __call__(self, scope, receive, send):
        """
        ASGI 中间件的异步调用方法

        :param scope: ASGI 请求作用域
        :param receive: 接收消息的回调
        :param send: 发送消息的回调
        """
        # 从 scope 中获取 headers（ASGI 使用 lowercase header names）
        headers = dict(scope.get('headers', []))

        # 检查是否有 X-Forwarded-For 头
        if b'x-forwarded-for' in headers:
            forwarded_for = headers[b'x-forwarded-for'].decode('utf-8')
            # 取最后一个代理IP（根据 num_proxies 配置）
            client_addr = forwarded_for.split(",")[-1 * self.num_proxies].strip()

            if client_addr:
                # 更新 scope 中的 client 信息
                # scope['client'] 是 (host, port) 元组
                client = scope.get('client')
                if client:
                    scope['client'] = (client_addr, client[1])

        # 调用下一个中间件或应用
        await self.app(scope, receive, send)
