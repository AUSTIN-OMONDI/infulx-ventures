# Putting the shop on Truehost (cPanel) — influxventures.co.ke

Cost: about **KSh 2,500/year** for the Starter plan (domain already bought).
Allow about 45 minutes.

## 0. Before you pay — one question for Truehost

Open their live chat and ask:

> "Does the Starter shared hosting plan include **Setup Python App** in cPanel,
> and which Python versions are available? I need to run a Flask application."

- **If yes** — buy the Starter plan and carry on below.
- **If no** — ask for the cheapest plan that does, or try HostPinnacle or Sasahost.
  A PHP-only plan cannot run this site.

## 1. Buy hosting and attach the domain

1. truehost.co.ke → Hosting → **Starter**, billed yearly.
2. At checkout choose **Use a domain I already own** → `influxventures.co.ke`.
3. Pay by M-Pesa. You'll receive cPanel login details by email.
4. If the domain is registered with Truehost, DNS is wired automatically. If it
   isn't, set the nameservers from the welcome email on the domain.

## 2. Upload the shop

In cPanel, open **Terminal** (under Advanced). If Terminal is missing, see
"No Terminal?" below.

```bash
cd ~
git clone https://github.com/AUSTIN-OMONDI/infulx-ventures.git influx
```

## 3. Create the Python application

cPanel → **Setup Python App** → **Create Application**:

| Field | Value |
|---|---|
| Python version | 3.11 or 3.12 (the newest offered) |
| Application root | `influx` |
| Application URL | `influxventures.co.ke` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

Add two **environment variables** on the same screen:

| Name | Value |
|---|---|
| `ADMIN_PASSWORD` | a strong password for the admin area |
| `SECRET_KEY` | a long random string (40+ characters) |

Click **Create**.

## 4. Install the libraries

On the Setup Python App page, copy the command shown at the top
(`source /home/USER/virtualenv/influx/3.11/bin/activate && cd ~/influx`),
paste it into **Terminal**, then run:

```bash
pip install -r infulx/requirements.txt
python infulx/seed.py          # first time only: loads the products
```

Back on the Setup Python App page, click **Restart**.

## 5. Check it

Open **https://influxventures.co.ke** — the shop should appear.
Admin: **https://influxventures.co.ke/admin** with username `admin` and the
password you set in step 3.

If cPanel shows "It works! Python" instead of the shop, the startup file or entry
point is wrong — recheck the table in step 3 and click Restart.

## 6. Turn on HTTPS

cPanel → **SSL/TLS Status** → tick the domain → **Run AutoSSL**. Free and
automatic; wait a few minutes, then confirm the padlock shows in the browser.

## No Terminal?

Some shared plans hide Terminal. Then:

1. Download the code as a ZIP from GitHub (Code → Download ZIP).
2. cPanel → **File Manager** → upload the ZIP to your home folder → **Extract**.
3. Rename the extracted folder to `influx`.
4. Do step 3 as above; for step 4 use cPanel's Setup Python App page, which has a
   **"Run pip install"** box — enter `infulx/requirements.txt`.
5. Seeding without Terminal: visit the site once; it creates the database
   automatically but with no products, so add them in the admin, or ask me for a
   one-off seeding page.

## Updating later

```bash
cd ~/influx && git pull
```

Then **Restart** on the Setup Python App page.

## Backups

The database and uploaded photos live in `~/influx/infulx/data` and
`~/influx/infulx/static/uploads`. In cPanel use **Backup → Download a Home
Directory Backup** once a month, or copy those two folders.
