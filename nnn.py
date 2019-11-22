import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Remember user id
    user_id = session["user_id"]

    # Get balance from database
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id)

    bal = cash[0]['cash']

    stocks = db.execute("SELECT symbol, name, SUM(shares) as shares FROM transactions WHERE"
                        + " user_id = :user_id GROUP BY symbol", user_id=user_id)

    # Initialize total value
    grand_total = bal

    for i in range(len(stocks)):
        current = lookup(stocks[i]['symbol'])
        price = current['price']
        total = price * stocks[i]['shares']
        grand_total += total
        stocks[i]['price'] = usd(price)
        stocks[i]['total'] = usd(total)

    return render_template("index.html", stocks=stocks, grand_total=usd(grand_total), bal=usd(bal))


def is_int(n):
    """Determine if an input can be converted to integer"""
    try:
        # Convert to integer
        int(n)
        return True
    # Handle error
    except ValueError:
        return False


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # Check if user wants to submit a form
    if request.method == "POST":
        # Remember symbol
        symbol = request.form.get("symbol")

        # Check if symbol field is empty
        if not symbol:
            return apology("symbol is required", 400)

        # Remember shares
        shares = request.form.get("shares")

        if not is_int(shares) or not int(shares) or int(shares) < 1:
            return apology("Shares is required and must be a positive integer", 400)

        shares = int(shares)

        if not shares:
            return apology("Shares is required", 400)

        # Call a function to retrieve stock info
        stock = lookup(symbol)

        # Check if stock was retrieved successfully
        if not stock:
            return apology("the requested stock was not found", 400)

        cost = float(stock['price']) * shares

        name = stock['name']

        symbol = stock['symbol']

        # Get id of the user
        user_id = session["user_id"]

        balance = db.execute("SELECT cash FROM users WHERE id = :user_id AND cash > :cost",
                             user_id=user_id, cost=cost)

        # Return error if user does not have sufficient funds
        if not balance:
            return apology("You do not have enough funds to complete the transaction", 400)

        # Get balance
        bal = balance[0]["cash"] - cost

        # Add transaction to database
        db.execute("INSERT INTO transactions (user_id, symbol, name, shares, cost) VALUES" +
                   "(:user_id, :symbol, :name, :shares, :cost)", user_id=user_id,
                   symbol=symbol, name=name, shares=shares, cost=cost)

        # Update cash in database with balance
        db.execute("UPDATE users SET cash = :bal WHERE id = :user_id", bal=bal, user_id=user_id)

        # Redirect user to home page
        return redirect("/")

    return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username")
    if len(username) > 0:
        is_user = db.execute("SELECT username FROM users WHERE username = :username",
                             username=username)
        if len(is_user) == 0:
            return jsonify(True)

    return jsonify(False)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    stocks = db.execute("SELECT symbol, name, shares, transacted_at FROM transactions"
                        + " WHERE user_id = :user_id", user_id=session["user_id"])

    return render_template("history.html", stocks=stocks)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
    # Check if user wants to submit a form
    if request.method == "POST":
        # Remember symbol
        symbol = request.form.get("symbol")

        # Check if symbol field is empty
        if not symbol:
            return apology("symbol is required", 400)

        # Call a function to retrieve stock info
        stock = lookup(symbol)

        # Check if stock was retrieved successfully
        if not stock:
            return apology("the requested stock was not found", 400)

        name = stock["name"]

        price = stock["price"]

        # Render a new page displaying stock
        return render_template("quoted.html", name=name, price=usd(price))

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Remove any previous user from session
    session.clear()

    # Check if user wants to submit a form
    if request.method == "POST":
        # Remember username
        username = request.form.get("username")
        # Remember password
        password = request.form.get("password")
        # Remember confirmation
        confirmation = request.form.get("confirmation")
        print(username, password)

        if not username:
            return apology("username is required", 400)

        if not password:
            return apology("password is required", 400)

        if not confirmation:
            return apology("please confirm your password", 400)

        if password != confirmation:
            return apology("mismatched password", 400)

        hashpass = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        if len(rows):
            return apology("username is already in use", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashpass)",
                   username=username, hashpass=hashpass)

        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Remember user id
    user_id = session["user_id"]

    stocks = db.execute("SELECT symbol, SUM(shares) as shares FROM transactions WHERE"
                        + " user_id = :user_id GROUP BY symbol", user_id=user_id)

    symbols = []
    for i in range(len(stocks)):
        symbols.append(stocks[i]["symbol"])

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not symbol:
            return apology("Symbol is required", 400)

        if symbol not in symbols:
            return apology("You do not have the requested stock", 404)

        if not shares:
            return apology("Shares is required", 400)

        for i in range(len(stocks)):
            if symbol == stocks[i]["symbol"]:
                myshares = stocks[i]["shares"]

        if shares > myshares:
            return apology("You don't have that many shares to sell", 400)

        stock = lookup(symbol)

        price = stock["price"] * shares

        name = stock["name"]

        db.execute("INSERT INTO transactions (user_id, symbol, name, shares, cost) VALUES"
                   + " (:user_id, :symbol, :name, :shares, :price)", user_id=user_id,
                   symbol=symbol, name=name, shares=-shares, price=price)

        db.execute("UPDATE users SET cash = cash + :price WHERE id = :user_id",
                   price=price, user_id=user_id)

        return redirect("/")

    else:
        return render_template("sell.html", symbols=symbols)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
