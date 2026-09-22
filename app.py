"""Influx Ventures - wholesale e-commerce store (Flask + SQLite)."""
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from PIL import Image, ImageOps
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("INFULX_DB", os.path.join(BASE_DIR, "data", "store.db"))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "gif"}


def load_secret_key():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = os.path.join(BASE_DIR, "data", ".secret_key")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app = Flask(__name__)
app.config.update(
    SECRET_KEY=load_secret_key(),
    MAX_CONTENT_LENGTH=25 * 1024 * 1024,  # 25 MB per request
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    icon TEXT DEFAULT '',
    sort INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    price INTEGER NOT NULL DEFAULT 0,
    old_price INTEGER,
    description TEXT DEFAULT '',
    in_stock INTEGER DEFAULT 1,
    featured INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    sort INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    location TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    mpesa_code TEXT DEFAULT '',
    total INTEGER NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'New',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    qty INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
"""

DEFAULT_SETTINGS = {
    "store_name": "Influx Ventures",
    "tagline": "Your Home. Our Passion.",
    "phone1": "0727 077 377",
    "phone2": "0740 447 389",
    "whatsapp": "254727077377",
    "paybill": "247247",
    "account": "404473",
    "email": "",
    "location": "Nairobi, Kenya",
    "delivery_note": "Countrywide delivery available. Wholesale prices for bulk orders.",
}

ORDER_STATUSES = ["New", "Paid", "Processing", "Delivered", "Cancelled"]


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    for k, v in DEFAULT_SETTINGS.items():
        db.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (k, v))
    if not db.execute("SELECT 1 FROM admins").fetchone():
        # First run: use ADMIN_PASSWORD if set, otherwise generate one and save it locally.
        password = os.environ.get("ADMIN_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(9)
            with open(os.path.join(os.path.dirname(DB_PATH), "admin_password.txt"), "w") as f:
                f.write(f"username: admin\npassword: {password}\n")
            print(f" * Admin account created - username: admin, password: {password}")
        db.execute("INSERT INTO admins(username, password_hash) VALUES (?, ?)",
                   ("admin", generate_password_hash(password)))
    db.commit()


def get_settings():
    if "settings" not in g:
        rows = get_db().execute("SELECT key, value FROM settings").fetchall()
        g.settings = {**DEFAULT_SETTINGS, **{r["key"]: r["value"] for r in rows}}
    return g.settings


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "item"


def unique_slug(table, name, exclude_id=None):
    base = slugify(name)
    slug, n = base, 2
    db = get_db()
    while True:
        row = db.execute(f"SELECT id FROM {table} WHERE slug = ?", (slug,)).fetchone()
        if not row or row["id"] == exclude_id:
            return slug
        slug, n = f"{base}-{n}", n + 1


def to_int(value, default=0):
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def save_image(file_storage):
    """Validate, resize and store an uploaded image as WebP. Returns filename or None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return None
    try:
        img = Image.open(file_storage.stream)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGBA") if img.mode in ("P", "LA", "RGBA") else img.convert("RGB")
        img.thumbnail((1200, 1200))
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        name = f"{uuid.uuid4().hex[:16]}.webp"
        img.save(os.path.join(UPLOAD_DIR, name), "WEBP", quality=85)
        return name
    except Exception:
        return None


def delete_image_file(filename):
    path = os.path.join(UPLOAD_DIR, os.path.basename(filename))
    if os.path.exists(path):
        os.remove(path)


def product_query(where="1=1", params=(), order="p.featured DESC, p.created_at DESC", limit=None):
    sql = f"""
        SELECT p.*, c.name AS category_name, c.slug AS category_slug,
               (SELECT filename FROM product_images i WHERE i.product_id = p.id
                ORDER BY sort, id LIMIT 1) AS image
        FROM products p LEFT JOIN categories c ON c.id = p.category_id
        WHERE {where} ORDER BY {order}"""
    if limit:
        sql += f" LIMIT {int(limit)}"
    return get_db().execute(sql, params).fetchall()


def get_categories(nonempty=False):
    """All categories with product counts; nonempty=True hides empty ones (for the storefront)."""
    rows = get_db().execute("""
        SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id) AS count,
               (SELECT i.filename FROM products p JOIN product_images i ON i.product_id = p.id
                WHERE p.category_id = c.id ORDER BY p.featured DESC, i.sort LIMIT 1) AS image
        FROM categories c ORDER BY c.sort, c.name""").fetchall()
    return [c for c in rows if c["count"]] if nonempty else rows


# --------------------------------------------------------------------------
# Template context / filters / CSRF
# --------------------------------------------------------------------------
@app.template_filter("ksh")
def ksh(value):
    return f"KSh {to_int(value):,}"


@app.template_filter("features")
def features(description, limit=3):
    """First few non-empty description lines, without bullet marks, for product cards."""
    lines = [ln.strip().lstrip("•-*·").strip() for ln in (description or "").splitlines()]
    return [ln for ln in lines if ln][:limit]


@app.template_filter("img")
def img_url(filename):
    if not filename:
        return url_for("static", filename="img/placeholder.svg")
    return url_for("static", filename=f"uploads/{filename}")


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
        if not token or token != session.get("_csrf"):
            abort(400, "Session expired. Please go back, refresh the page and try again.")


@app.context_processor
def inject_globals():
    s = get_settings()
    return {
        "S": s,
        "nav_categories": get_categories(nonempty=True),
        "csrf_token": csrf_token,
        "wa_link": lambda text="": f"https://wa.me/{s['whatsapp']}" + (f"?text={quote(text)}" if text else ""),
        "tel": lambda p: "+254" + re.sub(r"\D", "", p).lstrip("0")[-9:] if p else "",
        "year": datetime.now().year,
    }


# --------------------------------------------------------------------------
# Storefront
# --------------------------------------------------------------------------
@app.route("/")
def home():
    featured = product_query("p.featured = 1", limit=8)
    latest = product_query(order="p.created_at DESC, p.id DESC", limit=8)
    return render_template("index.html", featured=featured, latest=latest,
                           categories=get_categories(nonempty=True))


@app.route("/shop")
@app.route("/category/<slug>")
def shop(slug=None):
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "")
    where, params, category = ["1=1"], [], None
    if slug:
        category = get_db().execute("SELECT * FROM categories WHERE slug = ?", (slug,)).fetchone()
        if not category:
            abort(404)
        where.append("p.category_id = ?")
        params.append(category["id"])
    if q:
        where.append("(p.name LIKE ? OR p.description LIKE ? OR c.name LIKE ?)")
        params += [f"%{q}%"] * 3
    order = {"price_asc": "p.price ASC", "price_desc": "p.price DESC",
             "new": "p.created_at DESC, p.id DESC"}.get(sort, "p.featured DESC, p.id DESC")
    products = product_query(" AND ".join(where), params, order)
    return render_template("shop.html", products=products, category=category, q=q, sort=sort)


