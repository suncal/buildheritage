#!/usr/bin/env python3
"""Build Heritage — static site generator.
Regenerate:            python3 gen_site.py
Publish next N pages:  python3 gen_site.py --publish-next 3   (used by weekly GitHub Action)

Lives inside the repo so GitHub Actions can run it. State in published.json.
"""
import os, html, json, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = BASE  # generator lives at the repo/web root
BASE_URL = "https://buildheritage.org"
LEAD_EMAIL = "info@buildheritage.org"
INDEXNOW_KEY = "91299c4117504e89ed344bebd0ae14b1"
PUBLISHED_FILE = os.path.join(BASE, "published.json")
CONSENT_VERSION = "2026-08-15-v1"

CITIES = ["Atlanta", "Marietta", "Alpharetta", "Roswell", "Sandy Springs",
          "Johns Creek", "Duluth", "Lawrenceville", "Decatur", "Smyrna",
          "Kennesaw", "Woodstock", "Cumming", "Gainesville", "Athens",
          "Augusta", "Macon", "Savannah", "Columbus"]

# ---- Local-SEO city pages -------------------------------------------------
# Each priority city gets unique local copy. Pages publish gradually (3/week)
# via the GitHub Action so growth looks organic to Google.
CITY_INFO = {
  "marietta": {"name": "Marietta", "county": "Cobb County",
    "blurb": "From the historic homes around Marietta Square to the established neighborhoods of East Cobb, Marietta mixes century-old craftsmanship with busy family subdivisions — and both need contractors who respect the difference.",
    "hoods": ["Marietta Square", "East Cobb", "Whitlock Avenue", "Indian Hills", "Sprayberry"]},
  "alpharetta": {"name": "Alpharetta", "county": "Fulton County",
    "blurb": "Alpharetta's growth around Avalon and downtown has filled the city with newer construction — which means builder-grade finishes that homeowners upgrade, and busy families who want work done right the first time.",
    "hoods": ["Downtown Alpharetta", "Avalon", "Windward", "Milton border", "Webb Bridge"]},
  "roswell": {"name": "Roswell", "county": "Fulton County",
    "blurb": "Between Historic Roswell's antebellum charm and the big wave of 1980s–90s subdivisions off Holcomb Bridge, Roswell homes are at exactly the age where roofs, floors, paint and trim come due for renewal.",
    "hoods": ["Historic Roswell", "Canton Street", "Holcomb Bridge", "Martins Landing", "Crabapple"]},
  "woodstock": {"name": "Woodstock", "county": "Cherokee County",
    "blurb": "Woodstock is one of Georgia's fastest-growing cities — Downtown Woodstock and Towne Lake keep adding families, and with them a steady demand for movers, painters and finish work that keeps up with new-home standards.",
    "hoods": ["Downtown Woodstock", "Towne Lake", "Eagle Watch", "Bradshaw Farm", "River Park"]},
  "kennesaw": {"name": "Kennesaw", "county": "Cobb County",
    "blurb": "From brick ranches near Kennesaw Mountain to newer builds around Kennesaw State, this is a city of practical homeowners who compare quotes line by line — exactly how we write them.",
    "hoods": ["Kennesaw Mountain", "Legacy Park", "Pinetree", "Shiloh Valley", "Barrett Parkway corridor"]},
  "smyrna": {"name": "Smyrna", "county": "Cobb County",
    "blurb": "Smyrna's Market Village and the Vinings edge have made it one of metro Atlanta's most in-demand addresses — a mix of 1990s townhomes and renovated intown houses where clean, fast, insured work wins referrals.",
    "hoods": ["Market Village", "Vinings edge", "Williams Park", "Forest Hills", "Belmont"]},
  "sandy-springs": {"name": "Sandy Springs", "county": "Fulton County",
    "blurb": "Sandy Springs pairs established custom homes under mature hardwoods with busy Perimeter professionals — homeowners who value named crews, confirmed windows, and job sites left spotless.",
    "hoods": ["Perimeter", "Riverside", "Dunwoody Panhandle", "Glenridge", "Powers Ferry"]},
  "decatur": {"name": "Decatur", "county": "DeKalb County",
    "blurb": "Decatur's historic bungalows and Oakhurst cottages are full of character — and full of the plaster, trim, and older framing that reward craftsmen who have actually worked on pre-war houses.",
    "hoods": ["Oakhurst", "Winnona Park", "Great Lakes", "MAK Historic District", "Clairemont"]},
}
CITY_PRIORITY = ["marietta", "alpharetta", "roswell", "woodstock", "kennesaw", "smyrna", "sandy-springs", "decatur"]
SVC_PRIORITY = ["roofing", "painting", "flooring", "drywall", "packing-moving", "doors", "window-door-trim", "framing"]
# Tier 1 (top 3 cities) rotates through all services first, then tier 2.
QUEUE = [(c, s) for group in (CITY_PRIORITY[:3], CITY_PRIORITY[3:]) for s in SVC_PRIORITY for c in group]

# Per-service local angle, slotted with city facts to keep each page's copy distinct.
SVC_LOCAL = {
  "roofing": "Roofs in {city} take the same Georgia beating as everywhere else — hail seasons, summer sun, the occasional tropical remnant — and {county} inspectors know what correct flashing and ventilation look like. We install to that standard, document storm damage for insurers, and leave the yard magnet-swept.",
  "painting": "Painting in {city} ranges from crisp modern palettes in newer subdivisions to careful color work on older homes near {hood}. Every job gets the same prep discipline: patch, sand, prime, caulk — because in Georgia humidity, prep is what a paint job's lifespan is made of.",
  "flooring": "In {city} we install a lot of luxury vinyl plank — it handles Georgia humidity, kids, and dogs better than anything at its price. The difference between a floor that lasts and one that fails is subfloor prep, and that's the part of the quote we never trim.",
  "drywall": "From water-stained ceilings after a {county} storm to full basement build-outs, our finishers work to a standard where raking light shows a flat, clean wall. Texture matching means a patch in a {city} home should be invisible once painted.",
  "packing-moving": "Moving within {city} or across metro Atlanta, our crews wrap furniture, protect floors and door frames, and label every carton by room. {hood} moves are on our regular routes, and commercial moves run after-hours so your business keeps running.",
  "doors": "A new entry door is one of the highest-ROI improvements a {city} home can make — instant curb appeal plus a real seal against Georgia summer heat. We hang doors square, shim them patiently, and adjust until they close like they mean it.",
  "window-door-trim": "Trim is what makes a {city} house look finished. We cut tight miters, scribe to real walls, and — for exteriors in Georgia humidity — install rot-resistant PVC that holds its lines for decades near {hood} and beyond.",
  "framing": "From basement build-outs to engineered load-bearing openings, our framing in {city} is square, plumb and permit-ready. {county} inspections pass the first time because we build to code, not around it.",
}

