from http import HTTPStatus
import typing as T

STATUS_PHRASES = { s.value: s.phrase for s in HTTPStatus }
__all__ = ['HTTPResponse', 'HTTPLocation', 'HTTPMethodNotAllowed']


class HTTPResponse(Exception):
    def __init__(self, status: int, response=None, headers=None):
        if response is None:
            response = "%d %s" % (status, STATUS_PHRASES[status])
        if headers is None:
            headers = dict()
        if isinstance(response, str):
            headers['content-type'] = 'text/plain; charset=utf-8'
        self.rv = (response, status, headers)

    @property
    def response(self):
        """
        Returns:
            flask.Response: a response
        """
        from flask import make_response
        return make_response(*self.rv)


class HTTPLocation(HTTPResponse):
    def __init__(self, status: int, url: str):
        url = str(url)
        super().__init__(
            status, url, {
                'location': url
            }
        )


class HTTPMethodNotAllowed(HTTPResponse):
    def __init__(self, allowed_methods: T.Iterable[str]):
        super().__init__(
            405, headers={
                'allow': ', '.join(allowed_methods)
            }
        )
