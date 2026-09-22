# Influx Ventures – Online Store

Wholesale e-commerce site for Influx Ventures (woofers, TVs, dinner sets, cookware, cookers, fridges).
Built with **Python Flask + SQLite**, so there is no separate database server to set up. It works on phones and computers.

## Features

**Customers**
- Home page with categories, Hot Deals and New Arrivals
- Search, category filter and sort by price
- Product page with a photo gallery, description and discount badge
- Cart (saved in the browser) and a simple checkout: name, phone, location and an optional M-Pesa code
- Order confirmation with Paybill details and a one-tap **"Send order on WhatsApp"** button
- Floating **WhatsApp** button and floating **Paybill 247247** button (opens how-to-pay steps with copy buttons)
- Tap-to-call phone numbers: 0727 077 377 and 0740 447 389

**Admin** (`/admin`)
- Dashboard with new orders, sales and quick actions
- Add and edit products: upload several photos (drag and drop or tap), set the main photo, price, old price (shows a discount), description, in-stock and Hot Deal switches
- One-click in-stock and Hot Deal toggles from the product list
- Orders: filter by status, see details, call or WhatsApp the customer, set the status and M-Pesa code
- Categories: add, rename, reorder and delete
- Settings: phone numbers, WhatsApp number, Paybill and account number, store name, and admin password

Uploaded photos are automatically resized and converted to WebP so pages load fast on mobile data.

## Run locally

```bash
pip install -r requirements.txt
python seed.py        # first time only – loads the product catalogue
python app.py         # open http://localhost:5000  (admin: http://localhost:5000/admin)
```

**Admin login:** the username is `ADMIN_USERNAME` (default `admin`). If the `ADMIN_PASSWORD` environment variable is set (as on Render), that is
the password; it is applied every time the site starts, so change it there. Without it, a random password is
generated on first run, printed in the console and saved to `data/admin_password.txt`.

## Deploying

The site runs on any host that supports Python, such as PythonAnywhere, a VPS or Render. For example:

```bash
# Linux server
gunicorn -w 3 -b 0.0.0.0:8000 app:app
# Windows server
waitress-serve --port=8000 app:app
```

- Put the site behind HTTPS (for example with Nginx and Let's Encrypt).
- Back up the `data/` folder (the database) and `static/uploads/` (product photos).
- Optional environment variables: `SECRET_KEY`, `INFULX_DB` (database path) and `PORT`.

## Product catalogue

`python seed.py` loads the products Influx Ventures shared on WhatsApp (photos in `seed_images/`).
`python seed.py --reset` deletes every product and loads that list again.
Categories with no products are hidden on the website automatically; add products to them from the admin panel.
