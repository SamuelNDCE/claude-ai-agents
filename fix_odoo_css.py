#!/usr/bin/env python3
"""
Fix for perpetualtechnologies.odoo.com:
Removes raw CSS text accidentally placed in the page body,
then adds it properly to the website's custom head CSS.

Usage:
  1. Fill in USERNAME and PASSWORD below
  2. Run:  python fix_odoo_css.py
"""
import xmlrpc.client
import sys

URL      = "https://perpetualtechnologies.odoo.com"
DB       = "perpetualtechnologies"
USERNAME = "Samuelndce@gmail.com"    # <-- fill in your Odoo admin email
PASSWORD = "Pass98!Chatgpt" # <-- fill in your Odoo admin password

# The CSS that should be in the head, not on the page body
THE_CSS = """\
:root {
  --pt-dark:    #0a0d18;
  --pt-surface: #111827;
  --pt-purple:  #7c3aed;
  --pt-teal:    #22d3ee;
}

/* NAV BACKGROUND */
#top, header, .navbar, header.o_header_standard,
nav.navbar {
  background: #0a0d18 !important;
  border-bottom: 1px solid #1e2640 !important;
}

/* STRIP BACKGROUNDS FROM ALL HEADER CHILDREN */
#top *, #top *::before, #top *::after,
header *, header *::before, header *::after,
.navbar *, .navbar *::before, .navbar *::after {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  border-color: transparent !important;
}

/* ALL NAV TEXT: BRIGHT WHITE */
header a, header span, header li,
header .nav-link, header .nav-item,
header p, header div,
.navbar a, .navbar span, .navbar li,
.navbar .nav-link, .navbar-nav .nav-link,
.navbar-nav > li > a,
#top a, #top span, #top li {
  color: #ffffff !important;
  font-family: 'Rajdhani', sans-serif !important;
  font-weight: 600 !important;
  font-size: .85rem !important;
  letter-spacing: .07em !important;
  text-transform: uppercase !important;
  text-shadow: none !important;
}

/* HOVER */
header a:hover, .navbar a:hover,
.navbar-nav .nav-link:hover {
  color: #22d3ee !important;
}

/* LOGO */
header .o_logo, header .navbar-brand,
header [class*="logo"], .navbar-brand {
  display: flex !important;
  align-items: center !important;
  padding: 0 !important;
}
header .o_logo img, header .navbar-brand img,
header [class*="logo"] img, .navbar-brand img {
  height: 48px !important;
  width: auto !important;
  max-width: 200px !important;
  min-width: 80px !important;
  object-fit: contain !important;
  opacity: 1 !important;
  visibility: visible !important;
  display: block !important;
  filter: brightness(1.2) contrast(1.1) !important;
}

/* APPOINTMENT PILL */
header a[href*="appointment"], .navbar a[href*="appointment"] {
  background: #22d3ee !important;
  color: #0a0d18 !important;
  border-radius: 4px !important;
  padding: .35rem 1rem !important;
  font-weight: 700 !important;
}

/* CONTACT BUTTON */
header a[href*="contactus"], header a[href*="contact-us"],
.navbar a[href*="contactus"] {
  background: #7c3aed !important;
  color: #ffffff !important;
  border-radius: 4px !important;
  padding: .35rem 1.1rem !important;
  font-weight: 700 !important;
}

/* DROPDOWN */
.dropdown-menu {
  background: #111827 !important;
  border: 1px solid #1e2640 !important;
}
.dropdown-item {
  color: #ffffff !important;
  background: transparent !important;
}
.dropdown-item:hover {
  background: rgba(124,58,237,.2) !important;
  color: #22d3ee !important;
}

/* HERO */
.o_hero, section.o_hero, .o_home_cover,
.s_cover, section.s_cover, .s_hero, section.s_hero {
  background: linear-gradient(135deg, #0a0d18 0%, #0d1b3e 50%, #0a0d18 100%) !important;
  color: #f1f5f9 !important;
  min-height: 88vh !important;
}
.o_hero *, .o_home_cover *, .s_cover *, .s_hero * { color: #f1f5f9 !important; }

/* LIGHT CONTENT SECTIONS */
.o_editable section, section.s_text_block,
section.s_three_columns, section.s_features,
section.s_image_text, section.s_tabs {
  background: #ffffff !important;
  color: #1e293b !important;
}

/* FOOTER */
footer, #footer {
  background: #0a0d18 !important;
  color: #64748b !important;
  border-top: 1px solid #1e2640 !important;
}
footer a, footer p, footer span { color: #64748b !important; }
footer a:hover { color: #22d3ee !important; }

/* BUTTONS */
.btn-primary, .o_btn_primary {
  background: #7c3aed !important;
  border-color: #7c3aed !important;
  color: #fff !important;
  border-radius: 4px !important;
  font-family: 'Rajdhani', sans-serif !important;
  font-weight: 700 !important;
}
.btn-primary:hover { background: #6d28d9 !important; }
.btn-secondary, .o_btn_secondary {
  background: transparent !important;
  border: 1.5px solid #22d3ee !important;
  color: #22d3ee !important;
  border-radius: 4px !important;
}

/* MOBILE */
@media(max-width:991px){
  .navbar-collapse {
    background: #0a0d18 !important;
    padding: 1rem !important;
  }
  .navbar-toggler-icon { filter: invert(1) !important; }
}
"""

