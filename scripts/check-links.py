#!/usr/bin/env python3
"""Checks internal links in a built Hugo site.

Usage: check-links.py PUBLIC_DIR BASE_URL
Every href/src inside the site and every sitemap <loc> must resolve to a
file, and a #fragment must exist as an id on the target page. Prints the
broken links and exits 1 if there are any.
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])


def target_file(public, path):
    p = os.path.join(public, unquote(path).lstrip("/"))
    if path.endswith("/") or os.path.isdir(p):
        p = os.path.join(p, "index.html")
    return os.path.normpath(p)


def main(public, base):
    host = urlparse(base).netloc
    pages, broken, checked = {}, [], 0
    for root, _, files in os.walk(public):
        for name in files:
            if name.endswith(".html"):
                path = os.path.normpath(os.path.join(root, name))
                parser = Page()
                with open(path, encoding="utf-8") as f:
                    parser.feed(f.read())
                pages[path] = parser
    sources = [(p, "/" + os.path.relpath(p, public).replace(os.sep, "/"), parser.links)
               for p, parser in pages.items()]
    for root, _, files in os.walk(public):
        for name in files:
            if name.endswith(".xml") and "sitemap" in name:
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as f:
                    locs = re.findall(r"<loc>([^<]+)</loc>", f.read())
                sources.append((path, "/" + os.path.relpath(path, public), locs))
    for _, page_url, links in sources:
        for link in links:
            u = urlparse(urljoin(base.rstrip("/") + page_url, link))
            if u.scheme not in ("http", "https") or u.netloc != host:
                continue
            checked += 1
            f = target_file(public, u.path)
            if not os.path.exists(f):
                broken.append((page_url, link, "missing"))
            elif u.fragment and f in pages and u.fragment not in pages[f].ids:
                broken.append((page_url, link, "no id " + u.fragment))
    for b in broken:
        print("BROKEN %s -> %s (%s)" % b)
    print("%d pages, %d links checked, %d broken" % (len(pages), checked, len(broken)))
    return 1 if broken else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
