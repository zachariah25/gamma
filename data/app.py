import time
import shutil

import redis
from flask import Flask

from td.client import TDClient

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)

# TDClient expects a writable credential file, so copy the client_secret to /code
try:
    shutil.copyfile("/run/secrets/client_secret", "/code/client_secret")
except FileNotFoundError:
    print("Error copying client secret (expected when running locally)")

def getClientSecretPath():
    try:
        open('/run/secrets/client_secret')
        return '/run/secrets/client_secret'
    except FileNotFoundError:
        return '../client_secret.json'


def getClientId():
    try:
        return open('/run/secrets/client_id').readline().strip()
    except FileNotFoundError as e:
        return open('../client_id.txt').readline().strip()


# Create a new session, credentials path is optional.
TDSession = TDClient(
    client_id=getClientId(),
    redirect_uri='https://127.0.0.1',
    credentials_path=getClientSecretPath(),
    auth_flow='flask'
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
    return "Hello! Hit count: " + str(count)


@app.route('/symbol/<symbol>')
def getOptionsChain(symbol):
    symbol = symbol.upper()
    opt_chain = build_opt_chain(symbol)
    
    chain = TDSession.get_options_chain(opt_chain)
    if chain is None:
        TDSession.login()
        chain = TDSession.get_options_chain(opt_chain)

    gamma = None
    try:
        gamma = calculate_gamma(chain)
    except Exception as e:
        print(e)

    return "gamma: " + '{:20,.2f}'.format(gamma) #+ " chain data: " + str(chain)

def calculate_gamma(chain):
    # careful! gamma is always positive
    printed = str(chain)
    print(printed[:1000])

    mark = chain["underlying"]["mark"]

    gamma = 0.0
    for expiry, callsAtExpiry in chain["callExpDateMap"].items():
        #print("expiry: " + str(expiry))
        #print("callsAtExpiry: " + str(callsAtExpiry))
        for strike_price, calls in callsAtExpiry.items():
            #print("strke price: " + str(strike_price))
            #print("calls: " + str(calls))
            for call in calls:
                gamma += call["gamma"] * call["openInterest"] * call["multiplier"]

    for expiry, putsAtExpiry in chain["putExpDateMap"].items():
        for strike_price, puts in putsAtExpiry.items():
            for put in puts:
                gamma -= put["gamma"] * put["openInterest"] * put["multiplier"]

    print("gamma without close:", gamma)
    print("close:", mark)
    return gamma * (mark ** 2) * .01

def build_opt_chain(symbol):
    return {
        'symbol': symbol,
        'contractType': 'ALL',
        #'optionType':'S', # S = standard ? default is ALL
        'fromDate':'2020-07-12', # TODO: today!
        'toDate':'2020-10-12',
        #'strikeCount':4,
        'includeQuotes':True,
        #'range':'ALL',
        #'strategy':'ANALYTICAL',
        #'volatility': 29.0
    }