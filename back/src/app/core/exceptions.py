class RustoreError(Exception):
    pass


class RustoreHTTPError(RustoreError):
    def __init__(self, status_code: int, url: str):
        self.status_code = status_code
        self.url = url
        super().__init__(f'HTTP {status_code} while fetching {url}')


class RustoreParseError(RustoreError):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f'Failed to parse apps from {url}')


class EmbeddingModelMissingError(Exception):
    pass


class OllamaError(Exception):
    pass


class OllamaHTTPError(OllamaError):
    def __init__(self, status_code: int, endpoint: str, body: str = ''):
        self.status_code = status_code
        self.endpoint = endpoint
        self.body = body
        super().__init__(f'Ollama HTTP {status_code} at {endpoint}: {body[:200]}')