CSS_MARKER = "--pt-dark"


def connect():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        print("Authentication failed. Check your email, password, and DB name.")
        print(f"  DB tried: {DB}")
        sys.exit(1)
    print(f"Connected as UID {uid}")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    return uid, models


def remove_css_from_views(uid, models):
    """Find ir.ui.view records that contain the raw CSS text and remove it."""
    views = models.execute_kw(DB, uid, PASSWORD, "ir.ui.view", "search_read",
        [[["arch_db", "ilike", CSS_MARKER]]],
        {"fields": ["id", "name", "arch_db", "key"]}
    )

    if not views:
        print("No views found with raw CSS text (already fixed, or stored differently).")
        return

    print(f"Found {len(views)} view(s) containing raw CSS:")
    for view in views:
        print(f"  ID={view['id']}  key={view['key']}  name={view['name']}")
        arch = view["arch_db"]

        # The CSS block starts at ":root {" and ends with trailing newlines
        marker = ":root {"
        if marker not in arch:
            print(f"    Skipping: marker not found in expected position")
            continue

        start = arch.find(marker)

        # Find the end: last closing brace of the @media block + trailing whitespace
        # The CSS ends with "}\n}\n\n\n" from the @media rule
        end = arch.rfind("}")
        if end == -1 or end < start:
            print(f"    Skipping: could not find end of CSS block")
            continue
        end += 1  # include the closing brace

        # Skip any trailing whitespace/newlines after the CSS
        while end < len(arch) and arch[end] in " \t\r\n":
            end += 1

        cleaned_arch = arch[:start] + arch[end:]
        models.execute_kw(DB, uid, PASSWORD, "ir.ui.view", "write",
            [[view["id"]], {"arch_db": cleaned_arch}]
        )
        print(f"    CSS text removed from view {view['id']}")


def add_css_to_website_head(uid, models):
    """Add the CSS properly to website.custom_code_head (rendered in <head>)."""
    websites = models.execute_kw(DB, uid, PASSWORD, "website", "search_read",
        [[]],
        {"fields": ["id", "name", "custom_code_head"]}
    )

    for site in websites:
        existing = site.get("custom_code_head") or ""
        if CSS_MARKER in existing:
            print(f"CSS already present in website '{site['name']}' head — skipping.")
            continue
        new_head = existing + f"\n<style>\n{THE_CSS}\n</style>\n"
        models.execute_kw(DB, uid, PASSWORD, "website", "write",
            [[site["id"]], {"custom_code_head": new_head}]
        )
        print(f"CSS added to website '{site['name']}' custom head.")


def main():
    print("=== PerpetualTechnologies Odoo CSS Fix ===\n")
    uid, models = connect()
    remove_css_from_views(uid, models)
    add_css_to_website_head(uid, models)
    print("\nDone! Hard-refresh your website (Ctrl+Shift+R) to verify the fix.")


if __name__ == "__main__":
    main()