SERVICES = {
  "packing-moving": {
    "name": "Packing & Moving", "img": "moving.jpg",
    "kw": "packing and moving services",
    "tagline": "Careful hands. Zero drama. Your things arrive like they left.",
    "intro": "Moving is consistently ranked among life's most stressful events — but it doesn't have to be. Build Heritage provides full-service packing and moving across Georgia: professional packing with quality materials, careful loading, protected transport, and placement in your new home exactly where you want everything.",
    "features": ["Full-service packing with premium materials", "Furniture disassembly and reassembly", "Local and long-distance moves within Georgia", "Licensed and insured crews", "Floor, wall and doorway protection", "Transparent flat-rate quotes — no surprise fees"],
    "body": "Whether you're moving a two-bedroom apartment in Atlanta or a full family home in Alpharetta, our crews treat every box like it holds something irreplaceable — because to you, it might. We wrap furniture, protect floors and door frames, label every carton by room, and stage your new home so the first night feels like home, not a warehouse. Commercial moves are handled after-hours to keep your business running.",
    "faqs": [("How far in advance should I book a move in Georgia?", "Two to three weeks is ideal for local moves; four or more for end-of-month dates, which fill fastest. We do accommodate short-notice moves when the schedule allows."),
             ("Do you supply boxes and packing materials?", "Yes. Full-service packing includes boxes, paper, bubble wrap and specialty cartons for TVs, mirrors, and wardrobe items."),
             ("Are my belongings insured during the move?", "Yes — we are licensed and insured, and basic valuation coverage is included with every move. Full-value protection options are available for high-value households."),
             ("Do you handle both residential and commercial moves?", "Both. We move homes, apartments, offices and small warehouses across the state of Georgia.")]
  },
  "painting": {
    "name": "Painting", "img": "painting.jpg",
    "kw": "painting services",
    "tagline": "Crisp lines, flawless finish — interior and exterior painting done right.",
    "intro": "A professional paint job is the fastest way to transform a home — and the easiest one to get wrong. Build Heritage delivers interior and exterior painting across Georgia with meticulous prep, premium paints, and clean, crisp results that last for years in the Southern climate.",
    "features": ["Interior and exterior painting", "Cabinet refinishing and trim work", "Drywall repair before painting — one crew, one schedule", "Premium low-VOC paints", "Full surface prep: patch, sand, prime, caulk", "Clean job sites, daily"],
    "body": "Georgia's humidity and sun are hard on paint. That's why our exterior work starts with pressure washing, scraping, priming and caulking before a single coat goes on — and why we use paints rated for Southern weather. Inside, we protect your floors and furniture, repair the dings and nail pops first, and cut lines you'll want to photograph. Most rooms are done in a day; whole-home repaints in under a week.",
    "faqs": [("How much does it cost to paint a house interior in Georgia?", "Most single rooms fall in the $350–$900 range depending on size and prep needs; whole-home interiors typically range from $3,000–$8,000. Every quote is free and itemized."),
             ("Do you repair drywall before painting?", "Yes — drywall patching, skim coating, and texture matching are part of our prep, so you never need a second contractor."),
             ("What paint brands do you use?", "We work with premium lines from Sherwin-Williams and Benjamin Moore, matched to each surface and room."),
             ("How long does exterior paint last in Georgia's climate?", "With correct prep and quality paint, 7–10 years. Prep is the difference — and it's the part we never skip.")]
  },
  "drywall": {
    "name": "Drywall", "img": "drywall.jpg",
    "kw": "drywall installation and repair",
    "tagline": "Walls so smooth you'll forget they were ever damaged.",
    "intro": "From a doorknob hole to a whole-home hang-and-finish, Build Heritage handles drywall installation, repair, and finishing across Georgia. Level 5 smooth finishes, invisible patches, and texture matching that makes damage disappear.",
    "features": ["New drywall hanging and finishing", "Hole and water-damage repair", "Texture matching (orange peel, knockdown, smooth)", "Ceiling repair and popcorn removal", "Basement and garage finishing", "Paint-ready results — or we paint it too"],
    "body": "Drywall is the skill you only notice when it's done badly. Our finishers tape, mud, and sand to a standard where light from any angle shows a clean, flat wall — the test most patch jobs fail. Water damage from Georgia storms, cracked ceilings, kids-were-kids holes, or a new basement build-out: one crew handles hanging, finishing, texture, and (if you want) primer and paint.",
    "faqs": [("Can you match my existing wall texture?", "Yes — orange peel, knockdown, skip trowel, and smooth finishes. A matched patch should be invisible once painted, and that's the standard we hold."),
             ("How fast can a drywall hole be repaired?", "Small patches are usually same-visit. Larger repairs need a return visit for second coats and sanding — typically finished within 2–3 days."),
             ("Do you remove popcorn ceilings?", "Yes, including containment, removal, refinishing to smooth or light texture, and repainting."),
             ("Do you handle water-damaged drywall?", "Yes — we cut out the damaged sections, address the affected framing surface, and rebuild the wall or ceiling to paint-ready condition.")]
  },
  "flooring": {
    "name": "Flooring & Vinyl", "img": "flooring.jpg",
    "kw": "flooring installation",
    "tagline": "Luxury vinyl, laminate and more — floors built for real life.",
    "intro": "Build Heritage installs luxury vinyl plank (LVP), vinyl tile, and laminate flooring across Georgia homes and businesses. Waterproof, beautiful, and installed with the subfloor prep that makes floors last.",
    "features": ["Luxury vinyl plank (LVP) and tile (LVT)", "Laminate installation", "Subfloor repair and leveling", "Old flooring removal and disposal", "Baseboard and transition finishing", "Residential and commercial"],
    "body": "The secret to a floor that still looks perfect in ten years isn't the plank — it's what's under it. We level, repair and prep subfloors before the first board is clicked, then finish with clean transitions, undercut door jambs, and tight baseboards. LVP has become Georgia's favorite floor for a reason: waterproof, kid-proof, dog-proof, and beautiful. We'll help you choose the right wear layer for how you actually live.",
    "faqs": [("How much does LVP flooring installation cost in Georgia?", "Installed prices typically run $4–$8 per square foot including material, depending on the product line and prep required. Quotes are free and itemized."),
             ("Can vinyl plank go over my existing floor?", "Often yes — over tile, hardwood or vinyl if the surface is flat and sound. We assess this during the free estimate."),
             ("How long does installation take?", "Most single rooms are one day; a whole main floor usually takes 2–4 days including trim work."),
             ("Is LVP really waterproof?", "Quality LVP is fully waterproof from above — ideal for kitchens, baths and basements. We'll steer you to lines with the durability ratings that match the space.")]
  },
  "framing": {
    "name": "Framing", "img": "framing.jpg",
    "kw": "framing contractors",
    "tagline": "Straight, square, and built to code — the bones your project deserves.",
    "intro": "Build Heritage provides structural and finish framing across Georgia: room additions, basement build-outs, wall modifications, garages, decks and repair work — square, plumb, code-compliant, and inspection-ready.",
    "features": ["Room additions and build-outs", "Basement framing", "Load-bearing wall modifications (engineered)", "Garage, porch and deck framing", "Rot and termite damage repair", "Permit-ready, code-compliant work"],
    "body": "Everything that comes after framing — drywall, doors, trim, floors — is only as good as the frame behind it. Our framing is square and plumb, uses correct lumber grades and fasteners, and passes inspection the first time. Opening up a wall between kitchen and living room? We coordinate the engineering, install the proper beam, and leave you with an open plan that's structurally right, not just visually open.",
    "faqs": [("Do I need a permit for framing work in Georgia?", "Structural changes generally require a permit. We handle permit-ready plans and inspections as part of the project."),
             ("Can you remove a load-bearing wall?", "Yes — with proper engineering and beam installation. We coordinate the structural engineering so the opening is safe and legal."),
             ("Do you repair rotted or termite-damaged framing?", "Yes. We remove and replace the damaged members, address the underlying issue with the surface, and restore full structural integrity."),
             ("Do you frame basements for finishing?", "Yes — full basement build-outs including walls, soffits, and blocking, ready for electrical, drywall and flooring.")]
  },
  "doors": {
    "name": "Doors", "img": "doors.jpg",
    "kw": "door installation",
    "tagline": "Entry, interior, patio — doors that close like they mean it.",
    "intro": "Build Heritage installs and replaces entry doors, interior doors, French and patio doors, and barn doors across Georgia. Precise fitting, smooth swings, tight seals — and curb appeal that pays for itself.",
    "features": ["Entry and front door replacement", "Interior door installation", "French, sliding and patio doors", "Barn doors and pocket doors", "Weatherstripping and threshold sealing", "Hardware, locksets and smart locks"],
    "body": "A door is judged in the first second: does it swing smoothly, close with a solid click, seal without daylight? Getting there takes precise shimming, square hanging, and patient adjustment — which is exactly the work most quick installs skip. A new entry door is also one of the highest-ROI improvements a Georgia home can make: instant curb appeal plus real energy savings from a proper seal against summer heat.",
    "faqs": [("How long does a front door replacement take?", "Most entry door replacements are completed in half a day, including hardware, weatherstripping and cleanup."),
             ("Can you replace just the door without the frame?", "Often yes (a slab replacement) if the existing frame is square and sound. We'll tell you honestly which route makes sense."),
             ("Do you install smart locks?", "Yes — we install and configure smart locksets and deadbolts from the major brands as part of any door project."),
             ("My door sticks and won't latch — repair or replace?", "Frequently a repair: hinge adjustment, strike realignment or planing. We fix what can be fixed and only recommend replacement when it's truly warranted.")]
  },
  "window-door-trim": {
    "name": "Window & Door Trim", "img": "trim.jpg",
    "kw": "window and door trim carpentry",
    "tagline": "The details that make a house look finished — and expensive.",
    "intro": "Casings, sills, aprons, and custom moulding: Build Heritage delivers fine finish carpentry for windows and doors across Georgia. Tight miters, clean caulk lines, paint-ready or fully finished.",
    "features": ["Window casing and sill replacement", "Door casing and jamb trim", "Craftsman, colonial and modern profiles", "Rot-resistant PVC and wood options", "Crown moulding and baseboards", "Caulked, filled, paint-ready finish"],
    "body": "Trim is the jewelry of a house. Crisp casings around windows and doors pull a room together in a way furniture never can — and sloppy miters do the opposite. Our finish carpenters cut tight joints, scribe to imperfect walls (every wall is imperfect), and leave surfaces filled, caulked and ready for paint. Exterior trim in Georgia needs to survive humidity: we install rot-resistant materials that keep their lines for decades.",
    "faqs": [("Can you match my home's existing trim profile?", "Yes — we match existing profiles from stock or have knives run for custom historic profiles when needed."),
             ("What trim style suits a Georgia craftsman home?", "Flat craftsman casings with a header cap are the classic choice; we'll bring samples so you can see options against your walls."),
             ("Wood or PVC trim for exteriors?", "For Georgia humidity, cellular PVC outlasts wood dramatically on exteriors and paints beautifully. Interiors are usually poplar or MDF depending on the finish."),
             ("Do you paint the trim after installing it?", "Yes — trim projects can be delivered fully painted, with sprayed finishes available for the smoothest result.")]
  },
  "roofing": {
    "name": "Roofing & Tiles", "img": "roofing.jpg",
    "kw": "roofing services",
    "tagline": "Storm-tested roofs and tile work that protects what matters.",
    "intro": "Build Heritage installs and repairs shingle and tile roofing across Georgia — replacements, storm damage repair, leak diagnosis, and insurance-claim support. Quality materials, clean installs, and warranties we stand behind.",
    "features": ["Full roof replacement", "Shingle and tile installation", "Leak detection and repair", "Storm and hail damage repair", "Insurance claim documentation support", "Gutter and flashing work"],
    "body": "Georgia roofs take a beating: summer sun, hail seasons, and the occasional tropical remnant. We install architectural shingles and tile systems rated for it, with correct underlayment, flashing and ventilation — the three things bad roofers cheat on and good inspectors catch. After storms, we document damage thoroughly for your insurance claim and repair to pre-storm condition or better. Every roof gets a final walkthrough and a written warranty.",
    "faqs": [("How much does a roof replacement cost in Georgia?", "Most single-family replacements fall between $9,000 and $20,000 depending on size, pitch and material. Estimates are free and itemized line by line."),
             ("How do I know if I have hail damage?", "Bruised shingles, granule loss and dented vents are the signs — often invisible from the ground. We provide free inspections with photo documentation you can take to your insurer."),
             ("How long does a roof replacement take?", "Most homes are completed in 1–2 days, including full cleanup and magnetic nail sweep of your yard."),
             ("Do you help with insurance claims?", "Yes — we document damage, meet your adjuster on-site, and provide the scope reports insurers expect. You get a fair claim and a correct roof.")]
  },
}

