"""Load starter categories and products (run once: python seed.py).

Images in seed_images/ were collected from Pinterest as placeholders.
Replace them with your own product photos from the admin panel.
"""
import os
import shutil
import uuid

from app import UPLOAD_DIR, app, get_db, unique_slug

HERE = os.path.dirname(os.path.abspath(__file__))

CATEGORIES = [
    ("Woofers & Sound", "woofer", "🔊"),
    ("TVs", "tv", "📺"),
    ("Dinner Sets", "dinner", "🍽️"),
    ("Cookware", "cookware", "🍲"),
    ("Cookers", "cooker", "🔥"),
    ("Fridges", "fridge", "🧊"),
]

# (category key, image number, name, price, old price, featured, description)
PRODUCTS = [
    ("woofer", 1, "3.1 Channel Bluetooth Subwoofer System", 8500, 10500, 1,
     "Powerful 3.1 home woofer with blue LED bass ring, 2 satellite speakers and remote control.\n"
     "• Bluetooth, USB, SD card & FM radio\n• Deep bass subwoofer\n• Ideal for living rooms and shops"),
    ("woofer", 2, "Hi-Fi 3.1 Woofer with LED Display", 9800, 12000, 0,
     "Stylish multimedia speaker system with LED lights and digital display.\n"
     "• Bluetooth / USB / AUX\n• Rich bass and clear vocals\n• Remote control included"),
    ("woofer", 3, "2.1 Multimedia Woofer - Red Edition", 6500, None, 0,
     "Compact 2.1 woofer with striking red accents and remote.\n• Bluetooth & USB playback\n• FM radio\n• Great value for bulk buyers"),
    ("woofer", 4, "Studio 2.1 Bookshelf Speaker Set", 14500, None, 0,
     "Premium wooden-cabinet 2.1 speaker set for crisp, room-filling sound.\n• Optical & Bluetooth input\n• Solid wood cabinet"),
    ("woofer", 5, "5.1 Home Theatre Tower System", 28500, 32000, 1,
     "Complete 5.1 surround sound with four tall tower speakers, centre speaker and powered subwoofer.\n"
     "• Bluetooth, HDMI (ARC), USB\n• Cinema experience at home"),
    ("woofer", 6, "12\" Powered Subwoofer", 18000, None, 0,
     "Stand-alone 12-inch active subwoofer for deep, punchy bass. Pairs with any sound system."),

    ("tv", 1, "43\" Full HD Smart TV", 26500, 29999, 1,
     "Frameless 43-inch Smart TV with Netflix, YouTube and Wi-Fi.\n• Full HD 1080p\n• 2x HDMI, 2x USB\n• Free-to-air digital tuner"),
    ("tv", 2, "55\" 4K UHD Smart TV", 48500, 54000, 1,
     "Big 55-inch 4K Ultra HD Smart TV with HDR and slim bezels.\n• Google / Android apps\n• Dolby Audio\n• Voice remote"),
    ("tv", 3, "65\" 4K QLED Smart TV", 79000, 88000, 0,
     "Vivid QLED colour on a 65-inch 4K display.\n• HDR10+\n• Built-in Chromecast\n• Perfect for lounges and hotels"),
    ("tv", 4, "32\" HD LED TV", 13500, 15500, 0,
     "Reliable 32-inch HD LED TV with digital tuner.\n• HDMI & USB\n• Low power consumption\n• Great for bedrooms and shops"),
    ("tv", 5, "55\" Google TV 4K Dolby Vision", 56000, None, 0,
     "55-inch Google TV with Dolby Vision & Dolby Atmos.\n• Hands-free voice control\n• Thousands of apps"),
    ("tv", 6, "50\" Frameless 4K Smart TV", 39500, 43000, 0,
     "50-inch 4K Smart TV with an elegant frameless design and chrome stand."),

    ("dinner", 1, "Porcelain Gold Rim Dinner Set - 24 pcs", 6800, 8500, 1,
     "Elegant white porcelain dinner set with gold rim.\n• Plates, bowls, platters & cups\n• Dishwasher safe\n• Perfect gift set"),
    ("dinner", 2, "Luxury Gold Line Dinner Set - 32 pcs", 9500, None, 0,
     "Premium 32-piece set with oval serving platter and matching bowls. Ideal for family and events."),
    ("dinner", 3, "Classic White & Gold Dinner Set - 18 pcs", 4800, 5500, 0,
     "Timeless everyday dinner set with cups and saucers. Chip-resistant ceramic."),
    ("dinner", 4, "Hammered Gold Rim Dinnerware - 16 pcs", 5200, None, 0,
     "Modern hammered-texture porcelain with gold rim. Plates, bowls and mugs for 4."),
    ("dinner", 5, "Royal Gold Dinner & Serving Set - 40 pcs", 12500, 14500, 1,
     "Complete dining and serving collection for large families and occasions."),
    ("dinner", 6, "Textured White Dinner Set - 12 pcs", 3600, None, 0,
     "Minimalist textured ceramic set with gold edge. Microwave safe."),

    ("cookware", 1, "Stainless Steel Cookware Set - 12 pcs", 7500, 9000, 1,
     "Mirror-finish stainless steel pots with glass lids and gold handles.\n• Induction & gas compatible\n• Rust resistant"),
    ("cookware", 2, "Tri-Ply Stainless Pots & Pans - 10 pcs", 9800, None, 0,
     "Heavy tri-ply base for even heating. Includes fry pan, saucepans and stock pot."),
    ("cookware", 3, "Stackable Stainless Casserole Set - 6 pcs", 5400, 6500, 0,
     "Space-saving stackable stainless steel pots with tempered glass lids."),
    ("cookware", 4, "Professional Stainless Cookware - 14 pcs", 13500, None, 0,
     "Chef-grade stainless steel set with riveted handles. Oven safe."),
    ("cookware", 5, "Non-Stick Granite Cookware Set - 10 pcs", 8200, 9500, 1,
     "Black granite non-stick coating, PFOA free. Easy to clean, cooks with less oil."),
    ("cookware", 6, "Non-Stick Pots & Pans with Utensils - 23 pcs", 11500, None, 0,
     "Brown granite non-stick cookware with wooden-look handles, utensils and pot protectors."),

    ("cooker", 1, "4 Gas Burner Standing Cooker 60x60", 32500, 36000, 1,
     "Free-standing 60x60 cooker with 4 gas burners and gas oven.\n• Auto ignition\n• Stainless steel finish\n• Oven light & grill"),
    ("cooker", 2, "3 Gas + 1 Electric Cooker 60x55", 29500, None, 0,
     "Versatile cooker with 3 gas burners and 1 electric hot plate plus electric oven."),
    ("cooker", 3, "5 Burner 90cm Gas Cooker with Oven", 58000, 64000, 1,
     "Large 90cm range cooker with 5 burners including wok burner and big-capacity oven."),
    ("cooker", 4, "4 Burner White Standing Cooker 50x50", 24500, None, 0,
     "Compact white standing cooker with glass lid. Ideal for apartments."),
    ("cooker", 5, "4 Gas Burner Black Cooker with Glass Lid", 26500, 28500, 0,
     "Black enamel standing cooker with gas oven, rotisserie and tempered glass lid."),
    ("cooker", 6, "Inox 4 Burner Cooker with Electric Oven", 38500, None, 0,
     "Stainless steel cooker with electric fan oven and digital timer."),

    ("fridge", 1, "Side by Side Fridge with Water Dispenser 520L", 115000, 125000, 1,
     "Spacious side-by-side refrigerator with water dispenser.\n• No frost\n• Inverter compressor\n• Energy saving"),
    ("fridge", 2, "Double Door Fridge 250L", 42500, 46000, 1,
     "Top-freezer double door fridge, silver finish.\n• Fresh cooling\n• Adjustable glass shelves"),
    ("fridge", 3, "Black Side by Side Fridge 560L", 128000, None, 0,
     "Matte black side-by-side refrigerator with water dispenser and digital control."),
    ("fridge", 4, "French Door Refrigerator with Ice Maker", 185000, None, 0,
     "Premium 4-door French door fridge with ice & water dispenser and door-in-door."),
    ("fridge", 5, "Silver Double Door Fridge 180L", 34500, 37500, 0,
     "Compact double door fridge ideal for small families."),
    ("fridge", 6, "Single Door Fridge 190L - Wine Floral", 27500, None, 0,
     "Direct-cool single door refrigerator with floral finish and stabilizer-free operation."),
]


def seed():
    with app.app_context():
        db = get_db()
        if db.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
            print("Products already exist - seed skipped.")
            return
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        cat_ids = {}
        for sort, (name, key, icon) in enumerate(CATEGORIES):
            cur = db.execute("INSERT INTO categories(name, slug, icon, sort) VALUES (?,?,?,?)",
                             (name, unique_slug("categories", name), icon, sort))
            cat_ids[key] = cur.lastrowid
        for key, n, name, price, old, featured, desc in PRODUCTS:
            cur = db.execute("""INSERT INTO products(name, slug, category_id, price, old_price, description, featured)
                                VALUES (?,?,?,?,?,?,?)""",
                             (name, unique_slug("products", name), cat_ids[key], price, old, desc, featured))
            src = os.path.join(HERE, "seed_images", f"{key}-{n}.webp")
            if os.path.exists(src):
                fname = f"{uuid.uuid4().hex[:16]}.webp"
                shutil.copy(src, os.path.join(UPLOAD_DIR, fname))
                db.execute("INSERT INTO product_images(product_id, filename, sort) VALUES (?,?,0)",
                           (cur.lastrowid, fname))
        db.commit()
        print(f"Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products.")


if __name__ == "__main__":
    seed()
