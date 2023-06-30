import os
from flask_redis import FlaskRedis
import psycopg2
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp

import secrets


from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)
# app.debug = False

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
secret_key = secrets.token_hex(16)
app = Flask(__name__)
app.config['SECRET_KEY'] = "dbkjnskjnkgnsk"

app.config['REDIS_URL'] = os.environ.get('KV_URL')
redis_store = FlaskRedis(app)
app.session_interface.redis = redis_store


# Database connection details
# Establish a connection to the PostgreSQL database
def connect_db():
    return psycopg2.connect(os.environ.get("POSTGRES_URL"))


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
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        hash TEXT NOT NULL,
        cash NUMERIC NOT NULL DEFAULT 10000.00
    )
""")
    cur.execute("CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, symbol TEXT NOT NULL, quantity INTEGER NOT NULL, amount NUMERIC NOT NULL, type TEXT NOT NULL, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
    cur.execute("CREATE TABLE IF NOT EXISTS stocks (id SERIAL PRIMARY KEY, symbol TEXT NOT NULL, user_id INTEGER NOT NULL, quantity INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
    user_id = session['user_id']
    cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
    user_name = cur.fetchone()[0]
    cur.execute("SELECT * FROM stocks WHERE user_id=%s", (user_id,))
    data = cur.fetchall()
    cur.execute("SELECT cash FROM users WHERE id=%s", (user_id,))
    cash = cur.fetchone()[0]
    conn.close()
    total = cash
    data2 = []
    print(data)
    for row in data:
        symbol = row[1]  # Assuming the "symbol" column is at index 1
        quantity = row[3]  # Assuming the "quantity" column is at index 3
        print(symbol)
        d = lookup(symbol)
        print(d)
        if not d:
            continue
        price = d.get('price')
        name = d.get('name')
        amount = price * quantity
        row = {
            'symbol': symbol,
            'name': name,
            'quantity': quantity,
            'price': usd(price),
            'amount': usd(amount)
        }
        data2.append(row)
    return render_template("index.html", name=user_name.title(), data=data2, cash=usd(cash), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if request.form.get('name') != None:
            return redirect('/buy?name='+request.form.get('name'))
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS stocks (id SERIAL PRIMARY KEY, symbol TEXT NOT NULL, user_id INTEGER NOT NULL, quantity INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
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
        print(symbol, quan, data)
        if not data:
            return apology("Re-enter Symbol", 400)
        if quan % 1 != 0 or quan <= 0:
            return apology("Re-enter Quantity", 400)
        amt = data.get('price') * quan
        cursor.execute("SELECT cash FROM users WHERE id=%s", (user_id,))
        current_cash = cursor.fetchone()[0]
        if amt > current_cash:
            return apology("Insufficient Cash", 400)
        cursor.execute(
            "SELECT * FROM stocks WHERE symbol=%s AND user_id=%s", (data['symbol'], user_id))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO stocks (symbol, user_id, quantity) values(%s, %s, %s)",
                           (data['symbol'], user_id, int(quan)))
        else:
            cursor.execute("UPDATE stocks SET quantity=quantity+%s WHERE symbol=%s AND user_id=%s",
                           (int(quan), data['symbol'], user_id))
        cursor.execute(
            "UPDATE users SET cash = cash-%s WHERE id=%s", (amt, user_id))
        cursor.execute("CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, symbol TEXT NOT NULL, quantity INTEGER NOT NULL, amount NUMERIC NOT NULL, type TEXT NOT NULL, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")

        cursor.execute("INSERT INTO history (user_id, symbol, quantity, amount, type) values(%s, %s, %s, %s, %s)",
                       (user_id, data['symbol'], quan, amt, 'buy'))
        conn.commit()
        conn.close()
        return redirect('/')
    elif request.method == "GET":
        name = str(request.args.get('name'))
        user_id = session['user_id']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT cash FROM users WHERE id=%s", (user_id,))
        current_cash = cursor.fetchone()[0]
        conn.close()
        return render_template("buy.html", name=name, cash=usd(current_cash))
    return apology("TODO", 400)


@app.route("/getprice", methods=["POST"])
@login_required
def get_price():
    """Get price of a share"""
    if request.method == "POST":
        sym = request.form.get("symbol")
        print(sym)
        data = lookup(sym)
        if not data:
            return "Wrong Symbol"
        return usd(data['price'])


@app.route("/getamount", methods=["POST"])
@login_required
def get_amount():
    """Get amount for a given price and quantity"""
    if request.method == "POST":
        price = request.form.get("price")
        price = price[1:]
        quan = request.form.get("quan")
        amt = float(price) * float(quan)
        return usd(amt)


@app.route("/getamountfromsymbol", methods=["POST"])
@login_required
def get_amount2():
    """Get amount for a given symbol and quantity"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quantity = request.form.get("quantity")
        price = lookup(symbol)['price']
        amt = float(price) * float(quantity)
        return usd(amt)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    if request.method == 'GET':
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, symbol TEXT NOT NULL, quantity INTEGER NOT NULL, amount NUMERIC NOT NULL, type TEXT NOT NULL, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
        cur.execute(
            "SELECT * FROM history WHERE user_id=%s ORDER BY id DESC", (session['user_id'],))
        data = cur.fetchall()
        cur.close()
        conn.close()
        data2 = []
        for row in data:
            data2.append({
                "id": row[0],
                "user_id": row[1],
                "symbol": row[2],
                "quantity": row[3],
                "amount": usd(row[4]),
                "type": row[5],
                "time": row[6]
            })
        return render_template('history.html', data=data2)
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
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s",
                    (request.form.get("username"),))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

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
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.0)")
        cur.execute("SELECT username FROM users WHERE username=%s", (username,))
        if len(cur.fetchall()) != 0:
            cur.close()
            conn.close()
            return apology("username exists", 400)

        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)

        password2 = request.form.get("confirmation")
        if not password2:
            return apology("must re-enter password", 400)
        if password != password2:
            return apology("passwords does not match :(", 400)

        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, hash) VALUES (%s, %s)",
                    (username, hashed_password))
        conn.commit()
        cur.close()
        conn.close()
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
        print(symbol, quantity)
        price = lookup(symbol).get('price')
        amt = float(price)*float(quantity)
        user_id = session['user_id']
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS history (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, symbol TEXT NOT NULL, quantity INTEGER NOT NULL, amount NUMERIC NOT NULL, type TEXT NOT NULL, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")

        cur.execute(
            "SELECT quantity FROM stocks WHERE symbol=%s AND user_id=%s", (symbol, user_id))
        current_quan = cur.fetchone()
        if not current_quan:
            cur.close()
            conn.close()
            return apology("Wrong Symbol Selected", 400)
        if current_quan[0] < quantity:
            cur.close()
            conn.close()
            return apology("Insufficient Stocks", 400)
        elif current_quan[0] == quantity:
            cur.execute(
                "DELETE FROM stocks WHERE symbol=%s AND user_id=%s", (symbol, user_id))
            cur.execute(
                "UPDATE users SET cash=cash+%s WHERE id=%s", (amt, user_id))
        else:
            cur.execute("UPDATE stocks SET quantity=quantity-%s WHERE symbol=%s AND user_id=%s",
                        (quantity, symbol, user_id))
            cur.execute(
                "UPDATE users SET cash=cash+%s WHERE id=%s", (amt, user_id))
        cur.execute("INSERT INTO history (user_id, symbol, quantity, amount, type) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, symbol, quantity, amt, 'sell'))
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/")
    elif request.method == 'GET':
        user_id = session['user_id']
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT cash FROM users WHERE id=%s", (user_id,))
        current_cash = cur.fetchone()[0]
        cur.execute(
            "SELECT symbol, quantity FROM stocks WHERE user_id=%s", (user_id,))
        current_stocks = cur.fetchall()
        print(current_stocks)
        current_stocks_list = []
        for i, row in enumerate(current_stocks):
            current_stocks_list.append({
                "symbol": current_stocks[i][0],
                "quantity": current_stocks[i][1]
            })

        print(current_stocks_list)
        cur.close()
        conn.close()
        return render_template("sell.html", cash=usd(current_cash), stocks=current_stocks_list)
    return apology("TODO")

# Rest of the code...


# Close the cursor and connection after the request
# @app.teardown_request
# def teardown_request(exception):
#     if cur:
#         cur.close()
#     if conn:
#         conn.close()


if __name__ == '__main__':
    app.run()
