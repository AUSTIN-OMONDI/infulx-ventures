# The shop on Truehost (cPanel) — influxventures.co.ke

This is how the live site is set up. Cost: about **KSh 2,500/year** (Starter
plan), plus the domain.

Server: `das124.truehost.cloud`, cPanel user `dfhhhcvp`, home `/home/dfhhhcvp`.

## 1. Hosting and domain

Starter shared hosting with `influxventures.co.ke` as the **main domain**
(document root `/public_html`). DNS points the domain at the shared IP
`102.212.247.139`.

Starter is enough: it includes cPanel's **Setup Python App**.

## 2. Get the code onto the server

cPanel -> **Git Version Control** -> Create:

| Field | Value |
|---|---|
| Clone URL | `https://github.com/AUSTIN-OMONDI/infulx-ventures.git` |
| Repository path | `influx` |

That puts the code in `/home/dfhhhcvp/influx`.

## 3. Create the Python application

cPanel -> **Setup Python App** -> Create Application:

| Field | Value |
|---|---|
| Python version | 3.12 |
| Application root | `influx` |
| Application URL | `influxventures.co.ke` |
| Application startup file | `app.py` |
| Application Entry point | `app` |

**The startup file must be `app.py`, not `passenger_wsgi.py`.** cPanel writes its
own `passenger_wsgi.py` that loads whatever the startup file points at; pointing
it back at itself makes it import itself forever and every page dies with a
500 (`stderr.log` fills with a repeating traceback).

Add one **environment variable**:

| Name | Value |
|---|---|
| `SECRET_KEY` | a long random string (40+ characters) |

Leave `ADMIN_PASSWORD` unset and the site generates a password on first start
and writes it to `influx/data/admin_password.txt`. Set the variable instead if
you want to choose the password yourself; it is then re-applied on every start.

## 4. Install the libraries

On the Setup Python App page, under **Configuration files**, type
`requirements.txt` into the "Add another file and press enter" box and **press
Enter** (the Run Pip Install button stays greyed out until you do), then click
**Run Pip Install**.

## 5. Make LiteSpeed hand requests to the app

Truehost runs LiteSpeed, which ignores the Passenger block cPanel writes unless
Passenger is switched on explicitly. Without this the domain just lists the
files in `public_html`.

cPanel -> **File Manager** -> Settings -> tick *Show Hidden Files*, open
`/home/dfhhhcvp/public_html/.htaccess` with **Edit** and add at the end:

```apache
PassengerEnabled on
PassengerAppType wsgi
PassengerStartupFile passenger_wsgi.py
```

Also make sure `public_html` has **no `index.html`** — a leftover one (for
example from the host's parking page) is served instead of the shop. The old
OLITT page was renamed to `index.html.olitt-backup`.

## 6. Load the products

Setup Python App -> **Execute python script** -> `seed.py` -> **Run Script**.
It prints `Seeded 70 products.`

## 7. HTTPS

cPanel -> **SSL/TLS Status** -> tick the domain -> **Run AutoSSL**. Truehost
already had a Let's Encrypt wildcard in place, so `https://influxventures.co.ke`
and `https://www.influxventures.co.ke` both work.

## Updating the site later

1. cPanel -> **Setup Python App** -> *Execute python script* ->
   `deploy/cpanel_update.py` -> **Run Script** (pulls from GitHub).
2. Click **RESTART** on the same page.

`cpanel_update.py` discards local edits in the checkout first, because cPanel
rewrites `passenger_wsgi.py` whenever the app settings are saved and git will
not pull over it. The database and photos are untouched.

## Backups

The database and uploaded photos live in `~/influx/data` and
`~/influx/static/uploads`. In cPanel use **Backup -> Download a Home Directory
Backup** once a month, or copy those two folders.

## If something breaks

`~/influx/stderr.log` holds the Python traceback — open it in File Manager.