GOLD = "#C9A24B"; NAVY = "#0A1830"

CSS = """
:root{--navy:#0A1830;--navy2:#122647;--gold:#C9A24B;--gold2:#E3C57E;--cream:#F7F5F0;--ink:#1B2431;--gray:#5A6474;--rule:#E3E0D8}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:#fff;line-height:1.65;font-size:17px}
.sans{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 22px}
a{color:var(--navy)}
/* NAV */
nav{position:sticky;top:0;background:var(--navy);z-index:50;border-bottom:2px solid var(--gold)}
.nav-in{display:flex;align-items:center;justify-content:space-between;height:66px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo svg{height:40px;width:40px}
.logo-t{color:#fff;font-weight:700;font-size:19px;letter-spacing:.04em;white-space:nowrap}
.logo-t b{color:var(--gold2)}
.nav-l{display:flex;gap:26px;align-items:center}
.nav-l a{color:#E8EAF0;text-decoration:none;font-family:Helvetica,sans-serif;font-size:14.5px;letter-spacing:.02em}
.nav-l a:hover{color:var(--gold2)}
.btn{display:inline-block;background:var(--gold);color:var(--navy);font-family:Helvetica,sans-serif;font-weight:700;padding:13px 26px;border-radius:6px;text-decoration:none;font-size:15.5px;letter-spacing:.02em;border:none;cursor:pointer}
.btn:hover{background:var(--gold2)}
.btn.ghost{background:transparent;border:1.5px solid var(--gold);color:var(--gold2)}
/* HERO */
.hero{position:relative;color:#fff;min-height:560px;display:flex;align-items:center;background:var(--navy)}
.hero .bg{position:absolute;inset:0;object-fit:cover;width:100%;height:100%;opacity:.38}
.hero-in{position:relative;padding-top:90px;padding-bottom:90px;max-width:760px}
.kick{font-family:Helvetica,sans-serif;font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold2)}
h1{font-size:clamp(34px,5vw,54px);line-height:1.1;margin:16px 0 18px;font-weight:700}
.hero p{font-size:20px;color:#D9DEE8;max-width:620px}
.hero .cta{margin-top:30px;display:flex;gap:14px;flex-wrap:wrap}
/* TRUST BAR */
.trust{background:var(--navy2);color:#fff;padding:18px 0;border-top:1px solid rgba(201,162,75,.35)}
.trust .wrap{display:flex;gap:34px;justify-content:center;flex-wrap:wrap;font-family:Helvetica,sans-serif;font-size:14px;letter-spacing:.02em}
.trust span{display:flex;align-items:center;gap:8px}
.trust svg{width:17px;height:17px;fill:var(--gold)}
/* SECTIONS */
section{padding:74px 0}
h2{font-size:clamp(27px,3.6vw,38px);line-height:1.15;margin-bottom:14px;color:var(--navy)}
.sub{color:var(--gray);font-size:18.5px;max-width:680px;margin-bottom:40px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.card{background:#fff;border:1px solid var(--rule);border-radius:10px;overflow:hidden;text-decoration:none;color:var(--ink);display:block;transition:transform .15s ease,box-shadow .15s ease}
.card:hover{transform:translateY(-4px);box-shadow:0 16px 34px rgba(10,24,48,.14)}
.card img{width:100%;height:150px;object-fit:cover;display:block}
.card .ci{padding:16px 18px 20px}
.card h3{font-size:18.5px;color:var(--navy);margin-bottom:6px}
.card p{font-family:Helvetica,sans-serif;font-size:13.5px;color:var(--gray);line-height:1.5}
.card .more{font-family:Helvetica,sans-serif;font-size:13px;font-weight:700;color:var(--gold);display:inline-block;margin-top:10px}
.band{background:var(--cream);border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.cols2{display:grid;grid-template-columns:1.05fr .95fr;gap:54px;align-items:center}
.cols2 img{width:100%;border-radius:10px;box-shadow:0 18px 40px rgba(10,24,48,.18)}
.check{list-style:none;margin-top:20px}
.check li{padding-left:32px;position:relative;margin:12px 0;font-size:17px}
.check li:before{content:"";position:absolute;left:0;top:5px;width:18px;height:18px;background:var(--gold);border-radius:50%;}
.check li:after{content:"";position:absolute;left:5px;top:9px;width:8px;height:5px;border-left:2.5px solid var(--navy);border-bottom:2.5px solid var(--navy);transform:rotate(-45deg)}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;margin-top:36px}
.step{background:#fff;border:1px solid var(--rule);border-top:4px solid var(--gold);border-radius:8px;padding:26px}
.step .n{font-family:Helvetica,sans-serif;font-weight:700;color:var(--gold);font-size:14px;letter-spacing:.1em}
.step h3{margin:8px 0 8px;color:var(--navy);font-size:20px}
.step p{color:var(--gray);font-size:15.5px}
/* AREAS */
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.chip{font-family:Helvetica,sans-serif;font-size:14px;background:#fff;border:1px solid var(--rule);border-radius:999px;padding:8px 16px;color:var(--ink)}
a.chip{text-decoration:none}
a.chip:hover{border-color:var(--gold);color:var(--navy)}
/* FAQ */
.faq details{border-bottom:1px solid var(--rule);padding:18px 0}
.faq summary{font-weight:700;font-size:18px;cursor:pointer;color:var(--navy)}
.faq p{margin-top:10px;color:var(--gray)}
/* CONTACT */
.contact-box{background:var(--navy);border-radius:14px;color:#fff;padding:52px;display:grid;grid-template-columns:1fr 1fr;gap:44px}
.contact-box h2{color:#fff}
.contact-box .sub{color:#C6CDDB}
form .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
input,select,textarea{width:100%;padding:13px 14px;border-radius:6px;border:1px solid rgba(255,255,255,.25);background:rgba(255,255,255,.08);color:#fff;font-family:Helvetica,sans-serif;font-size:15px;margin-bottom:12px}
input::placeholder,textarea::placeholder{color:#9AA3B5}
select{color:#fff}
select option{color:#111}
.consent{display:flex;gap:10px;align-items:flex-start;font-size:12.5px;color:#9AA3B5;line-height:1.5;margin-bottom:14px}
.consent input{width:auto;margin:3px 0 0;accent-color:var(--gold)}
.consent a{color:var(--gold2)}
/* FOOTER */
footer{background:var(--navy);color:#B9C1D0;padding:56px 0 34px;border-top:3px solid var(--gold)}
.f-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:34px;font-family:Helvetica,sans-serif;font-size:14px}
.f-grid h4{color:#fff;font-size:15px;margin-bottom:12px}
.f-grid a{color:#B9C1D0;text-decoration:none;display:block;margin:7px 0}
.f-grid a:hover{color:var(--gold2)}
.f-bottom{border-top:1px solid rgba(255,255,255,.12);margin-top:38px;padding-top:20px;font-family:Helvetica,sans-serif;font-size:12.5px;color:#8892A6;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
.f-bottom a{color:#8892A6}
/* SERVICE PAGE */
.page-hero{background:var(--navy);color:#fff;padding:74px 0 60px;position:relative;overflow:hidden}
.page-hero .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.25}
.page-hero .wrap{position:relative}
.page-hero p{color:#D9DEE8;font-size:19.5px;max-width:700px}
.crumb{font-family:Helvetica,sans-serif;font-size:13px;color:#9AA3B5;margin-bottom:14px}
.crumb a{color:#9AA3B5}
.svc-body{display:grid;grid-template-columns:1.5fr .9fr;gap:50px;align-items:start}
.side{background:var(--cream);border:1px solid var(--rule);border-radius:10px;padding:28px;position:sticky;top:90px}
.side h3{color:var(--navy);margin-bottom:8px}
.side p{font-size:15px;color:var(--gray);margin-bottom:16px}
/* LEGAL */
.legal h2{font-size:24px;margin-top:34px}
.legal p,.legal li{color:var(--ink);margin:12px 0;font-size:16px}
.legal ul{padding-left:22px}
/* MOBILE NAV */
.nav-m{display:none;align-items:center;gap:10px}
.burger{background:none;border:1.5px solid var(--gold);color:var(--gold2);border-radius:6px;font-size:19px;line-height:1;padding:8px 12px;cursor:pointer}
.m-menu{display:none;background:var(--navy2);border-top:1px solid rgba(201,162,75,.3)}
body.menu-open .m-menu{display:block}
.m-menu a{display:block;padding:15px 22px;color:#E8EAF0;text-decoration:none;font-family:Helvetica,sans-serif;font-size:15.5px;border-bottom:1px solid rgba(255,255,255,.08)}
.m-menu a:active{background:rgba(201,162,75,.15)}
@media(max-width:900px){
 .grid{grid-template-columns:1fr 1fr}
 .cols2,.contact-box,.svc-body{grid-template-columns:1fr}
 .steps{grid-template-columns:1fr}
 .f-grid{grid-template-columns:1fr 1fr}
 .nav-l{display:none}
 .nav-m{display:flex}
 .side{position:static}
 .hero{min-height:480px}
 .hero-in{padding-top:64px;padding-bottom:64px}
 .contact-box{padding:34px 24px}
 .page-hero{padding:56px 0 46px}
}
@media(max-width:560px){
 .grid{grid-template-columns:1fr}
 .gallery{grid-template-columns:1fr}
 form .row{grid-template-columns:1fr}
 .trust .wrap{gap:12px 22px;font-size:12.5px}
 .btn.big{width:100%;text-align:center}
 .hero .cta{flex-direction:column}
 .hero .cta .btn{width:100%;text-align:center}
 h1{font-size:32px}
 .logo-t{display:none}
}
"""

