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
    ("xmas", "Christmas Trees", "🎄"),
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
    ("xmas", "p25-tree", "Cypress Artificial Christmas Tree 4ft (120cm)", 1600, 1,
     "Cypress artificial Christmas tree - xmas decoration tree.\n"
     "• Durable PVC foliage with a sturdy fold-out base\n• Rich green pine needles\n• Height: 4ft (120cm)"),
    ("xmas", "p25-tree", "Cypress Artificial Christmas Tree 5ft (150cm)", 3000, 1,
     "Cypress artificial Christmas tree - xmas decoration tree.\n"
     "• Durable PVC foliage with a sturdy fold-out base\n• Rich green pine needles\n• Height: 5ft (150cm)"),
    ("xmas", "p25-tree", "Cypress Artificial Christmas Tree 6ft (180cm)", 4000, 1,
     "Cypress artificial Christmas tree - xmas decoration tree.\n"
     "• Durable PVC foliage with a sturdy fold-out base\n• Rich green pine needles\n• Height: 6ft (180cm)"),
    ("xmas", "p25-tree", "Cypress Artificial Christmas Tree 7ft (210cm)", 4800, 0,
     "Cypress artificial Christmas tree - xmas decoration tree.\n"
     "• Durable PVC foliage with a sturdy fold-out base\n• Rich green pine needles\n• Height: 7ft (210cm)"),

    ("tv", "tv32smart", "Skyworth 32\" Smart TV", 17000, 0,
     "• 32-inch smart TV\n• HDR10 and HLG picture\n• Dolby Audio and DTS sound\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast and screen mirroring\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2) - no decoder needed\n• Wi-Fi, Bluetooth and Ethernet\n• Slim frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv43qled2k", "Skyworth 43\" 2K QLED Google TV", 25000, 1,
     "• 43-inch QLED+ with Quantum Dot colour\n• 2K / Full HD picture\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv43smart4k", "Skyworth 43\" 4K Smart TV", 28500, 0,
     "• 43-inch smart TV\n• 4K Ultra HD (3840 x 2160)\n• HDR10 and HLG picture\n• Dolby Audio and DTS sound\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast and screen mirroring\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2) - no decoder needed\n• Wi-Fi, Bluetooth and Ethernet\n• Slim frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv50qled2k", "Skyworth 50\" 2K QLED Google TV", 32000, 1,
     "• 50-inch QLED+ with Quantum Dot colour\n• 2K / Full HD picture\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• World Cup promotion price"),
    ("tv", "tv50qled4k", "Skyworth 50\" 4K QLED Google TV", 37500, 0,
     "• 50-inch QLED+ with Quantum Dot colour\n• 4K Ultra HD (3840 x 2160)\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv55smart", "Skyworth 55\" Smart TV", 40500, 0,
     "• 55-inch smart TV\n• HDR10 and HLG picture\n• Dolby Audio and DTS sound\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast and screen mirroring\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2) - no decoder needed\n• Wi-Fi, Bluetooth and Ethernet\n• Slim frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv55qled", "Skyworth 55\" QLED Google TV", 41500, 1,
     "• 55-inch QLED+ with Quantum Dot colour\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv60qled", "Skyworth 60\" QLED Google TV", 51000, 0,
     "• 60-inch QLED+ with Quantum Dot colour\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv65smart4k", "Skyworth 65\" 4K Smart TV", 61000, 0,
     "• 65-inch smart TV\n• 4K Ultra HD (3840 x 2160)\n• HDR10 and HLG picture\n• Dolby Audio and DTS sound\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast and screen mirroring\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2) - no decoder needed\n• Wi-Fi, Bluetooth and Ethernet\n• Slim frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv65qled", "Skyworth 65\" QLED Google TV", 69000, 0,
     "• 65-inch QLED+ with Quantum Dot colour\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv75qled", "Skyworth 75\" QLED Google TV", 116000, 0,
     "• 75-inch QLED+ with Quantum Dot colour\n• EyeCare low-blue-light, flicker free for long viewing\n• Dolby Audio with Dolby Atmos support\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Find-my-remote\n• Chromecast and screen mirroring from your phone\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),
    ("tv", "tv55mini", "Skyworth 55\" Mini-QLED Google TV", 50000, 1,
     "• 55-inch 4K Mini-QLED - brighter highlights, deeper blacks\n• Quantum Dot colour for richer, truer shades\n• Dolby Vision and HDR10+\n• Dolby Atmos sound\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast and screen mirroring\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• World Cup promotion price"),
    ("tv", "tv65mini", "Skyworth 65\" Mini-QLED Google TV", 76000, 0,
     "• 65-inch 4K Mini-QLED - brighter highlights, deeper blacks\n• Quantum Dot colour for richer, truer shades\n• Dolby Vision and HDR10+\n• Dolby Atmos sound\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast and screen mirroring\n• HDMI with ARC for soundbars, USB media playback\n• Built-in digital tuner (DVB-T2), Wi-Fi and Bluetooth\n• Frameless design, wall-mountable\n• End month offer"),

    ("tv", "tcl_qled43", "TCL 43\" QLED Google TV (S5K)", 27500, 1,
     "• 43-inch QLED with Quantum Dot colour\n• Full HD picture, HDR10 and HLG\n• VA panel, about 4000:1 native contrast\n• 60Hz refresh rate, ALLM for gaming\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Voice search and casting from your phone\n• Dolby Audio, 20W sound\n• 3 x HDMI, 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Frameless design, wall-mountable"),
    ("tv", "tcl_google", "TCL 43\" 4K Google TV (V6D)", 32000, 0,
     "• 43-inch 4K Ultra HD (3840 x 2160)\n• Direct LED with HVA panel - up to 5000:1 native contrast\n• AiPQ processor with MEMC motion smoothing for sport\n• HDR10 and HLG\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast built in\n• Dolby Atmos, 2 x 10W speakers\n• 2GB RAM, 16GB storage\n• 3 x HDMI (one ARC), 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Built-in digital tuner, wall-mountable"),
    ("tv", "tcl_qled", "TCL 50\" QLED Google TV (S5K)", 34000, 0,
     "• 50-inch QLED with Quantum Dot colour\n• Full HD picture, HDR10 and HLG\n• VA panel, about 4000:1 native contrast\n• 60Hz refresh rate, ALLM for gaming\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Voice search and casting from your phone\n• Dolby Audio, 20W sound\n• 3 x HDMI, 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Frameless design, wall-mountable"),
    ("tv", "tcl_google", "TCL 50\" 4K Google TV (V6D)", 39000, 0,
     "• 50-inch 4K Ultra HD (3840 x 2160)\n• Direct LED with HVA panel - up to 5000:1 native contrast\n• AiPQ processor with MEMC motion smoothing for sport\n• HDR10 and HLG\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast built in\n• Dolby Atmos, 2 x 10W speakers\n• 2GB RAM, 16GB storage\n• 3 x HDMI (one ARC), 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Built-in digital tuner, wall-mountable"),
    ("tv", "tcl_qled", "TCL 50\" QLED Google TV (T6D)", 42000, 1,
     "• 50-inch 4K QLED with Quantum Dot colour\n• Up to 93% DCI-P3 cinema colour, over a billion shades\n• HVA panel with Direct LED backlight, AiPQ Pro processor\n• Dolby Vision, HDR10+, HDR10 and HLG\n• 120Hz Game Accelerator (DLG), ALLM and Game Bar\n• Dolby Atmos and DTS Virtual:X, 20W sound\n• Google TV with Google Assistant and Chromecast\n• 2GB RAM, 16GB storage\n• 3 x HDMI with eARC for soundbars, USB playback\n• Wi-Fi, Bluetooth, Ethernet, wall-mountable"),
    ("tv", "tcl_google2", "TCL 55\" 4K Google TV (V6D)", 42000, 0,
     "• 55-inch 4K Ultra HD (3840 x 2160)\n• Direct LED with HVA panel - up to 5000:1 native contrast\n• AiPQ processor with MEMC motion smoothing for sport\n• HDR10 and HLG\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast built in\n• Dolby Atmos, 2 x 10W speakers\n• 2GB RAM, 16GB storage\n• 3 x HDMI (one ARC), 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Built-in digital tuner, wall-mountable"),
    ("tv", "tcl_qled", "TCL 55\" QLED Google TV (T6D)", 49000, 1,
     "• 55-inch 4K QLED with Quantum Dot colour\n• Up to 93% DCI-P3 cinema colour, over a billion shades\n• HVA panel with Direct LED backlight, AiPQ Pro processor\n• Dolby Vision, HDR10+, HDR10 and HLG\n• 120Hz Game Accelerator (DLG), ALLM and Game Bar\n• Dolby Atmos and DTS Virtual:X, 20W sound\n• Google TV with Google Assistant and Chromecast\n• 2GB RAM, 16GB storage\n• 3 x HDMI with eARC for soundbars, USB playback\n• Wi-Fi, Bluetooth, Ethernet, wall-mountable"),
    ("tv", "tcl_p8l55", "TCL 55\" QLED Google TV (P8LK)", 58000, 0,
     "• 55-inch 4K QD-Mini LED with Quantum Dot colour\n• HVA panel with local dimming for deep blacks\n• 144Hz native refresh - smooth sport and gaming\n• Dolby Vision, HDR10+, HLG and Filmmaker Mode\n• ONKYO 2.1 speakers with built-in subwoofer, Dolby Atmos\n• Google TV (Android 14) with Google Assistant\n• HDMI 2.1, AMD FreeSync, VRR and ALLM\n• Chromecast and AirPlay 2 casting\n• Dual-band Wi-Fi, Bluetooth, Ethernet"),
    ("tv", "tcl_c6k55", "TCL 55\" QD-Mini LED Google TV (C6K) - NEW", 65000, 1,
     "• 55-inch 4K QD-Mini LED with precise local dimming\n• Up to 93% DCI-P3 cinema colour\n• HVA panel, 144Hz native refresh\n• AiPQ Pro processor, Dolby Vision IQ adjusts to your room light\n• HDR10+, HDR10 and HLG\n• ONKYO 2.1 audio (2 x 10W plus 20W subwoofer), Dolby Atmos and DTS Virtual:X\n• AMD FreeSync Premium Pro, ALLM and VRR for consoles\n• Google TV with Google Assistant, Kids profile and Google Meet\n• 2 x HDMI 2.1 with eARC, USB, Wi-Fi, Bluetooth, Ethernet\n• New model"),
    ("tv", "tcl_v6d65", "TCL 65\" 4K Google TV (V6D)", 65000, 0,
     "• 65-inch 4K Ultra HD (3840 x 2160)\n• Direct LED with HVA panel - up to 5000:1 native contrast\n• AiPQ processor with MEMC motion smoothing for sport\n• HDR10 and HLG\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast built in\n• Dolby Atmos, 2 x 10W speakers\n• 2GB RAM, 16GB storage\n• 3 x HDMI (one ARC), 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Built-in digital tuner, wall-mountable"),
    ("tv", "tcl_qled", "TCL 65\" QLED Google TV (T6D)", 73000, 0,
     "• 65-inch 4K QLED with Quantum Dot colour\n• Up to 93% DCI-P3 cinema colour, over a billion shades\n• HVA panel with Direct LED backlight, AiPQ Pro processor\n• Dolby Vision, HDR10+, HDR10 and HLG\n• 120Hz Game Accelerator (DLG), ALLM and Game Bar\n• Dolby Atmos and DTS Virtual:X, 20W sound\n• Google TV with Google Assistant and Chromecast\n• 2GB RAM, 16GB storage\n• 3 x HDMI with eARC for soundbars, USB playback\n• Wi-Fi, Bluetooth, Ethernet, wall-mountable"),
    ("tv", "tcl_c6k", "TCL 65\" QD-Mini LED Google TV (C6K) - NEW", 96000, 0,
     "• 65-inch 4K QD-Mini LED with precise local dimming\n• Up to 93% DCI-P3 cinema colour\n• HVA panel, 144Hz native refresh\n• AiPQ Pro processor, Dolby Vision IQ adjusts to your room light\n• HDR10+, HDR10 and HLG\n• ONKYO 2.1 audio (2 x 10W plus 20W subwoofer), Dolby Atmos and DTS Virtual:X\n• AMD FreeSync Premium Pro, ALLM and VRR for consoles\n• Google TV with Google Assistant, Kids profile and Google Meet\n• 2 x HDMI 2.1 with eARC, USB, Wi-Fi, Bluetooth, Ethernet\n• New model"),
    ("tv", "tcl_c7l65", "TCL 65\" QLED Google TV (C7L)", 124000, 0,
     "• 65-inch 4K SQD-Mini LED, high brightness for bright rooms\n• HVA 2.0 panel with fine local dimming\n• Up to 144Hz with AMD FreeSync for consoles\n• Dolby Vision and HDR10+\n• Sound tuned by Bang & Olufsen with Dolby Atmos\n• Google TV with Google Assistant and Chromecast\n• 4 x HDMI 2.1 with eARC, USB, Wi-Fi, Bluetooth, Ethernet"),
    ("tv", "tcl_c8l65", "TCL 65\" QD-Mini LED Google TV (C8L) - NEW", 146000, 0,
     "• 65-inch 4K SQD-Mini LED flagship (WHVA 2.0 panel)\n• TSR AiPQ Pro processor with wide BT.2020 cinema colour\n• 144Hz panel, VRR and ALLM on all four HDMI 2.1 ports\n• Dolby Vision IQ, HDR10+, HDR10 and HLG\n• Bang & Olufsen 2.1 audio, 60W, Dolby Atmos and DTS:X\n• Google TV with Google Assistant, Kids profile and Google Meet\n• AirPlay 2 and Chromecast built in\n• Wi-Fi 6, Bluetooth 5.4, Ethernet, wall-mountable\n• New model"),
    ("tv", "tcl_google", "TCL 75\" 4K Google TV (V6D)", 96000, 0,
     "• 75-inch 4K Ultra HD (3840 x 2160)\n• Direct LED with HVA panel - up to 5000:1 native contrast\n• AiPQ processor with MEMC motion smoothing for sport\n• HDR10 and HLG\n• Google TV - Netflix, YouTube, Prime Video and Showmax\n• Google Assistant voice remote, Chromecast built in\n• Dolby Atmos, 2 x 10W speakers\n• 2GB RAM, 16GB storage\n• 3 x HDMI (one ARC), 2 x USB, Wi-Fi, Bluetooth, Ethernet\n• Built-in digital tuner, wall-mountable"),
    ("tv", "tcl_qled", "TCL 75\" QLED Google TV (T6D) - NEW", 106000, 0,
     "• 75-inch 4K QLED with Quantum Dot colour\n• Up to 93% DCI-P3 cinema colour, over a billion shades\n• HVA panel with Direct LED backlight, AiPQ Pro processor\n• Dolby Vision, HDR10+, HDR10 and HLG\n• 120Hz Game Accelerator (DLG), ALLM and Game Bar\n• Dolby Atmos and DTS Virtual:X, 20W sound\n• Google TV with Google Assistant and Chromecast\n• 2GB RAM, 16GB storage\n• 3 x HDMI with eARC for soundbars, USB playback\n• Wi-Fi, Bluetooth, Ethernet, wall-mountable\n• New model"),
    ("tv", "tcl_c6k", "TCL 75\" QD-Mini LED Google TV (C6K) - NEW", 141000, 0,
     "• 75-inch 4K QD-Mini LED with precise local dimming\n• Up to 93% DCI-P3 cinema colour\n• HVA panel, 144Hz native refresh\n• AiPQ Pro processor, Dolby Vision IQ adjusts to your room light\n• HDR10+, HDR10 and HLG\n• ONKYO 2.1 audio (2 x 10W plus 20W subwoofer), Dolby Atmos and DTS Virtual:X\n• AMD FreeSync Premium Pro, ALLM and VRR for consoles\n• Google TV with Google Assistant, Kids profile and Google Meet\n• 2 x HDMI 2.1 with eARC, USB, Wi-Fi, Bluetooth, Ethernet\n• New model"),
    ("tv", "tcl_c7l75", "TCL 75\" QD-Mini LED Google TV (C7L)", 173000, 0,
     "• 75-inch 4K SQD-Mini LED, high brightness for bright rooms\n• HVA 2.0 panel with fine local dimming\n• Up to 144Hz with AMD FreeSync for consoles\n• Dolby Vision and HDR10+\n• Sound tuned by Bang & Olufsen with Dolby Atmos\n• Google TV with Google Assistant and Chromecast\n• 4 x HDMI 2.1 with eARC, USB, Wi-Fi, Bluetooth, Ethernet"),
    ("tv", "tcl_c8l75", "TCL 75\" Mini LED Google TV (C8L)", 195000, 0,
     "• 75-inch 4K SQD-Mini LED flagship (WHVA 2.0 panel)\n• TSR AiPQ Pro processor with wide BT.2020 cinema colour\n• 144Hz panel, VRR and ALLM on all four HDMI 2.1 ports\n• Dolby Vision IQ, HDR10+, HDR10 and HLG\n• Bang & Olufsen 2.1 audio, 60W, Dolby Atmos and DTS:X\n• Google TV with Google Assistant, Kids profile and Google Meet\n• AirPlay 2 and Chromecast built in\n• Wi-Fi 6, Bluetooth 5.4, Ethernet, wall-mountable"),
    ("tv", "tcl_c6k", "TCL 85\" QD-Mini LED Google TV (C6K)", 176000, 0,
     "• 85-inch 4K QD-Mini LED with precise local dimming\n• Up to 93% DCI-P3 cinema colour\n• HVA panel, 144Hz native refresh\n• AiPQ Pro processor, Dolby Vision IQ adjusts to your room light\n• HDR10+, HDR10 and HLG\n• ONKYO 2.1 audio (2 x 10W plus 20W subwoofer), Dolby Atmos and DTS Virtual:X\n• AMD FreeSync Premium Pro, ALLM and VRR for consoles\n• Google TV with Google Assistant, Kids profile and Google Meet\n• 2 x HDMI 2.1 with eARC, USB, Wi-Fi, Bluetooth, Ethernet"),
    ("tv", "tcl_p8l85", "TCL 85\" QLED Google TV (P8L)", 166000, 0,
     "• 85-inch 4K QD-Mini LED with Quantum Dot colour\n• HVA panel with local dimming for deep blacks\n• 144Hz native refresh with 288Hz game accelerator\n• Dolby Vision, HDR10+, HLG and Filmmaker Mode\n• ONKYO 2.1 speakers with subwoofer, Dolby Atmos and DTS Virtual:X\n• Google TV (Android 14), 3GB RAM, 32GB storage\n• HDMI 2.1, AMD FreeSync, VRR and ALLM\n• Chromecast, AirPlay 2 and Miracast casting\n• Dual-band Wi-Fi, Bluetooth 5.4, Ethernet"),
    ("tv", "tcl_c8l85", "TCL 85\" QD-Mini LED Google TV (C8L)", 281000, 0,
     "• 85-inch 4K SQD-Mini LED flagship (WHVA 2.0 panel)\n• TSR AiPQ Pro processor with wide BT.2020 cinema colour\n• 144Hz panel, VRR and ALLM on all four HDMI 2.1 ports\n• Dolby Vision IQ, HDR10+, HDR10 and HLG\n• Bang & Olufsen 2.1 audio, 60W, Dolby Atmos and DTS:X\n• Google TV with Google Assistant, Kids profile and Google Meet\n• AirPlay 2 and Chromecast built in\n• Wi-Fi 6, Bluetooth 5.4, Ethernet, wall-mountable"),

    ("tv", "vit_24", "Vitron 24\" Digital TV", 8400, 0,
     "• 24-inch digital TV\n• Free-to-air channels straight from the aerial - no decoder, no monthly fees\n• Built-in DVB-T2 tuner\n• USB movie and music playback\n• HDMI for decoder, DVD player or console\n• AV input for older equipment\n• Wall-mountable, low power use"),
    ("tv", "vit_32", "Vitron 32\" Digital TV", 10600, 0,
     "• 32-inch digital TV\n• Free-to-air channels straight from the aerial - no decoder, no monthly fees\n• Built-in DVB-T2 tuner\n• USB movie and music playback\n• HDMI for decoder, DVD player or console\n• AV input for older equipment\n• Wall-mountable, low power use"),
    ("tv", "vit_32s", "Vitron 32\" Smart TV", 13000, 1,
     "• 32-inch smart TV\n• Android home screen with Play Store apps\n• Netflix and YouTube built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• HDMI, USB, AV and Ethernet ports, Wi-Fi\n• Wall-mountable"),
    ("tv", "vit_40", "Vitron 40\" Whale Smart TV", 18000, 0,
     "• 40-inch Whale smart TV\n• Whale OS home screen with app store\n• Netflix, YouTube and Prime Video built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• 2 x HDMI, USB, AV and Ethernet, Wi-Fi\n• Frameless design with slim bezel, wall-mountable"),
    ("tv", "vit_43", "Vitron 43\" Whale Smart TV", 19800, 1,
     "• 43-inch Whale smart TV\n• Whale OS home screen with app store\n• Netflix, YouTube and Prime Video built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• 2 x HDMI, USB, AV and Ethernet, Wi-Fi\n• Frameless design with slim bezel, wall-mountable"),
    ("tv", "vit_50a", "Vitron 50\" Smart TV 2K", 27500, 0,
     "• 50-inch smart TV\n• 2K / Full HD picture\n• Android home screen with Play Store apps\n• Netflix and YouTube built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• HDMI, USB, AV and Ethernet ports, Wi-Fi\n• Wall-mountable"),
    ("tv", "vit_50c", "Vitron 50\" Whale Smart TV", 27400, 0,
     "• 50-inch Whale smart TV\n• Whale OS home screen with app store\n• Netflix, YouTube and Prime Video built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• 2 x HDMI, USB, AV and Ethernet, Wi-Fi\n• Frameless design with slim bezel, wall-mountable"),
    ("tv", "vit_50b", "Vitron 50\" Whale Smart QLED TV", 28500, 1,
     "• 50-inch QLED with Quantum Dot colour\n• Whale OS home screen with app store\n• Netflix, YouTube and Prime Video built in\n• Screen mirroring from your phone\n• Bluetooth for speakers and headphones\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• 2 x HDMI, 2 x USB, AV and Ethernet\n• Frameless design, wall-mountable"),
    ("tv", "vit_55", "Vitron 55\" Whale Smart TV 4K", 35500, 0,
     "• 55-inch Whale smart TV\n• 4K Ultra HD (3840 x 2160)\n• Whale OS home screen with app store\n• Netflix, YouTube and Prime Video built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• 2 x HDMI, USB, AV and Ethernet, Wi-Fi\n• Frameless design with slim bezel, wall-mountable"),
    ("tv", "vit_65", "Vitron 65\" Smart TV", 54000, 0,
     "• 65-inch smart TV\n• Android home screen with Play Store apps\n• Netflix and YouTube built in\n• Screen mirroring from your phone\n• USB movie and music playback\n• Built-in DVB-T2 tuner - free-to-air channels, no decoder\n• HDMI, USB, AV and Ethernet ports, Wi-Fi\n• Wall-mountable"),

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

    ("storage", "p16", "Black 5-Tier Foldable Kitchen Rack with Wheels", 5000, 0,
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
