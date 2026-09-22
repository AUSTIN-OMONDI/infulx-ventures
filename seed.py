"""Load the product catalogue (run: python seed.py, or python seed.py --reset to replace all products).

Products and photos come from the offers Felix (Influx Ventures) sent on WhatsApp.
"""
import os
import shutil
import sys
import uuid

from app import UPLOAD_DIR, app, delete_image_file, get_db, unique_slug

HERE = os.path.dirname(os.path.abspath(__file__))

# (key, name, emoji) - categories without products are hidden on the website
CATEGORIES = [
    ("washing", "Washing Machines", "🧺"),
    ("hair", "Hair Care & Salon", "💇"),
    ("fryer", "Deep Fryers", "🍟"),
    ("heater", "Room Heaters", "🔥"),
    ("storage", "Kitchen Storage", "🗄️"),
    ("woofer", "Woofers & Sound", "🔊"),
    ("tv", "TVs", "📺"),
    ("dinner", "Dinner Sets", "🍽️"),
    ("cookware", "Cookware", "🍲"),
    ("cooker", "Cookers", "🔥"),
    ("fridge", "Fridges", "🧊"),
]

# (category key, image file or None, name, price, featured, description)
PRODUCTS = [
    ("washing", "p03", "TCL 10KG Wash & Dry Front Load Washing Machine (C510WDG)", 59000, 1,
     "• 10KG wash capacity, 7KG dry capacity\n• Fully automatic front load\n• Smart DD inverter motor, 1400 RPM spin\n"
     "• Wi-Fi connectivity\n• JetBubble technology, Auto Dose\n• Steam Care, Allergy Care, Air Wash & Air Refresh\n"
     "• 15 & 30-minute quick wash\n• Drum clean, add garment, auto weight detection\n• Delay start, child lock, LED digital display"),
    ("washing", "p04", "TCL 10KG Wash & Spin Front Load Washing Machine (C510FLG)", 52000, 0,
     "• 10KG capacity, wash & spin\n• Front load, Smart DD inverter motor\n• 1400 RPM spin speed\n• Wi-Fi connectivity\n"
     "• 540mm Super Drum\n• Steam / heat sterilization, Allergy Care\n• Auto weight detection, drum clean, add garment\n"
     "• Spray wash, Air Refresh\n• 24-hour delay start, child lock, LED digital display"),

    ("hair", "p05", "Hot Comb Electric Press Comb", 600, 0,
     "• Gold ceramic plate designed for professional hair styling\n• Variable heat settings for different hair types\n"
     "• Comes with a stand and a black handle with LED temperature indicators"),
    ("hair", "p06", "Cronier Professional Hair Straightener (CR-974)", 1200, 0,
     "• Ceramic coated plates\n• 4-level temperature display, up to 200°C"),
    ("hair", "p07", "Sayona 2000W Professional Hair Dryer", 4000, 0,
     "• For salon and home use\n• Powerful 2000W motor for fast drying\n• 2 speed levels and 3 heat settings\n"
     "• Soft-grip handle with hanging loop"),
    ("hair", "p08", "Nunix HD-01C 2200W Blow Dryer with Accessories", 1000, 0,
     "• 2200W blow dryer\n• Comes with accessories"),
    ("hair", "p09", "Nunix HD-77C 2400W Blow Dryer + Free Manicure Set", 1500, 1,
     "• Professional 2400W blow dryer\n• Comes with accessories\n• FREE manicure set"),
    ("hair", "p10", "Gek 3800 Professional Blow Dryer", 1500, 0, "• Professional blow dryer by Gek / Zeriotti"),
    ("hair", "p11", "Gek 3000 Professional Blow Dryer", 1400, 0, "• Professional blow dryer by Gek / Zeriotti"),
    ("hair", "p12", "ElectroMate 2200W Hair Dryer", 700, 1, "🔥 Offer\n• Quality 2200W blow dryer"),
    ("hair", "p13", "Equator Salon Standing Hair Dryer", 11500, 1,
     "• Professional salon-style standing dryer with a durable, long-life motor\n• 60-minute timer\n"
     "• Adjustable temperature from 30°C to 85°C\n• High heating performance, for salons and home use"),
    ("hair", "p14", "Wall-Mounted Salon Hood Dryer", 18000, 0,
     "• Wall-mounted to save space\n• Adjustable arm\n• Red hood with clear visor\n• Control knobs for speed and heat"),

    ("fryer", "p15", "Macro DF6S Double Deep Fryer 12L", 5500, 0, "• Double tank, 12 litres total (6L + 6L)\n• Stainless steel"),
    ("fryer", "p17", "Nunix MF-01 Electric Single Deep Fryer 6L", 3000, 0, "• 6 litres\n• Stainless steel\n• 1 year warranty"),
    ("fryer", "p19", "Nunix DF-6D Electric Double Deep Fryer 12L", 6500, 1,
     "🔥 Price down\n• Stainless steel, two 6-litre tanks (12L total)\n• About 5000W combined power\n"
     "• Independent thermostat per tank, 60°C to 200°C\n• Heat-resistant basket handles\n• For commercial or home use"),

    ("heater", "p24", "ElectroMate 2000W 5-Sided Quartz Room Heater (QH02)", 2000, 1,
     "🔥 Offer\n• 2000W high-power heating\n• 5-sided design for wide-angle heat\n• Caster wheels and top handle\n"
     "• Multiple heat settings via front toggle switches\n• Safety feature\n• 1 year warranty"),
    ("heater", "p20", "ElectroMate Portable Quartz Room Heater 800W (QH-01)", 1200, 0,
     "• 800W with two heat settings (400W / 800W)\n• Dual quartz tubes for instant warmth\n"
     "• Tip-over safety switch and overheat protection\n• Ideal for small spaces"),
    ("heater", "p21", "Nunix NH-02 Portable Electric Room Heater", 1500, 0,
     "• 800 watts, quality quartz\n• Over-heat protection and tip-over switch\n• 1 year warranty"),
    ("heater", "p22", "Nunix HQ1250 Ceramic Quartz Room Heater", 1900, 0,
     "• Four quartz heating tubes for fast, radiant warmth\n• Built-in overheat protection\n"
     "• Tip-over switch cuts power if knocked over\n• Portable, compact – bedrooms, living rooms and offices"),
    ("heater", "p23", "Macro HQ-800 Quartz Room Heater", 1100, 0,
     "• Portable 800W electric heater\n• Two heat settings\n• Tip-over protection"),

    ("storage", None, "Black 5-Tier Foldable Kitchen Rack with Wheels", 5000, 0,
     "• Foldable, collapsible frame – saves space when not in use\n• Smooth-rolling wheels (casters)\n"
     "• Heavy-duty carbon / stainless steel frame for appliances and cookware\n"
     "• For kitchens, garages, pantries or living spaces"),
]


