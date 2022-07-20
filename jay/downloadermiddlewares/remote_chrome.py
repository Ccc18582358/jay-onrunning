import json
from urllib import parse

from scrapy.http.headers import Headers

from jay.downloadermiddlewares import AbstractDownloaderMiddleware


class RemoteChromeMiddleware(AbstractDownloaderMiddleware):

    def __init__(self, settings):
        AbstractDownloaderMiddleware.__init__(self, settings)
        self.remote_chrome_interface_proxy = self.settings.get('REMOTE_CHROME_INTERFACE_PROXY',
                                                               'http://127.0.0.1:3000/chrome')
        self.remote_chrome_read_timeout = self.settings.getfloat('REMOTE_CHROME_READ_TIMEOUT', '300')
        self.priority_adjust = self.settings.getint('RETRY_PRIORITY_ADJUST', -1)
        self.target_close_time = 5000

    def process_request(self, request, spider):
        flags = request.flags
        if 'only_bucket' in flags:
            callback = str(request.callback)
            if 'parse_scu' in callback:
                return
        if self.remote_chrome_interface_proxy in request.url:
            return

        if request.meta.get('target_close_time'):
            self.target_close_time = request.meta.get('target_close_time')

        body = {
            'url': request.url,
            'method': request.method,
            'response_fields': ['html'],
            'timeout': 120000,
            'target_close_time': self.target_close_time
        }
        data = parse.urlencode(body)
        if request.method == 'POST':
            body['body'] = request.body.decode('utf-8')

        headers = Headers({'Content-Type': 'application/json',
                           'referer': request.url
                           })
        new_request = request.replace(
            url=self.remote_chrome_interface_proxy + "?" + data,
            method='GET',
            body=json.dumps(body, ensure_ascii=False, sort_keys=True, indent=4),
            headers=headers,
            # priority=request.priority + self.priority_adjust
        )

        new_request.meta['priority'] = (request.meta['jay']['priority'] + self.priority_adjust) * -1
        return new_request

    def process_response(self, request, response, spider):
        self.logger.debug(f"get {response.url} from remote chrome")
        flags = request.flags
        if 'only_bucket' in flags:
            callback = str(request.callback)
            if 'parse_scu' in callback:
                return response
        request_body = json.loads(request.body.decode())
        fixed_response = response.replace(url=request_body['url'])
        return fixed_response
