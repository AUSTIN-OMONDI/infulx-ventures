# Putting the shop on an Oracle Cloud Always Free server

Cost: **KSh 0 per month, permanently** (plus the domain, about KSh 1,200/year).
Allow about an hour the first time.

## 1. Create the Oracle account

1. Go to **oracle.com/cloud/free** and click *Start for free*.
2. Country **Kenya**, then your real name, email and phone.
3. Add a **Visa or Mastercard debit card** for identity checking. Oracle holds about
   US$1 and releases it; there is no subscription. Prepaid and virtual cards are
   usually rejected — use a normal bank debit card.
4. Choose a **home region close to Kenya**: *Germany Central (Frankfurt)*,
   *UK South (London)* or *India West (Mumbai)*. This cannot be changed later.

## 2. Create the server

1. In the console: **Menu → Compute → Instances → Create instance**.
2. Name: `influx`.
3. Image: **Canonical Ubuntu 24.04**.
4. Shape: **Always Free eligible**
   - `VM.Standard.A1.Flex` (ARM, 1-4 CPUs, 6-24 GB) is best — if it says *out of capacity*,
     try again later or choose `VM.Standard.E2.1.Micro` (AMD), which is almost always free.
5. Networking: leave the defaults and tick **Assign a public IPv4 address**.
6. **Add SSH keys → Generate a key pair for me** and *download the private key*. Keep that file.
7. Click **Create** and note the **Public IP address**.

## 3. Open the web ports

1. On the instance page click the **Subnet** link, then the **Default Security List**.
2. **Add Ingress Rules** → Source `0.0.0.0/0`, IP protocol TCP, destination port **80**.
3. Repeat for port **443**.

## 4. Point the domain at the server

At your domain registrar (Truehost, Namecheap, etc.) create:

| Type | Name | Value |
|---|---|---|
| A | @ | your server's public IP |
| A | www | your server's public IP |

Wait until `ping yourdomain.co.ke` answers with that IP (usually minutes, up to a few hours).

## 5. Install the shop

Connect to the server (replace the key path, IP and domain):

```bash
ssh -i C:\path\to\private-key.key ubuntu@YOUR_SERVER_IP
```

Then on the server:

```bash
sudo apt-get update -y && sudo apt-get install -y git
git clone https://github.com/AUSTIN-OMONDI/infulx-ventures.git influx
bash influx/deploy/setup.sh yourdomain.co.ke you@email.com
```

That installs Python, the shop, gunicorn, nginx and a free HTTPS certificate.

## 6. Set the admin password

```bash
sudo systemctl edit influx
```

Add these three lines, save (Ctrl+O, Enter, Ctrl+X):

```
[Service]
Environment=ADMIN_PASSWORD=choose-a-strong-password
Environment=SECRET_KEY=paste-a-long-random-string
```

Then `sudo systemctl restart influx`.

## Everyday tasks

| Task | Command |
|---|---|
| Update the site after I push changes | `cd ~/influx && git pull && sudo systemctl restart influx` |
| See the logs | `sudo journalctl -u influx -n 50` |
| Restart the shop | `sudo systemctl restart influx` |
| Back up products and orders | `cp -r ~/influx/infulx/data ~/backup-$(date +%F)` |

The database and uploaded photos live in `~/influx/infulx/data` and
`~/influx/infulx/static/uploads`. **Copy those two folders somewhere safe every month.**
