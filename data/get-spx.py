import time
import shutil

import redis
from flask import Flask

from td.client import TDClient

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)

# TDClient expects a writable credential file, so copy the client_secret to /code
shutil.copyfile("/run/secrets/client_secret", "/code/client_secret")

# Create a new session, credentials path is optional.
TDSession = TDClient(
    client_id=open('/run/secrets/client_id').readline().strip(),
    redirect_uri='https://127.0.0.1',
    credentials_path='/code/client_secret'
)

# Login to the session
TDSession.login()

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.route('/')
def hello():
    count = get_hit_count()

    # Option Chain Example
    opt_chain = {
        'symbol':'MSFT',
        'contractType':'CALL',
        'optionType':'S',
        'fromDate':'2020-04-01',
        'afterDate':'2020-05-01',
        'strikeCount':4,
        'includeQuotes':True,
        'range':'ITM',
        'strategy':'ANALYTICAL',
        'volatility': 29.0
    }

    # Get Option Chains
    option_chains = TDSession.get_options_chain(option_chain=opt_chain)

    return str(option_chains)


@app.route('/spx')
def spx():
    spx = yf.Ticker("SPX")
    chain = spy.option_chain("2020-07-09")
    return 'Hello spx! ' + str(chain)