LOGO_SVG = f"""<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M4 26 24 8l20 18" fill="none" stroke="{GOLD}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/><text x="24" y="38" text-anchor="middle" font-family="Georgia,serif" font-weight="bold" font-size="21" fill="{GOLD}">B<tspan fill="#DDE3EE">H</tspan></text></svg>"""

CHECK_ICON = '<svg viewBox="0 0 24 24"><path d="M12 1 21 5v6c0 5.2-3.8 10-9 12C6.8 21 3 16.2 3 11V5l9-4zm-1.2 14.6 6.4-6.4-1.7-1.7-4.7 4.7-2.3-2.3-1.7 1.7 4 4z"/></svg>'

# ---- published-state helpers ----------------------------------------------

def load_published():
    if os.path.exists(PUBLISHED_FILE):
        return json.load(open(PUBLISHED_FILE))["published"]
    return []

def save_published(pub):
    json.dump({"published": pub}, open(PUBLISHED_FILE, "w"), indent=1)

def live_cities(pub):
    """City slugs with at least one published page, in priority order."""
    have = {c for c, s in pub}
    return [c for c in CITY_PRIORITY if c in have]

def city_pages_for(pub, city):
    return [s for c, s in pub if c == city]

def cities_for_service(pub, svc):
    return [c for c, s in pub if s == svc]

# ---- shared components -----------------------------------------------------

