#!/usr/bin/env python3

if __name__ == '__main__':
    import sys
    import os

    try:
        import elaphure
    except ImportError:
        ROOT=os.path.dirname(os.path.abspath(__file__))
        sys.path.append(os.path.dirname(ROOT)+"/elaphure")

    import elaphure.__main__


def source_link(collection, prob):
    if collection == 'leetcode':
        return f'https://leetcode.com/problems/{prob}/'
    elif collection == 'AOJ':
        return f"http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id={prob}"
    assert False

def wiki(filename, meta):
    slug = meta.get("slug", [filename[5:-3]])[0]
    title = meta.get("title", [slug])[0]

    if slug.startswith("online-judge/AOJ/"):
        title = slug.rsplit("/", 1)[1] + ": " + title

    meta = {
        "type": "wiki",
        "title": title,
        "tags": meta.get("tag", []),
        "slug": slug}

    if slug.startswith("online-judge/"):
        if "/" in slug[13:]:
            meta["source"] = source_link(*slug[13:].split('/', 1))

    return meta


def article(filename, meta):
    slug = meta.get("slug", [filename[9:-3]])[0]

    return {"type": "article",
            "title": meta.get("title", [slug])[0],
            "date": meta.get("date", [None])[0],
            "tags": meta.get("tag", []),
            "slug": slug}

def css(filename, meta):
    return {
        'type': 'css',
        'slug': filename[7:-4],
    }

SOURCE_FILES = [
    ("wiki/**/*.md", 'markdown', wiki),
    ("articles/**/*.md", 'markdown', article),
    ("static/*.css", 'wheezy', css)
]

URLS = [
    Rule('/',
         defaults={'type': 'article', 'page': 1},
         endpoint='article_list'),
    Rule('/page<int:page>.html',
         defaults={'type': 'article'},
         endpoint='article_list'),
    Rule('/<int(fixed_digits=4):date__year>/',
         defaults={'type': 'article'},
         endpoint='article_list_by_year'),
    Rule('/<int(fixed_digits=4):date__year>/<int(fixed_digits=2):date__month>/',
         defaults={'type': 'article'},
         endpoint='article_list_by_month'),
    Rule('/<int(fixed_digits=4):date__year>/<int(fixed_digits=2):date__month>/<slug>.html',
         defaults={'type': 'article'},
         endpoint='article'),
    Rule('/wiki/<path:slug>.html',
         defaults={'type': 'wiki'},
         endpoint='wiki'),
    Rule(
        '/static/<slug>.css',
        defaults={'type': 'css'},
        endpoint='css')
]


class views(config):
    article_list = EntryListView(template_name='templates/article_list.html', paginate_by=10, ordering='-date')
    article_list_by_year = EntryListView(template_name='templates/article_list.html', ordering='-date')
    article_list_by_month = EntryListView(template_name='templates/article_list.html', ordering='-date')
    article = EntryView(template_name='templates/article.html')
    wiki = EntryView(template_name='templates/wiki.html')
    css = RawEntryView(mimetype='text/css')


def build_link(target, text=None):
    if target.startswith("/"):
        url = urls.current_url()
        _, values = urls.match(url)
        if values["type"] != 'wiki':
            warn(f"{url!r} not wiki")
            return None, text or target, False
        target = values['slug'] + '/' + target[1:]

    url = urls.build('wiki', {'slug': target})

    entries = db.select('''
SELECT source.*
FROM source
WHERE json_extract(source.metadata, '$.type') = 'wiki'
AND json_extract(source.metadata, '$.slug') = {}
''', target)

    entry = None

    if not entries:
        warn(f"wiki {target!r} not found")
    else:
        entry = entries[0]

    if text is None:
        if entry is None:
            text = target
        else:
            text = entry["title"]

    return url, text, entry is not None

from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree

class WikiLinkExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        self.md = md
        WIKILINK_RE = r'\[\[(?P<target>[/@\w/0-9:_ -]+)(?P<text>(?:\|[\w/0-9:_ -]+)?)\]\]'
        pattern = WikiLinks(WIKILINK_RE)
        pattern.md = md
        md.inlinePatterns.add('wikilink', pattern, "<not_strong")


class WikiLinks(Pattern):

    def handleMatch(self, m):
        target = m.group("target")
        text = m.group("text")
        text = text[1:] if text else None
        url, text, exist = build_link(target, text)
        if exist:
            a = etree.Element('a')
            a.text = text
            a.set('href', url)
            return a
        else:
            span = etree.Element('span')
            span.text = text
            span.set("class", "new")
            return span

class readers(config):
    markdown = MarkdownReader(
        extensions=
        [ 'meta',
          'codehilite',
          'footnotes',
          WikiLinkExtension(),
        ],
        extension_configs={
            'codehilite': {'linenums': True}
        }
    )


SITENAME = "21天劝退计算机"

MENUITEMS = [
    ("日志", "article_list", {}),
    ("Wiki", "wiki", {"slug": "index"})
]