def reset_products(db):
    for row in db.execute("SELECT filename FROM product_images").fetchall():
        delete_image_file(row["filename"])
    db.execute("DELETE FROM products")
    db.execute("DELETE FROM product_images")


def seed(reset=False):
    with app.app_context():
        db = get_db()
        if reset:
            reset_products(db)
        elif db.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
            print("Products already exist - seed skipped (use --reset to replace them).")
            return
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        cat_ids = {}
        for sort, (key, name, icon) in enumerate(CATEGORIES):
            row = db.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
            if row:
                db.execute("UPDATE categories SET sort = ? WHERE id = ?", (sort, row["id"]))
                cat_ids[key] = row["id"]
            else:
                cat_ids[key] = db.execute("INSERT INTO categories(name, slug, icon, sort) VALUES (?,?,?,?)",
                                          (name, unique_slug("categories", name), icon, sort)).lastrowid
        # newest first on the site = reverse insert order, so insert the list backwards
        for key, img, name, price, featured, desc in reversed(PRODUCTS):
            pid = db.execute("""INSERT INTO products(name, slug, category_id, price, description, featured)
                                VALUES (?,?,?,?,?,?)""",
                             (name, unique_slug("products", name), cat_ids[key], price, desc, featured)).lastrowid
            src = os.path.join(HERE, "seed_images", f"{img}.webp") if img else None
            if src and os.path.exists(src):
                fname = f"{uuid.uuid4().hex[:16]}.webp"
                shutil.copy(src, os.path.join(UPLOAD_DIR, fname))
                db.execute("INSERT INTO product_images(product_id, filename, sort) VALUES (?,?,0)", (pid, fname))
        db.commit()
        print(f"Seeded {len(PRODUCTS)} products.")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