def nav(depth=0):
    p = "../" * depth
    links = "".join(f'<a href="{p}services/{s}.html">{d["name"]}</a>' for s, d in list(SERVICES.items())[:4])
    return f"""<nav><div class="wrap nav-in">
<a class="logo" href="{p}index.html">{LOGO_SVG}<span class="logo-t sans">BUILD <b>HERITAGE</b></span></a>
<div class="nav-l sans"><a href="{p}index.html#services">Services</a><a href="{p}service-areas.html">Service Areas</a><a href="{p}about.html">About</a><a href="{p}index.html#contact" class="btn" style="padding:10px 20px">Free Quote</a></div>
<div class="nav-m sans"><a href="{p}index.html#contact" class="btn" style="padding:9px 14px;font-size:13.5px">Free Quote</a><button class="burger" aria-label="Menu" onclick="document.body.classList.toggle('menu-open')">&#9776;</button></div>
</div>
<div class="m-menu" onclick="document.body.classList.remove('menu-open')">
<a href="{p}index.html#services">All Services</a>
<a href="{p}service-areas.html">Service Areas</a>
<a href="{p}about.html">About Us</a>
<a href="{p}index.html#contact">Get a Free Quote</a>
</div></nav>"""

def trustbar():
    items = ["Licensed & Insured", "Expert Craftsmanship", "On-Time & Reliable", "Satisfaction Guaranteed"]
    return '<div class="trust"><div class="wrap">' + "".join(f"<span>{CHECK_ICON}{i}</span>" for i in items) + "</div></div>"

def footer(depth=0, pub=None):
    p = "../" * depth
    svc = "".join(f'<a href="{p}services/{s}.html">{d["name"]}</a>' for s, d in SERVICES.items())
    lc = live_cities(pub or [])
    area_links = []
    for c in CITIES[:6]:
        slug = c.lower().replace(" ", "-")
        href = f"{p}{slug}/" if slug in lc else f"{p}service-areas.html"
        area_links.append(f'<a href="{href}">{c}</a>')
    return f"""<footer><div class="wrap">
<div class="f-grid">
<div><div class="logo" style="margin-bottom:14px">{LOGO_SVG}<span class="logo-t sans">BUILD <b>HERITAGE</b></span></div>
<p>Built on Quality. Rooted in Trust. Made to Last.<br>Residential &amp; commercial home services across Georgia, USA.</p></div>
<div><h4>Services</h4>{svc}</div>
<div><h4>Top Service Areas</h4>{"".join(area_links)}</div>
<div><h4>Get In Touch</h4><a href="{p}index.html#contact">Request a free quote</a><a href="mailto:{LEAD_EMAIL}">{LEAD_EMAIL}</a><a href="{p}about.html">About us</a></div>
</div>
<div class="f-bottom"><span>© 2026 Build Heritage · buildheritage.org · Serving the State of Georgia</span><span><a href="{p}privacy.html">Privacy Policy</a> · Licensed &amp; Insured · Residential &amp; Commercial</span></div>
</div></footer>"""

def head(title, desc, path, schema_extra=""):
    canonical = f"{BASE_URL}/{path}" if path else BASE_URL + "/"
    biz = {
      "@context": "https://schema.org", "@type": "HomeAndConstructionBusiness",
      "name": "Build Heritage", "url": BASE_URL + "/",
      "slogan": "Built on Quality. Rooted in Trust. Made to Last.",
      "email": LEAD_EMAIL,
      "areaServed": [{"@type": "State", "name": "Georgia"}] + [{"@type": "City", "name": c} for c in CITIES[:10]],
      "priceRange": "$$",
      "knowsAbout": [d["name"] for d in SERVICES.values()]
    }
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
<meta name="robots" content="index, follow">
<link rel="stylesheet" href="{'../' if '/' in path else ''}styles.css">
<link rel="icon" type="image/svg+xml" href='data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" fill="%230A1830"/><path d="M8 26 24 12l16 14" fill="none" stroke="%23C9A24B" stroke-width="3"/><text x="24" y="40" text-anchor="middle" font-family="Georgia" font-weight="bold" font-size="18" fill="%23C9A24B">BH</text></svg>'>
<script type="application/ld+json">{json.dumps(biz)}</script>
{schema_extra}
</head><body>"""

def contact_section():
    opts = "".join(f"<option>{d['name']}</option>" for d in SERVICES.values())
    return f"""<section id="contact"><div class="wrap"><div class="contact-box">
<div><div class="kick">Free, no-pressure quote</div><h2>Tell us about your project.</h2>
<p class="sub">Response within one business day. Every quote is free, written, and itemized — no surprises, no obligation.</p>
<p class="sub" style="margin-bottom:0">Prefer email? <a href="mailto:{LEAD_EMAIL}" style="color:var(--gold2)">{LEAD_EMAIL}</a></p></div>
<form action="https://formsubmit.co/{LEAD_EMAIL}" method="POST">
<input type="hidden" name="_subject" value="New Build Heritage lead"><input type="hidden" name="_captcha" value="false"><input type="hidden" name="_next" value="{BASE_URL}/thanks.html">
<input type="hidden" name="consent_version" value="{CONSENT_VERSION}">
<div class="row"><input name="name" placeholder="Name" required><input name="phone" placeholder="Phone" required></div>
<input name="email" type="email" placeholder="Email" required>
<div class="row"><select name="service" required><option value="" disabled selected>Service needed</option>{opts}</select><input name="city" placeholder="City (e.g. Atlanta)" required></div>
<textarea name="details" rows="4" placeholder="Tell us briefly about the project..."></textarea>
<label class="consent sans"><input type="checkbox" name="consent" value="yes" required>
<span>I agree that Build Heritage and its trusted local service partners may contact me about my project at the phone number and email I provided — by phone call, text message (SMS), or email, including messages sent with automated technology. Message/data rates may apply. Consent is not a condition of purchase, and I can opt out anytime. See our <a href="{BASE_URL}/privacy.html">Privacy Policy</a>.</span></label>
<button class="btn" type="submit" style="width:100%">Get My Free Quote →</button>
</form></div></div></section>"""

# ---- page builders ---------------------------------------------------------

def build_index(pub):
    cards = "".join(
      f"""<a class="card" href="services/{s}.html"><img src="img/{d['img']}" alt="{d['name']} services in Georgia" loading="lazy"><div class="ci"><h3>{d['name']}</h3><p>{d['tagline']}</p><span class="more sans">Learn more →</span></div></a>"""
      for s, d in SERVICES.items())
    lc = live_cities(pub)
    chips = []
    for c in CITIES:
        slug = c.lower().replace(" ", "-")
        if slug in lc:
            chips.append(f'<a class="chip" href="{slug}/">{c}, GA</a>')
        else:
            chips.append(f'<span class="chip">{c}, GA</span>')
    faqs = [
      ("Is Build Heritage licensed and insured?", "Yes — fully licensed and insured for residential and commercial work throughout the State of Georgia."),
      ("Which areas of Georgia do you serve?", "We serve Metro Atlanta and communities across Georgia including Marietta, Alpharetta, Roswell, Sandy Springs, Decatur, and beyond. See our service areas page for the full list."),
      ("Are quotes really free?", "Always. Every estimate is free, written, and itemized line by line, with no obligation."),
      ("Do you handle both residential and commercial projects?", "Yes — homes, apartments, offices, and retail spaces across all eight of our service lines."),
    ]
    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    h = head("Build Heritage — Home Services in Georgia | Moving, Painting, Drywall, Flooring, Framing, Doors, Trim, Roofing",
             "Licensed & insured home services across Georgia: packing & moving, painting, drywall, vinyl flooring, framing, doors, window & door trim, and roofing. Free itemized quotes.",
             "", f'<script type="application/ld+json">{json.dumps(faq_schema)}</script>')
    return h + nav() + f"""