@app.route("/product/<slug>")
def product(slug):
    rows = product_query("p.slug = ?", (slug,))
    if not rows:
        abort(404)
    p = rows[0]
    images = get_db().execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY sort, id",
                              (p["id"],)).fetchall()
    related = product_query("p.category_id = ? AND p.id != ?", (p["category_id"], p["id"]), limit=4)
    return render_template("product.html", p=p, images=images, related=related)


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/api/products")
def api_products():
    ids = [to_int(i) for i in request.args.get("ids", "").split(",") if i.strip()]
    if not ids:
        return jsonify([])
    marks = ",".join("?" * len(ids))
    rows = product_query(f"p.id IN ({marks})", ids)
    return jsonify([{
        "id": r["id"], "name": r["name"], "price": r["price"], "in_stock": bool(r["in_stock"]),
        "image": img_url(r["image"]), "url": url_for("product", slug=r["slug"]),
    } for r in rows])


@app.route("/checkout", methods=["POST"])
def checkout():
    f = request.form
    name, phone = f.get("name", "").strip(), f.get("phone", "").strip()
    items = {}
    for key, val in f.items():
        if key.startswith("qty_"):
            pid, qty = to_int(key[4:]), max(0, min(to_int(val), 10000))
            if pid and qty:
                items[pid] = qty
    if not name or not phone or not items:
        flash("Please fill in your name, phone number and add items to your cart.", "error")
        return redirect(url_for("cart"))

    db = get_db()
    marks = ",".join("?" * len(items))
    products = db.execute(f"SELECT id, name, price FROM products WHERE id IN ({marks}) AND in_stock = 1",
                          list(items)).fetchall()
    if not products:
        flash("The items in your cart are no longer available.", "error")
        return redirect(url_for("cart"))
    total = sum(p["price"] * items[p["id"]] for p in products)
    code = "INF" + datetime.now().strftime("%y%m%d") + secrets.token_hex(2).upper()
    cur = db.execute(
        "INSERT INTO orders(code, customer_name, phone, location, notes, mpesa_code, total) VALUES (?,?,?,?,?,?,?)",
        (code, name[:100], phone[:30], f.get("location", "").strip()[:200], f.get("notes", "").strip()[:1000],
         f.get("mpesa_code", "").strip().upper()[:20], total))
    for p in products:
        db.execute("INSERT INTO order_items(order_id, product_id, name, price, qty) VALUES (?,?,?,?,?)",
                   (cur.lastrowid, p["id"], p["name"], p["price"], items[p["id"]]))
    db.commit()
    session.setdefault("my_orders", [])
    session["my_orders"] = (session["my_orders"] + [code])[-20:]
    return redirect(url_for("order_done", code=code))


