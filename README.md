# Stock Portfolio Management Application

This is a Flask-based web application for managing stock portfolios. Users can register an account, buy and sell stocks, view their portfolio, and see transaction history.

## Technologies Used

- Python
- Flask
- PostgreSQL [vercel-deploy/production]
- Redis [vercel-deploy/production]
- HTML/CSS
- JavaScript
- SQLite [master/development]

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/manage_portfolio.git
```


2. Change into the project directory and deployment branch:
```bash
cd manage_portfolio
git checkout vercel-deploy
```


3. Install the required Python packages:
```bash
pip install -r requirements.txt
```


4. Set up the database:

- Install PostgreSQL and create a new database.
- Set the `POSTGRES_URL` environment variable to the connection URL of the PostgreSQL database.

5. Set up Redis:

- Install Redis and start the Redis server.
- Set the `KV_URL` environment variable to the connection URL of the Redis server.

6. Set the application secret key:

- Generate a secure secret key and set it as the `SECRET` environment variable.

7. Run the application:
```bash
flask run
```
8. Open your web browser and visit [http://localhost:5000](http://localhost:5000) to access the application.

###### Note:
An easier setup can be done by master branch for local preview using sqlite3:
``` bash
git clone https://github.com/your-username/manage_portfolio.git
cd manage_portfolio
pip install -r requirements.txt
flask run
```
___
## Usage

1. Register a new account or log in with your existing credentials.

2. Use the navigation menu to perform various actions:
- **Portfolio**: View your current stock holdings and cash balance.
- **Buy**: Purchase stocks by specifying the symbol and quantity.
- **Sell**: Sell stocks from your portfolio by selecting the symbol and quantity.
- **Quote**: Get a stock quote by entering the symbol.
- **History**: View a history of your transactions.

____
## Features
#### User Registration and Login
Users can register an account by providing a username and password. The passwords are securely hashed using the werkzeug.security library. Registered users can log in using their credentials.

#### Buying Stocks
Logged-in users can buy stocks by entering the stock symbol and the quantity they want to purchase. The application retrieves the current price of the stock using the helpers.lookup function and checks the user's available cash balance. If the user has sufficient funds, the purchase is made, and the stock is added to the user's portfolio.

#### Selling Stocks
Users can sell stocks from their portfolio by selecting the stock symbol and entering the quantity to sell. The application checks the user's available quantity of the selected stock and deducts it from their portfolio. The corresponding amount is added to the user's cash balance.

#### Portfolio and Transaction History
Users can view their stock portfolio, which includes the stocks they own along with their current quantity, price, and total value. They can also check their transaction history, which shows all the buy and sell transactions they have made, including the stock symbol, quantity, amount, and transaction type.

#### Stock Quotes
Users can get a stock quote by entering the stock symbol. The application fetches the current price and displays it to the user.

----
## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