<div class="hero"><img class="bg" src="img/hero.jpg" alt="Beautiful Georgia home served by Build Heritage" fetchpriority="high">
<div class="wrap hero-in"><div class="kick">Residential &amp; Commercial · Georgia, USA</div>
<h1>Built on Quality. Rooted in Trust. Made to Last.</h1>
<p>Eight trades. One accountable team. From moving day to a new roof, Build Heritage delivers licensed, insured craftsmanship across Georgia — on time, on budget, done right.</p>
<div class="cta"><a class="btn" href="#contact">Get a Free Quote</a><a class="btn ghost" href="#services">Explore Services</a></div>
</div></div>
{trustbar()}
<section id="services"><div class="wrap">
<div class="kick">What we do</div><h2>Eight services. One standard.</h2>
<p class="sub">Every crew is licensed, insured, and held to the same promise: craftsmanship you'd show off, schedules you can plan around, and pricing with no asterisks.</p>
<div class="grid">{cards}</div>
</div></section>
<section class="band"><div class="wrap cols2">
<div><div class="kick">Why Build Heritage</div><h2>The contractor Georgia homeowners recommend to family.</h2>
<ul class="check">
<li><b>Licensed &amp; insured</b> — real coverage, verifiable, on every job.</li>
<li><b>One team, eight trades</b> — no juggling five contractors who blame each other.</li>
<li><b>Written, itemized quotes</b> — you approve every line before work starts.</li>
<li><b>On-time or we tell you why</b> — communication is part of craftsmanship.</li>
<li><b>Clean job sites, daily</b> — we work in your home like guests, not tenants.</li>
<li><b>Satisfaction guaranteed</b> — final walkthrough on every project, every time.</li>
</ul></div>
<img src="img/team.jpg" alt="The Build Heritage team — skilled professionals serving Georgia" loading="lazy">
</div></section>
<section><div class="wrap cols2">
<img src="img/consult.jpg" alt="Build Heritage consultation with Georgia homeowners" loading="lazy">
<div><div class="kick">The Build Heritage promise</div><h2>Trust is built before the work starts.</h2>
<p style="margin:14px 0 4px">Inviting someone into your home is an act of trust. Here is exactly what we promise in return — in writing, on every job:</p>
<ul class="check">
<li><b>You'll know who's coming.</b> Named crew, confirmed arrival window, and a call if anything changes.</li>
<li><b>You approve before we build.</b> Written itemized quote, line by line — the price you approve is the price you pay.</li>
<li><b>Your home is protected.</b> Floors covered, furniture wrapped, dust contained, cleanup daily.</li>
<li><b>Nothing is finished until you say so.</b> Every project ends with a walkthrough — and we make it right if it isn't.</li>
</ul></div>
</div></section>
<section><div class="wrap">
<div class="kick">How it works</div><h2>Three steps to done.</h2>
<div class="steps">
<div class="step"><div class="n">STEP 1</div><h3>Tell us the project</h3><p>Two minutes on the form below — or email us. We respond within one business day.</p></div>
<div class="step"><div class="n">STEP 2</div><h3>Free itemized quote</h3><p>We visit, measure, and deliver a written quote you can actually compare — every line explained.</p></div>
<div class="step"><div class="n">STEP 3</div><h3>Done, and done right</h3><p>Licensed crews, protected floors, daily cleanup, and a final walkthrough you sign off on.</p></div>
</div></div></section>
<section class="band"><div class="wrap">
<div class="kick">Where we work</div><h2>Serving Metro Atlanta &amp; communities across Georgia.</h2>
<p class="sub">Based in Georgia, built for Georgia — from in-town Atlanta bungalows to new builds in the suburbs.</p>
<div class="chips sans">{"".join(chips)}</div>
</div></section>
<section><div class="wrap faq" style="max-width:800px">
<div class="kick">Questions</div><h2>Good questions, straight answers.</h2>{faq_html}
</div></section>
{contact_section()}
""" + footer(pub=pub) + "</body></html>"

def build_service(slug, d, pub):
    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faqs"]]}
    svc_schema = {"@context": "https://schema.org", "@type": "Service",
        "name": f"{d['name']} — Georgia", "serviceType": d["name"],
        "provider": {"@type": "HomeAndConstructionBusiness", "name": "Build Heritage", "url": BASE_URL + "/"},
        "areaServed": {"@type": "State", "name": "Georgia"}}
    extra = f'<script type="application/ld+json">{json.dumps(faq_schema)}</script><script type="application/ld+json">{json.dumps(svc_schema)}</script>'
    feats = "".join(f"<li>{f}</li>" for f in d["features"])
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in d["faqs"])
    others = "".join(f'<a href="{s}.html" class="chip">{sd["name"]}</a>' for s, sd in SERVICES.items() if s != slug)
    city_links = "".join(f'<a class="chip" href="../{c}/{slug}.html">{CITY_INFO[c]["name"]}</a>'
                         for c in cities_for_service(pub, slug))
    city_block = (f'<p style="margin-top:18px;margin-bottom:8px"><b>{d["name"]} near you:</b></p><div class="chips sans">{city_links}</div>'
                  if city_links else "")
    h = head(f"{d['name']} in Georgia | Build Heritage — Licensed & Insured",
             f"Professional {d['kw']} across Georgia. {d['tagline']} Licensed & insured, free itemized quotes from Build Heritage.",
             f"services/{slug}.html", extra)
    return h + nav(depth=1) + f"""
<div class="page-hero"><img class="bg" src="../img/{d['img']}" alt="">
<div class="wrap"><div class="crumb sans"><a href="../index.html">Home</a> / <a href="../index.html#services">Services</a> / {d['name']}</div>
<div class="kick">Licensed &amp; insured · Georgia, USA</div>
<h1>{d['name']} in Georgia</h1>
<p>{d['tagline']}</p>
<div class="cta" style="margin-top:26px"><a class="btn" href="../index.html#contact">Get a Free Quote</a></div>
</div></div>
{trustbar()}
<section><div class="wrap svc-body">
<div>
<h2>Professional {d['name'].lower()}, done the Build Heritage way.</h2>
<p style="font-size:18px;margin:16px 0">{d['intro']}</p>
<img src="../img/{d['img']}" alt="{d['name']} services by Build Heritage in Georgia" style="width:100%;border-radius:10px;margin:22px 0" loading="lazy">
<p style="margin-bottom:26px">{d['body']}</p>
<h2 style="font-size:26px">What's included</h2>
<ul class="check">{feats}</ul>
<div class="faq" style="margin-top:44px"><h2 style="font-size:26px">Frequently asked questions</h2>{faq_html}</div>
</div>
<aside class="side">
<h3>Free {d['name']} Quote</h3>
<p>Written, itemized, no obligation. Serving Metro Atlanta and all of Georgia.</p>
<a class="btn" href="../index.html#contact" style="width:100%;text-align:center;display:block">Request Quote →</a>
{city_block}
<p style="margin-top:18px;margin-bottom:8px"><b>Also need:</b></p>
<div class="chips sans">{others}</div>
</aside>
</div></section>
""" + footer(depth=1, pub=pub) + "</body></html>"

def build_city_service(city, slug, pub):
    d = SERVICES[slug]; ci = CITY_INFO[city]
    cname = ci["name"]; hood = ci["hoods"][0]
    local = SVC_LOCAL[slug].format(city=cname, county=ci["county"], hood=hood)
    faqs = list(d["faqs"][:2]) + [
        (f"Do you serve {cname}, GA?",
         f"Yes — {cname} is one of our core service areas. Our crews work throughout {ci['county']}, including {', '.join(ci['hoods'][:3])}, with the same licensed, insured standard on every job."),
        (f"How do I get a {d['name'].lower()} quote in {cname}?",
         f"Use the free-quote form on this site or email {LEAD_EMAIL}. We respond within one business day and every {cname} quote is free, written, and itemized line by line."),
    ]
    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    svc_schema = {"@context": "https://schema.org", "@type": "Service",
        "name": f"{d['name']} — {cname}, GA", "serviceType": d["name"],
        "provider": {"@type": "HomeAndConstructionBusiness", "name": "Build Heritage", "url": BASE_URL + "/"},
        "areaServed": {"@type": "City", "name": cname, "containedInPlace": {"@type": "State", "name": "Georgia"}}}
    extra = f'<script type="application/ld+json">{json.dumps(faq_schema)}</script><script type="application/ld+json">{json.dumps(svc_schema)}</script>'
    feats = "".join(f"<li>{f}</li>" for f in d["features"])
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    sibling_svcs = "".join(f'<a href="{s}.html" class="chip">{SERVICES[s]["name"]}</a>'
                           for s in city_pages_for(pub, city) if s != slug)
    sibling_block = (f'<p style="margin-top:18px;margin-bottom:8px"><b>Also in {cname}:</b></p><div class="chips sans">{sibling_svcs}</div>'
                     if sibling_svcs else "")
    hoods = "".join(f'<span class="chip">{h}</span>' for h in ci["hoods"])
    h = head(f"{d['name']} in {cname}, GA | Build Heritage — Licensed & Insured",
             f"Professional {d['kw']} in {cname}, Georgia. {d['tagline']} Licensed & insured, free itemized quotes. Serving {', '.join(ci['hoods'][:3])} and all of {ci['county']}.",
             f"{city}/{slug}.html", extra)
    return h + nav(depth=1) + f"""
