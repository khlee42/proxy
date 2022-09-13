import requests
from requests.exceptions import HTTPError, ConnectionError

import pickle, logging, json
import random, itertools, datetime
from pathlib import Path

def now():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

def get_path(file):
    path = Path(file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path

class Proxy:
    """
    Proxy class object contains proxy configurations for HTML requests.
    config dictionary must contains:
        'SOCKS5': access credential
        'PROXY': dict of proxy name and url
        'HEADER': dict of headers

    Usage:
    >>> config = {
            'SOCKS5': {'user': ..., 'password': ..., 'port': ...},
            'PROXY': {'proxy1': ..., },
            'HEADER': {'header1': {...}, }
        }
    >>> proxy = Proxy(config)
    >>> url = {
            'url' : 'https://gitcoin.co/api/v0.1/bounties/',
            'params' : {'pk': 1234}
        }
    >>> proxy.shuffle()
    >>> r = proxy.get(url)

    >>> r.to_json() # export to json
    >>> r.to_pkl() # export to pickle
    """
    
    ERR_PATH = get_path(f'var/tmp/err_{now()}.log')
    
    def __init__(self, config, logpath: str=ERR_PATH):
        self.socks5 = config['SOCKS5']
        self.proxies = config['PROXY']
        self.headers = config['HEADER']
        self.config = self._product()
        self.shuffle()
        logging.basicConfig(filename=logpath, filemode='w', format='%(levelname)s - %(message)s')
    
    @property
    def socks5(self):
        return self._socks5
    
    @socks5.setter
    def socks5(self, value):
        def test(d, key):
            try: 
                a = d[key]
                return True
            except KeyError:
                raise KeyError(f'{key} is missing in socks5 config.')        
        keys = ['user', 'password', 'port']
        for key in keys:
            test(value, key)

        self._socks5 = value
    
    def __str__(self):
        return f'{len(self.config)} configurations of proxies and headers.'

    def _product(self):
        return list(itertools.product(self.proxies, self.headers))
    
    def shuffle(self):
        """shuffle config list and make it iterable (config_iter)"""
        random.shuffle(self.config)
        self.config_iter = iter(self.config)
    
    @staticmethod
    def _gen_proxy_string(user, password, port, host):
        socks5_string = f'socks5://{user}:{password}@{host}:{port}'
        proxies = {
            'http': socks5_string,
            'https': socks5_string
        }
        return proxies
    
    @property
    def next(self):
        host_key, headers_key = next(self.config_iter)
        config_id = f'{host_key}, {headers_key}'
        return config_id, {
            'proxies': self._gen_proxy_string(**self.socks5, **{'host': self.proxies[host_key]}), 
            'headers': self.headers[headers_key]
        }
        
    def print_sample(self):
        # take argument for n; decorator?
        for i, j in enumerate(self.config_iter):
            if i>len(self.config)-6:
                item = f'#{i}\n{j}'
                print(item)

    def get(self, url):
        """
        request with rotated proxies and headers. it'll try all configurations of Proxy object
         until giving up. return Results object.
        """
        try:
            config_id, config = self.next
            response = requests.get(**url, **config)
            response.raise_for_status()
            return Results(url=url, config=config_id, response=response)

        except (HTTPError, ConnectionError) as err:
            message = f'{err}. Proxy server ({config_id}) failed. Try again with another server.'
            logging.warning(message)
            return self.get(url)

        except StopIteration:
            message = f'All proxy servers failed.'
            logging.warning(message)
            return Results(url=url, config=None, response=None)


class Results():
    """Results from Proxy.get(). Similar to Response to requests package."""

    def __init__(self, response, url=None, config=None):
        self.url = url
        self.config = config
        self.time = now()
        self.response = response
    
    def __str__(self) -> str:
        return f'Response of request to {self.url} with {self.config} server.'
    
    def to_json(self, file='data/data.json'):
        # JSON can't store Response object; they must be serializable.
        results = {
            'url': self.url,
            'config': self.config,
            'time': self.time,
            'status_code': self.response.status_code,
            'json': self.response.json()
        }
        with get_path(file).open('r+') as f:
            try:
                file_data = json.load(f)
            except json.decoder.JSONDecodeError: # empty file
                file_data = []
            file_data.append(results)
            f.seek(0)
            json.dump(file_data, f, indent=4)
    
    def to_pkl(self, file='data.pkl'):
        # Pickle on the other hand can store Response object as a whole.
        with get_path(file).open('r+b') as f:
            try:
                file_data = pickle.load(f)
            except EOFError: # empty file
                file_data = []
            file_data.append(self)
            f.seek(0)
            pickle.dump(file_data, f)