@app.route("/order/<code>")
def order_done(code):
    if code not in session.get("my_orders", []) and not session.get("admin_id"):
        abort(404)
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE code = ?", (code,)).fetchone()
    if not order:
        abort(404)
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
    lines = [f"Hello {get_settings()['store_name']}, I have placed order *{order['code']}*:"]
    lines += [f"- {i['qty']} x {i['name']} @ {ksh(i['price'])}" for i in items]
    lines += [f"Total: *{ksh(order['total'])}*", f"Name: {order['customer_name']}",
              f"Phone: {order['phone']}", f"Delivery: {order['location'] or '-'}"]
    if order["mpesa_code"]:
        lines.append(f"M-Pesa code: {order['mpesa_code']}")
    return render_template("order_done.html", order=order, items=items, wa_text="\n".join(lines))


# --------------------------------------------------------------------------
# Admin
# --------------------------------------------------------------------------
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = get_db().execute("SELECT * FROM admins WHERE username = ?",
                                (request.form.get("username", "").strip(),)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session["admin_id"] = user["id"]
            session["admin_name"] = user["username"]
            session.permanent = True
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/admin") else url_for("admin_dashboard"))
        flash("Wrong username or password.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "new_orders": db.execute("SELECT COUNT(*) FROM orders WHERE status = 'New'").fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "sales": db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status IN ('Paid','Processing','Delivered')").fetchone()[0],
        "out_of_stock": db.execute("SELECT COUNT(*) FROM products WHERE in_stock = 0").fetchone()[0],
    }
    recent = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 8").fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


@app.route("/admin/products")
@admin_required
def admin_products():
    q = request.args.get("q", "").strip()
    cat = to_int(request.args.get("cat"))
    where, params = ["1=1"], []
    if q:
        where.append("p.name LIKE ?")
        params.append(f"%{q}%")
    if cat:
        where.append("p.category_id = ?")
        params.append(cat)
    products = product_query(" AND ".join(where), params, "p.id DESC")
    return render_template("admin/products.html", products=products, q=q, cat=cat)