<div class="page-hero"><img class="bg" src="../img/{d['img']}" alt="">
<div class="wrap"><div class="crumb sans"><a href="../index.html">Home</a> / <a href="index.html">{cname}</a> / {d['name']}</div>
<div class="kick">Licensed &amp; insured · {cname}, {ci['county']}, Georgia</div>
<h1>{d['name']} in {cname}, GA</h1>
<p>{d['tagline']}</p>
<div class="cta" style="margin-top:26px"><a class="btn" href="../index.html#contact">Get a Free {cname} Quote</a></div>
</div></div>
{trustbar()}
<section><div class="wrap svc-body">
<div>
<h2>{d['name']} for {cname} homes, done the Build Heritage way.</h2>
<p style="font-size:18px;margin:16px 0">{ci['blurb']}</p>
<p style="margin-bottom:10px">{local}</p>
<img src="../img/{d['img']}" alt="{d['name']} services by Build Heritage in {cname}, Georgia" style="width:100%;border-radius:10px;margin:22px 0" loading="lazy">
<p style="margin-bottom:26px">{d['body']}</p>
<h2 style="font-size:26px">What's included</h2>
<ul class="check">{feats}</ul>
<h2 style="font-size:26px;margin-top:40px">{cname} areas we serve</h2>
<div class="chips sans">{hoods}<span class="chip">…and all of {ci['county']}</span></div>
<div class="faq" style="margin-top:44px"><h2 style="font-size:26px">Frequently asked questions</h2>{faq_html}</div>
</div>
<aside class="side">
<h3>Free {cname} {d['name']} Quote</h3>
<p>Written, itemized, no obligation. Serving {cname} and all of {ci['county']}.</p>
<a class="btn" href="../index.html#contact" style="width:100%;text-align:center;display:block">Request Quote →</a>
{sibling_block}
<p style="margin-top:18px;margin-bottom:8px"><b>Statewide:</b></p>
<div class="chips sans"><a class="chip" href="../services/{slug}.html">{d['name']} across Georgia</a><a class="chip" href="index.html">All {cname} services</a></div>
</aside>
</div></section>
""" + footer(depth=1, pub=pub) + "</body></html>"

def build_city_hub(city, pub):
    ci = CITY_INFO[city]; cname = ci["name"]
    live = city_pages_for(pub, city)
    cards = "".join(
      f"""<a class="card" href="{s}.html"><img src="../img/{SERVICES[s]['img']}" alt="{SERVICES[s]['name']} in {cname}, GA" loading="lazy"><div class="ci"><h3>{SERVICES[s]['name']}</h3><p>{SERVICES[s]['tagline']}</p><span class="more sans">{SERVICES[s]['name']} in {cname} →</span></div></a>"""
      for s in live)
    hoods = "".join(f'<span class="chip">{h}</span>' for h in ci["hoods"])
    other = "".join(f'<a class="chip" href="../services/{s}.html">{d["name"]}</a>' for s, d in SERVICES.items() if s not in live)
    other_block = (f'<h2 style="margin-top:54px">More services available in {cname}</h2><p class="sub">Dedicated {cname} pages are coming for these — but the crews already serve {cname} today:</p><div class="chips sans">{other}</div>' if other else "")
    h = head(f"Home Services in {cname}, GA | Build Heritage — Licensed & Insured",
             f"Build Heritage serves {cname}, Georgia with licensed & insured home services: roofing, painting, flooring, drywall, moving and more. Serving {', '.join(ci['hoods'][:3])} and all of {ci['county']}. Free itemized quotes.",
             f"{city}/")
    return h + nav(depth=1) + f"""
<div class="page-hero"><img class="bg" src="../img/hero.jpg" alt="">
<div class="wrap"><div class="crumb sans"><a href="../index.html">Home</a> / <a href="../service-areas.html">Service Areas</a> / {cname}</div>
<div class="kick">Licensed &amp; insured · {ci['county']}, Georgia</div>
<h1>Home Services in {cname}, GA</h1>
<p>{ci['blurb']}</p>
<div class="cta" style="margin-top:26px"><a class="btn" href="../index.html#contact">Get a Free {cname} Quote</a></div>
</div></div>
{trustbar()}
<section><div class="wrap">
<div class="kick">What we do in {cname}</div><h2>Services for {cname} homes &amp; businesses.</h2>
<div class="grid">{cards}</div>
{other_block}
<h2 style="margin-top:54px">{cname} neighborhoods we serve</h2>
<div class="chips sans">{hoods}<span class="chip">…and all of {ci['county']}</span></div>
</div></section>
""" + footer(depth=1, pub=pub) + "</body></html>"

def build_areas(pub):
    lc = live_cities(pub)
    chips = []
    for c in CITIES:
        slug = c.lower().replace(" ", "-")
        if slug in lc:
            chips.append(f'<a class="chip" href="{slug}/"><b>{c}, GA</b></a>')
        else:
            chips.append(f'<span class="chip">{c}, GA</span>')
    svc_links = "".join(f'<a class="chip" href="services/{s}.html">{d["name"]}</a>' for s, d in SERVICES.items())
    h = head("Service Areas — Build Heritage | Home Services Across Georgia",
             "Build Heritage serves Metro Atlanta and communities across Georgia: Atlanta, Marietta, Alpharetta, Roswell, Sandy Springs, Decatur and more. Licensed & insured.",
             "service-areas.html")
    return h + nav() + f"""
<div class="page-hero"><div class="wrap">
<div class="kick">Where we work</div><h1>Serving Georgia, one community at a time.</h1>
<p>Starting with Metro Atlanta and expanding across the state — if you're in Georgia, chances are we're already working in your neighborhood.</p>
</div></div>
{trustbar()}
<section><div class="wrap">
<h2>Communities we serve</h2>
<p class="sub">Don't see your city? If you're in Georgia, ask — the answer is usually yes. Bold cities have dedicated local pages.</p>
<div class="chips sans">{"".join(chips)}</div>
<h2 style="margin-top:54px">Every service, every area</h2>
<div class="chips sans">{svc_links}</div>
</div></section>
{contact_section()}
""" + footer(pub=pub) + "</body></html>"

def build_about(pub):
    h = head("About Build Heritage | Licensed Georgia Home Services Company",
             "Build Heritage is a licensed & insured Georgia home services company: one accountable team across eight trades. Built on quality. Rooted in trust. Made to last.",
             "about.html")
    return h + nav() + f"""
