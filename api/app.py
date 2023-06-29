import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

# Configure application 
app = Flask(__name__)
app.debug = False

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    db.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, symbol TEXT NOT NULL, quantity INTEGER NOT NULL, amount NUMERIC NOT NULL, type TEXT NOT NULL, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
    db.execute("CREATE TABLE IF NOT EXISTS stocks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, symbol TEXT NOT NULL, user_id INTEGER NOT NULL, quantity INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
    user_id = session['user_id']
    name = db.execute("SELECT username FROM users WHERE id=?", user_id)[
        0]['username']
    data = db.execute("SELECT * FROM stocks WHERE user_id=?", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id=?", user_id)[0]['cash']
    total = cash
    for row in data:
        d = lookup(row['symbol'])
        total += d['price'] * row['quantity']
        row['name'] = d['name']
        row['price'] = usd(d['price'])
        row['amount'] = usd(d['price'] * row['quantity'])
    return render_template("index.html", name=name.title(), data=data, cash=usd(cash), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if request.form.get('name') != None:
            return redirect('/buy?name='+request.form.get('name'))
        db.execute("CREATE TABLE IF NOT EXISTS stocks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, symbol TEXT NOT NULL, user_id INTEGER NOT NULL, quantity INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
        user_id = session['user_id']
        symbol = request.form.get('symbol')
        quan = request.form.get("shares")
        if not quan:
            return apology("Re-enter Quantity", 400)
        try:
            quan = float(quan)
        except:
            return apology("Re-enter Quantity", 400)
        data = lookup(symbol)
        if not data:
            return apology("Re-enter Symbol", 400)
        if quan % 1 != 0 or quan <= 0:
            return apology("Re-enter Quantity", 400)
        amt = data['price'] * quan
        current_cash = db.execute(
            "SELECT cash FROM users WHERE id=?", user_id)[0]['cash']
        if amt > current_cash:
            return apology("Insufficient Cash", 400)
        if not db.execute("SELECT * FROM stocks where symbol=? AND user_id=?", data['symbol'], user_id):
            db.execute("INSERT INTO stocks (symbol, user_id, quantity) values(?, ?, ?)",
                       data['symbol'], user_id, int(quan))
        else:
            db.execute("UPDATE stocks SET quantity=quantity+? WHERE symbol=? AND user_id=?",
                       int(quan), data['symbol'], user_id)
        db.execute("UPDATE users SET cash = cash-? WHERE id=?", amt, user_id)
        db.execute("INSERT INTO history (user_id, symbol, quantity, amount, type) values(?, ?, ?, ?, ?)",
                   user_id, data['symbol'], quan, amt, 'buy')
        return redirect('/')
    elif request.method == "GET":
        name = str(request.args.get('name'))
        user_id = session['user_id']
        current_cash = db.execute(
            "SELECT cash FROM users WHERE id=?", user_id)[0]['cash']
        return render_template("buy.html", name=name, cash=usd(current_cash))
    return apology("TODO", 400)


@app.route("/getprice", methods=["POST"])
@login_required
def get_price():
    """Get price a a share"""
    if request.method == "POST":
        sym = request.form.get("symbol")
        data = lookup(sym)
        if not data:
            return "Wrong Symbol"
        return usd(data['price'])


@app.route("/getamount", methods=["POST"])
@login_required
def get_amount():
    """Get price a a share"""
    if request.method == "POST":
        price = request.form.get("price")
        price = price[1:]
        quan = request.form.get("quan")
        amt = float(price)*float(quan)
        return usd(amt)


@app.route("/getamountfromsymbol", methods=["POST"])
@login_required
def get_amount2():
    """Get price a a share"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quantity = request.form.get("quantity")
        price = dict(lookup(symbol)).get('price')
        amt = float(price)*float(quantity)
        return usd(amt)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    if request.method == 'GET':
        data = db.execute(
            "SELECT * FROM history WHERE user_id=? ORDER BY id DESC", session['user_id'])
        for row in data:
            row['amount'] = usd(row['amount'])
        return render_template('history.html', data=data)
    return apology("Only Get")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        sym = request.form.get("symbol")
        data = lookup(sym)
        if not data:
            return apology("Wrong Symbol", 400)
        data['price'] = usd(data['price'])
        return render_template("quote.html", data=data)
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":

        username = request.form.get("username")
        if not username:
            return apology("must provide username", 400)
        if len(db.execute("SELECT username FROM users where username=?", (username))) != 0:
            return apology("username exists", 400)

        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)

        password2 = request.form.get("confirmation")
        if not password2:
            return apology("must re-enter password", 400)
        if password != password2:
            return apology("passwords does not match :(", 400)
        db.execute("INSERT INTO users (username, hash) values(?, ?)",
                   username, generate_password_hash(password))
        return redirect("/")
    return apology("ONLY GET OR POST")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == 'POST':
        symbol = request.form.get("symbol")
        quantity = request.form.get("shares")
        if not quantity:
            return apology("Quantity Required")
        quantity = int(quantity)
        price = dict(lookup(symbol)).get('price')
        amt = float(price)*float(quantity)
        user_id = session['user_id']
        current_quan = db.execute(
            "SELECT quantity FROM stocks WHERE symbol=? AND user_id=?", symbol, user_id)
        if not current_quan:
            return apology("Wrong Symbol Selected", 400)
        if current_quan[0]['quantity'] < quantity:
            return apology("Insufficient Stocks", 400)
        elif current_quan[0]['quantity'] == quantity:
            db.execute(
                "DELETE FROM stocks WHERE symbol=? AND user_id=?", symbol, user_id)
            db.execute("UPDATE users SET cash=cash+? WHERE id=?", amt, user_id)
        else:
            db.execute(
                "UPDATE stocks SET quantity=quantity-? WHERE symbol=? AND user_id=?", quantity, symbol, user_id)
            db.execute("UPDATE users SET cash=cash+? WHERE id=?", amt, user_id)
        db.execute("INSERT INTO history (user_id, symbol, quantity, amount, type) values(?, ?, ?, ?, ?)",
                   user_id, symbol, quantity, amt, 'sell')
        return redirect("/")
    elif request.method == 'GET':
        user_id = session['user_id']
        current_cash = db.execute(
            "SELECT cash FROM users WHERE id=?", user_id)[0]['cash']
        current_stocks = db.execute(
            "SELECT symbol, quantity FROM stocks WHERE user_id=?", user_id)
        return render_template("sell.html", cash=usd(current_cash), stocks=current_stocks)
    return apology("TODO")
