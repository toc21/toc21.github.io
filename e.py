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


def page(filename, meta):
    slug = meta.get("slug", [filename[6:-3]])[0]
    return {"type": "page",
            "title": meta.get("title", [slug])[0],
            "tags": meta.get("tag", []),
            "slug": slug}


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
    ("pages/*.md", 'markdown', page),
    ("articles/*.md", 'markdown', article),
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
    Rule('/<slug>.html',
         defaults={'type': 'page'},
         endpoint='page'),
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
    page = EntryView(template_name='templates/page.html')
    css = RawEntryView(mimetype='text/css')


def build_link(target, text=None):
    url = urls.build('page', {'slug': target})

    _, values = urls.match(url)

    entries = db.select('''
SELECT source.*
FROM source
WHERE json_extract(source.metadata, '$.type') = 'page'
AND json_extract(source.metadata, '$.slug') = {}
''', target)

    entry = None

    if not entries:
        warn(f"page {target!r} not found")
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
        WIKILINK_RE = r'\[\[(?P<target>[@\w/0-9:_ -]+)(?P<text>(?:\|[\w/0-9:_ -]+)?)\]\]'
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
    ("Home", "article_list", {})
]
