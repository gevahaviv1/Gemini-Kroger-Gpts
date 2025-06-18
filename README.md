# Kroger Price Monitor & Cart Manager

A Flask-based application that monitors Kroger product prices and manages shopping carts through the Kroger API.

## Features

- **Price Monitoring**: Track regular and promotional prices for specific products
- **Price Alerts**: Get notifications when prices drop
- **Price History**: View historical price data for products
- **Cart Management**: Add, remove, and manage items in your Kroger cart

## Prerequisites

- Python 3.8+
- Kroger API credentials (Client ID and Client Secret)
- SQLite

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Gemini-Kroger-Gpts.git
   cd Gemini-Kroger-Gpts
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Kroger API credentials:
   ```env
   KROGER_CLIENT_ID=your_client_id
   KROGER_CLIENT_SECRET=your_client_secret
   ```

## Project Structure

- `kroger_app.models` - database models
- `kroger_app.routes` - API routes
- `kroger_app.services` - external service helpers
- `kroger_app.mappers` - data mapping utilities
- `kroger_app.utils` - general utilities

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Access the API endpoints:
   - `GET /products`: List all monitored products
   - `POST /product/watch`: Add/update a product to watch
   - `GET /product/<product_id>/history`: Get price history
   - `POST /cart/add`: Add item to cart
   - `DELETE /cart/remove`: Remove item from cart
   - `GET /cart`: View cart contents

## API Documentation

### Cart Endpoints

#### Add to Cart
```http
POST /cart/add
Content-Type: application/json

{
    "product_id": "0001111041700",
    "quantity": 1
}
```

#### Remove from Cart
```http
DELETE /cart/remove
Content-Type: application/json

{
    "product_id": "0001111041700"
}
```

#### View Cart
```http
GET /cart
```

## Database Schema

### Products Table
- id (String, Primary Key)
- name (String)
- brand (String)
- category (String)
- regular_price (Float)
- promo_price (Float)
- other product details...

### PriceHistory Table
- id (Integer, Primary Key)
- product_id (String, Foreign Key)
- timestamp (DateTime)
- regular_price (Float)
- promo_price (Float)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License.
