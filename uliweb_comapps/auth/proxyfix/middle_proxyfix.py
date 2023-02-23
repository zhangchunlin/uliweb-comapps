from uliweb import Middleware, settings

class ProxyFixMiddle(Middleware):

    def process_request(self, request):
        if 'HTTP_X_FORWARDED_FOR' in request.environ:
            # http://en.wikipedia.org/wiki/X-Forwarded-For
            # https://github.com/pallets/werkzeug/commit/cdf680222af293a2c118d8d52eecfd7b0c566e14#diff-39ebf61f0ca6a6d4a94144386d56b3f3
            client_addr = request.environ['HTTP_X_FORWARDED_FOR'].split(",")[-1 * settings.XFORWARDED.num_proxies].strip()
            if client_addr:
                request.environ['REMOTE_ADDR'] = client_addr
