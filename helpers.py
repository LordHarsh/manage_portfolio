import os
import json
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    try:
        # Contact API
        api_key = os.environ.get("api_key")
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        url2 = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)
        d = response.json()
        quote = d['Global Quote']
        print(quote)
        #url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        #response = requests.get(url)
        #url = f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}'

        # Parse response
        #quote = response.json()
        # return {
        #     "name": quote["companyName"],
        #     "price": float(quote["latestPrice"]),
        #     "symbol": quote["symbol"]
        # }

        response2 = requests.get(url2)
        d2 = response2.json()
        print(d2)
        print("Lookup success")
        return {
            "name": d2["Name"] + " " + d2["Exchange"],
            "price": float(quote["05. price"]),
            "symbol": quote["01. symbol"]
        }
    except (KeyError, TypeError, ValueError):
        print ("Error in lookup")
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