<div class="page-hero"><div class="wrap">
<div class="kick">Our story</div><h1>Built on Quality. Rooted in Trust. Made to Last.</h1>
<p>Those aren't just words on our logo — they're the three tests every project has to pass before we call it finished.</p>
</div></div>
{trustbar()}
<section><div class="wrap" style="max-width:800px">
<h2>One team. Eight trades. Zero excuses.</h2>
<p style="margin:16px 0">Most home projects fail in the gaps between contractors — the painter blames the drywaller, the flooring guy blames the framer, and the homeowner pays for it. Build Heritage was created to close those gaps: one licensed, insured, accountable team covering the eight trades a home actually needs, from moving day to the roof over your head.</p>
<p style="margin:16px 0"><b>Quality</b> means crews who take pride in the parts you'll never see — the prep, the fasteners, the flashing. <b>Trust</b> means written itemized quotes, honest recommendations (including "you don't need this"), and job sites left cleaner than we found them. <b>Made to last</b> means materials chosen for Georgia's climate and workmanship we're happy to stand behind.</p>
<p style="margin:16px 0">We're starting where we live — Georgia — and earning our reputation one home, one business, one referral at a time.</p>
<img src="img/team.jpg" alt="The Build Heritage crew — a team as diverse as the communities we serve" style="width:100%;border-radius:10px;margin:26px 0 8px" loading="lazy">
<p style="margin:16px 0;color:var(--gray);font-size:15.5px;font-family:Helvetica,sans-serif">Our crews look like Georgia: skilled professionals from every background, held to one standard of craftsmanship — and one promise to every client we serve.</p>
<div class="cta" style="margin-top:30px"><a class="btn" href="index.html#contact">Work With Us →</a></div>
</div></section>
{contact_section()}
""" + footer(pub=pub) + "</body></html>"

def build_privacy(pub):
    h = head("Privacy Policy — Build Heritage",
             "How Build Heritage collects, uses, and shares the information you submit when requesting a quote.",
             "privacy.html")
    return h + nav() + f"""
<div class="page-hero"><div class="wrap">
<div class="kick">Legal</div><h1>Privacy Policy</h1>
<p>Effective August 15, 2026 · Applies to buildheritage.org</p>
</div></div>
<section><div class="wrap legal" style="max-width:800px">
<p><b>Who we are.</b> Build Heritage ("we," "us") is a Georgia home-services business reachable at <a href="mailto:{LEAD_EMAIL}">{LEAD_EMAIL}</a>. This policy explains what happens to the information you submit on this site.</p>
<h2>What we collect</h2>
<p>When you request a quote we collect what you type into the form: your name, phone number, email address, city, the service you need, and any project details you share. We do not ask for — and you should not submit — payment details, government IDs, or other sensitive personal information. This site does not use tracking cookies.</p>
<h2>How we use it</h2>
<ul>
<li>To respond to your request, prepare quotes, and schedule work.</li>
<li>To contact you about your project by phone, text (SMS), or email — including with automated technology if you gave that consent on the form.</li>
</ul>
<h2>Sharing with service partners</h2>
<p>To make sure your project gets handled, we may share — including for compensation — your quote request (name, contact information, city, and project details) with a limited number of <b>trusted local service partners</b>: licensed home-services businesses able to perform the work you requested. Partners who receive your request may contact you directly about that project. We do not sell your information to data brokers or for marketing unrelated to your home-services request.</p>
<h2>Your choices</h2>
<ul>
<li><b>Opt out anytime:</b> email <a href="mailto:{LEAD_EMAIL}">{LEAD_EMAIL}</a> with "opt out" and we will stop contact and stop sharing your details, and will pass the request to any partner we shared them with.</li>
<li><b>Texts:</b> reply STOP to any SMS to end text contact. Message and data rates may apply.</li>
<li><b>Access/deletion:</b> email us to ask what we hold about you or to have it deleted.</li>
</ul>
<h2>Retention &amp; security</h2>
<p>Quote requests are delivered to our business email and retained only as long as needed to serve you and to keep records of consent. We limit access to the people who need it to respond to you.</p>
<h2>Children</h2>
<p>This site is for adults arranging home services and is not directed at children under 13; we do not knowingly collect their information.</p>
<h2>Changes</h2>
<p>If this policy changes, the new version will be posted here with a new effective date. Questions: <a href="mailto:{LEAD_EMAIL}">{LEAD_EMAIL}</a>.</p>
</div></section>
""" + footer(pub=pub) + "</body></html>"

def build_thanks(pub):
    h = head("Thank You — Build Heritage", "Your quote request was received. We'll be in touch within one business day.", "thanks.html")
    return h + nav() + """
<section style="min-height:50vh;display:flex;align-items:center"><div class="wrap" style="text-align:center;max-width:640px">
<div class="kick">Request received</div><h1 style="color:var(--navy)">Thank you — we're on it.</h1>
<p class="sub" style="margin:18px auto">Your project details are in our inbox. Expect a response within one business day with next steps for your free, itemized quote.</p>
<a class="btn" href="index.html">Back to Home</a>
</div></section>
""" + footer(pub=pub) + "</body></html>"

def build_sitemap(pub):
    urls = [""] + [f"services/{s}.html" for s in SERVICES] + ["service-areas.html", "about.html", "privacy.html"]
    urls += [f"{c}/" for c in live_cities(pub)]
    urls += [f"{c}/{s}.html" for c, s in pub]
    items = "".join(f"<url><loc>{BASE_URL}/{u}</loc><changefreq>weekly</changefreq></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>'

# ---- main ------------------------------------------------------------------

def generate_all(pub):
    os.makedirs(f"{OUT}/services", exist_ok=True)
    os.makedirs(f"{OUT}/img", exist_ok=True)
    open(f"{OUT}/styles.css", "w").write(CSS)
    open(f"{OUT}/index.html", "w").write(build_index(pub))
    for slug, d in SERVICES.items():
        open(f"{OUT}/services/{slug}.html", "w").write(build_service(slug, d, pub))
    for city in live_cities(pub):
        os.makedirs(f"{OUT}/{city}", exist_ok=True)
        open(f"{OUT}/{city}/index.html", "w").write(build_city_hub(city, pub))
        for s in city_pages_for(pub, city):
            open(f"{OUT}/{city}/{s}.html", "w").write(build_city_service(city, s, pub))
    open(f"{OUT}/service-areas.html", "w").write(build_areas(pub))
    open(f"{OUT}/about.html", "w").write(build_about(pub))
    open(f"{OUT}/privacy.html", "w").write(build_privacy(pub))
    open(f"{OUT}/thanks.html", "w").write(build_thanks(pub))
    open(f"{OUT}/sitemap.xml", "w").write(build_sitemap(pub))
    open(f"{OUT}/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    open(f"{OUT}/{INDEXNOW_KEY}.txt", "w").write(INDEXNOW_KEY)
    open(f"{OUT}/.nojekyll", "w").write("")
    open(f"{OUT}/404.html", "w").write(build_thanks(pub).replace("Thank you — we're on it.", "Page not found.").replace("Your project details are in our inbox. Expect a response within one business day with next steps for your free, itemized quote.", "That page doesn't exist — but our services do."))
    n = len(SERVICES) + 7 + len(pub) + len(live_cities(pub))
    print(f"Generated {n} pages ({len(pub)} city pages live, {len(QUEUE) - len(pub)} still queued)")

if __name__ == "__main__":
    n = 0
    if "--publish-next" in sys.argv:
        i = sys.argv.index("--publish-next")
        n = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 and sys.argv[i + 1].isdigit() else 3
    pub = [tuple(x) for x in load_published()]
    before_cities = set(live_cities(pub))
    new = []
    for item in QUEUE:
        if len(new) >= n:
            break
        if item not in pub:
            pub.append(item); new.append(item)
    if new:
        save_published([list(x) for x in pub])
    generate_all(pub)
    for c, s in new:
        print(f"NEWURL {BASE_URL}/{c}/{s}.html")
    for c in set(live_cities(pub)) - before_cities:
        print(f"NEWURL {BASE_URL}/{c}/")