@app.route("/admin/products/new", methods=["GET", "POST"])
@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_form(pid=None):
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone() if pid else None
    if pid and not p:
        abort(404)
    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        price = to_int(f.get("price"))
        if not name or price <= 0:
            flash("Product name and a price above 0 are required.", "error")
        else:
            old_price = to_int(f.get("old_price")) or None
            data = (name, to_int(f.get("category_id")) or None, price, old_price,
                    f.get("description", "").strip(), 1 if f.get("in_stock") else 0,
                    1 if f.get("featured") else 0)
            if p:
                db.execute("""UPDATE products SET name=?, category_id=?, price=?, old_price=?, description=?,
                              in_stock=?, featured=?, slug=? WHERE id=?""",
                           data + (unique_slug("products", name, pid), pid))
            else:
                cur = db.execute("""INSERT INTO products(name, category_id, price, old_price, description,
                                    in_stock, featured, slug) VALUES (?,?,?,?,?,?,?,?)""",
                                 data + (unique_slug("products", name),))
                pid = cur.lastrowid
            start = db.execute("SELECT COALESCE(MAX(sort), -1) + 1 FROM product_images WHERE product_id = ?",
                               (pid,)).fetchone()[0]
            bad = 0
            for n, file in enumerate(request.files.getlist("images")):
                if not file.filename:
                    continue
                fname = save_image(file)
                if fname:
                    db.execute("INSERT INTO product_images(product_id, filename, sort) VALUES (?,?,?)",
                               (pid, fname, start + n))
                else:
                    bad += 1
            db.commit()
            if bad:
                flash(f"{bad} file(s) were skipped - only JPG, PNG, WEBP or GIF images are allowed.", "error")
            flash("Product saved.", "success")
            if f.get("action") == "save_new":
                return redirect(url_for("admin_product_form"))
            return redirect(url_for("admin_product_form", pid=pid))
    images = db.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY sort, id",
                        (pid,)).fetchall() if pid else []
    return render_template("admin/product_form.html", p=p, images=images,
                           categories=get_categories(), form=request.form)


@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    db = get_db()
    for img in db.execute("SELECT filename FROM product_images WHERE product_id = ?", (pid,)).fetchall():
        delete_image_file(img["filename"])
    db.execute("DELETE FROM products WHERE id = ?", (pid,))
    db.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:pid>/toggle/<field>", methods=["POST"])
@admin_required
def admin_product_toggle(pid, field):
    if field not in ("in_stock", "featured"):
        abort(400)
    db = get_db()
    db.execute(f"UPDATE products SET {field} = 1 - {field} WHERE id = ?", (pid,))
    db.commit()
    return redirect(request.referrer or url_for("admin_products"))


@app.route("/admin/images/<int:iid>/delete", methods=["POST"])
@admin_required
def admin_image_delete(iid):
    db = get_db()
    img = db.execute("SELECT * FROM product_images WHERE id = ?", (iid,)).fetchone()
    if not img:
        abort(404)
    delete_image_file(img["filename"])
    db.execute("DELETE FROM product_images WHERE id = ?", (iid,))
    db.commit()
    flash("Image removed.", "success")
    return redirect(url_for("admin_product_form", pid=img["product_id"]))


@app.route("/admin/images/<int:iid>/main", methods=["POST"])
@admin_required
def admin_image_main(iid):
    db = get_db()
    img = db.execute("SELECT * FROM product_images WHERE id = ?", (iid,)).fetchone()
    if not img:
        abort(404)
    db.execute("UPDATE product_images SET sort = sort + 1 WHERE product_id = ?", (img["product_id"],))
    db.execute("UPDATE product_images SET sort = 0 WHERE id = ?", (iid,))
    db.commit()
    flash("Main image updated.", "success")
    return redirect(url_for("admin_product_form", pid=img["product_id"]))


