# proxy

Randomized proxy setting for requests.get  

## Installation
```
pip install git+https://github.com/khlee42/proxy.git#egg=proxy
```

## Usage
```
config = {
        'SOCKS5': {'user': ..., 'password': ..., 'port': ...},
        'PROXY': {'proxy1': ..., },
        'HEADER': {'header1': {...}, }
}
url = {
        'url' : 'https://gitcoin.co/api/v0.1/bounties/',
        'params' : {'pk': 1234}
}

# Set up proxy servers from config
proxy = Proxy(config)

# Pick a server from the list
proxy.shuffle()

# Get response
r = proxy.get(url)

# export to json
r.to_json()

# export to pickle 
r.to_pkl() 
```