@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    db = get_db()
    if request.method == "POST":
        f = request.form
        name = f.get("name", "").strip()
        cid = to_int(f.get("id"))
        if not name:
            flash("Category name is required.", "error")
        elif cid:
            db.execute("UPDATE categories SET name=?, icon=?, sort=?, slug=? WHERE id=?",
                       (name, f.get("icon", "").strip(), to_int(f.get("sort")),
                        unique_slug("categories", name, cid), cid))
            flash("Category updated.", "success")
        else:
            db.execute("INSERT INTO categories(name, icon, sort, slug) VALUES (?,?,?,?)",
                       (name, f.get("icon", "").strip(), to_int(f.get("sort")), unique_slug("categories", name)))
            flash("Category added.", "success")
        db.commit()
        return redirect(url_for("admin_categories"))
    return render_template("admin/categories.html", categories=get_categories())


@app.route("/admin/categories/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_category_delete(cid):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id = ?", (cid,))
    db.commit()
    flash("Category deleted. Its products are now uncategorised.", "success")
    return redirect(url_for("admin_categories"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    where, params = ["1=1"], []
    if status in ORDER_STATUSES:
        where.append("status = ?")
        params.append(status)
    if q:
        where.append("(code LIKE ? OR customer_name LIKE ? OR phone LIKE ? OR mpesa_code LIKE ?)")
        params += [f"%{q}%"] * 4
    orders = get_db().execute(f"SELECT * FROM orders WHERE {' AND '.join(where)} ORDER BY id DESC",
                              params).fetchall()
    return render_template("admin/orders.html", orders=orders, status=status, q=q, statuses=ORDER_STATUSES)


@app.route("/admin/orders/<int:oid>", methods=["GET", "POST"])
@admin_required
def admin_order(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
    if not order:
        abort(404)
    if request.method == "POST":
        status = request.form.get("status")
        if status in ORDER_STATUSES:
            db.execute("UPDATE orders SET status = ?, mpesa_code = ? WHERE id = ?",
                       (status, request.form.get("mpesa_code", "").strip().upper()[:20], oid))
            db.commit()
            flash("Order updated.", "success")
        return redirect(url_for("admin_order", oid=oid))
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (oid,)).fetchall()
    wa_phone = "254" + re.sub(r"\D", "", order["phone"]).lstrip("0")[-9:]
    return render_template("admin/order.html", order=order, items=items, statuses=ORDER_STATUSES,
                           wa_phone=wa_phone)


@app.route("/admin/orders/<int:oid>/delete", methods=["POST"])
@admin_required
def admin_order_delete(oid):
    db = get_db()
    db.execute("DELETE FROM orders WHERE id = ?", (oid,))
    db.commit()
    flash("Order deleted.", "success")
    return redirect(url_for("admin_orders"))


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    db = get_db()
    if request.method == "POST":
        f = request.form
        if f.get("form") == "password":
            user = db.execute("SELECT * FROM admins WHERE id = ?", (session["admin_id"],)).fetchone()
            if not check_password_hash(user["password_hash"], f.get("current", "")):
                flash("Current password is wrong.", "error")
            elif len(f.get("new", "")) < 6:
                flash("New password must be at least 6 characters.", "error")
            elif f.get("new") != f.get("confirm"):
                flash("New passwords do not match.", "error")
            else:
                db.execute("UPDATE admins SET password_hash = ? WHERE id = ?",
                           (generate_password_hash(f["new"]), user["id"]))
                db.commit()
                flash("Password changed.", "success")
        else:
            for key in DEFAULT_SETTINGS:
                if key in f:
                    val = f[key].strip()
                    if key == "whatsapp":
                        digits = re.sub(r"\D", "", val)
                        val = "254" + digits.lstrip("0")[-9:] if digits else ""
                    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, val))
            db.commit()
            flash("Store settings saved.", "success")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html")


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, message="Sorry, we couldn't find that page."), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message=e.description), 400


@app.errorhandler(413)
def too_large(_e):
    return render_template("error.html", code=413,
                           message="Those images are too large. Please upload under 25 MB at a time."), 413


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("DEBUG") == "1")
