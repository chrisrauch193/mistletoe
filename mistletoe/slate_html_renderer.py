"""
Slate HTML renderer for mistletoe.
"""

import re
import sys
from itertools import chain
from urllib.parse import quote
from mistletoe.block_token import HTMLBlock, SlateTopToken, SlateBottomToken
from mistletoe.span_token import HTMLSpan, RawText
from mistletoe.base_renderer import BaseRenderer
if sys.version_info < (3, 4):
    from mistletoe import _html as html
else:
    import html

from mistletoe.span_token import SpanToken

import os
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class SlateHTMLRenderer(BaseRenderer):
    """
    Slate HTML renderer class.

    See mistletoe.base_renderer module for more info.
    """

    settings = {'title': 'BBOXX Smart Solar API Reference', 'language_tabs': ['python', 'js'], 'toc_footers': ["<a href='https://github.com/tripit/slate'>Documentation Powered by Slate</a>"], 'includes': ['_introduction.md', '_schema.md', '_action_type_product_type_linker.md'], 'search': True}


    def __init__(self, *extras):
        """
        Args:
            extras (list): allows subclasses to add even more custom tokens.
        """
        self._suppress_ptag_stack = [False]
        super().__init__(*chain((HTMLBlock, HTMLSpan, SlateTopToken, SlateBottomToken), extras))
        # html.entities.html5 includes entitydefs not ending with ';',
        # CommonMark seems to hate them, so...
        self._stdlib_charref = html._charref
        _charref = re.compile(r'&(#[0-9]+;'
                              r'|#[xX][0-9a-fA-F]+;'
                              r'|[^\t\n\f <&#;]{1,32};)')
        html._charref = _charref

        print(self.settings)

    def __exit__(self, *args):
        super().__exit__(*args)
        html._charref = self._stdlib_charref

    def render_to_plain(self, token):
        if hasattr(token, 'children'):
            inner = [self.render_to_plain(child) for child in token.children]
            return ''.join(inner)
        return self.escape_html(token.content)

    def render_strong(self, token):
        template = '<strong>{}</strong>'
        return template.format(self.render_inner(token))

    def render_emphasis(self, token):
        template = '<em>{}</em>'
        return template.format(self.render_inner(token))

    def render_inline_code(self, token):
        template = '<code>{}</code>'
        inner = html.escape(token.children[0].content)
        return template.format(inner)

    def render_strikethrough(self, token):
        template = '<del>{}</del>'
        return template.format(self.render_inner(token))

    def render_image(self, token):
        template = '<img src="{}" alt="{}"{} />'
        if token.title:
            title = ' title="{}"'.format(self.escape_html(token.title))
        else:
            title = ''
        return template.format(token.src, self.render_to_plain(token), title)

    def render_link(self, token):
        template = '<a href="{target}"{title}>{inner}</a>'
        target = self.escape_url(token.target)
        if token.title:
            title = ' title="{}"'.format(self.escape_html(token.title))
        else:
            title = ''
        inner = self.render_inner(token)
        return template.format(target=target, title=title, inner=inner)

    def render_auto_link(self, token):
        template = '<a href="{target}">{inner}</a>'
        if token.mailto:
            target = 'mailto:{}'.format(token.target)
        else:
            target = self.escape_url(token.target)
        inner = self.render_inner(token)
        return template.format(target=target, inner=inner)

    def render_escape_sequence(self, token):
        return self.render_inner(token)

    def render_raw_text(self, token):
        return self.escape_html(token.content)

    @staticmethod
    def render_html_span(token):
        return token.content

    def render_heading(self, token):
        template = '<h{level} id="{id}">{inner}</h{level}>'
        inner = self.render_inner(token)
        id = self.render_heading_id(token)
        self.add_heading_to_search(token)
        print("HEADER TEST")
        print(self.settings)
        print("HEADER TEST DONE")
        return template.format(level=token.level, id=id, inner=inner)

    def add_heading_to_search(self, token):
        if "search_list" not in self.settings:
            self.settings["search_list"] = []
        if token.level == 1:
            self.settings["search_list"].append([self.render_inner(token), []])
        if token.level == 2:
            if len(self.settings["search_list"]) > 0:
                # print(self.settings["search"][len(self.settings["search"]) - 1])
                # self.settings["search_list"][len(self.settings["search_list"]) - 1][1].append(self.render(token.children[1]))
                search_sub_heading = "ERROR"
                if len(token.children) > 1:
                    search_sub_heading = self.render(token.children[1])
                else:
                    search_sub_heading = self.render_inner(token)
                search_sub_heading = search_sub_heading.replace("<code>", "").replace("</code>", "")
                self.settings["search_list"][len(self.settings["search_list"]) - 1][1].append(search_sub_heading)

    # TODO: Finish this
    def render_heading_id(self, token):
        rawTextChildTokens = list(filter(lambda child: isinstance(child, RawText), token.children))
        return ''.join(map(self.render, rawTextChildTokens)).replace(" ", "-").lower()

    def render_quote(self, token):
        elements = ['<blockquote>']
        self._suppress_ptag_stack.append(False)
        elements.extend([self.render(child) for child in token.children])
        self._suppress_ptag_stack.pop()
        elements.append('</blockquote>')
        return '\n'.join(elements)

    def render_paragraph(self, token):
        if self._suppress_ptag_stack[-1]:
            return '{}'.format(self.render_inner(token))
        return '<p>{}</p>'.format(self.render_inner(token))

    def render_block_code(self, token):
        template = '<pre><code{attr}>{inner}</code></pre>'
        if token.language:
            attr = ' class="{}"'.format('language-{}'.format(self.escape_html(token.language)))
        else:
            attr = ''
        inner = html.escape(token.children[0].content)
        return template.format(attr=attr, inner=inner)

    def render_list(self, token):
        template = '<{tag}{attr}>\n{inner}\n</{tag}>'
        if token.start is not None:
            tag = 'ol'
            attr = ' start="{}"'.format(token.start) if token.start != 1 else ''
        else:
            tag = 'ul'
            attr = ''
        self._suppress_ptag_stack.append(not token.loose)
        inner = '\n'.join([self.render(child) for child in token.children])
        self._suppress_ptag_stack.pop()
        return template.format(tag=tag, attr=attr, inner=inner)

    def render_list_item(self, token):
        if len(token.children) == 0:
            return '<li></li>'
        inner = '\n'.join([self.render(child) for child in token.children])
        inner_template = '\n{}\n'
        if self._suppress_ptag_stack[-1]:
            if token.children[0].__class__.__name__ == 'Paragraph':
                inner_template = inner_template[1:]
            if token.children[-1].__class__.__name__ == 'Paragraph':
                inner_template = inner_template[:-1]
        return '<li>{}</li>'.format(inner_template.format(inner))

    def render_table(self, token):
        # This is actually gross and I wonder if there's a better way to do it.
        #
        # The primary difficulty seems to be passing down alignment options to
        # reach individual cells.
        template = '<table>\n{inner}</table>'
        if hasattr(token, 'header'):
            head_template = '<thead>\n{inner}</thead>\n'
            head_inner = self.render_table_row(token.header, is_header=True)
            head_rendered = head_template.format(inner=head_inner)
        else: head_rendered = ''
        body_template = '<tbody>\n{inner}</tbody>\n'
        body_inner = self.render_inner(token)
        body_rendered = body_template.format(inner=body_inner)
        return template.format(inner=head_rendered+body_rendered)

    def render_table_row(self, token, is_header=False):
        template = '<tr>\n{inner}</tr>\n'
        inner = ''.join([self.render_table_cell(child, is_header)
                         for child in token.children])
        return template.format(inner=inner)

    def render_table_cell(self, token, in_header=False):
        template = '<{tag}{attr}>{inner}</{tag}>\n'
        tag = 'th' if in_header else 'td'
        if token.align is None:
            align = 'left'
        elif token.align == 0:
            align = 'center'
        elif token.align == 1:
            align = 'right'
        attr = ' style="text-align: {}"'.format(align)
        inner = self.render_inner(token)
        return template.format(tag=tag, attr=attr, inner=inner)

    @staticmethod
    def render_thematic_break(token):
        return '<hr />'

    @staticmethod
    def render_line_break(token):
        return '\n' if token.soft else '<br />\n'

    @staticmethod
    def render_html_block(token):
        return token.content

    def render_document(self, token):
        self.footnotes.update(token.footnotes)
        inner = '\n'.join([self.render(child) for child in token.children])
        slate_top = self.render_slate_top()
        slate_bottom = self.render_slate_bottom()
        fullDocument = '\n'.join([slate_top, inner, slate_bottom])

        return '{}\n'.format(fullDocument) if inner else ''

    def render_slate_top(self):
        f = open(os.path.join(__location__, "slate_files/template_top.html"), "r")
        return f.read() + self.render_toc_wrapper()

    def add_slate_title(self, slate_top):
        if "title" in self.settings:
            slate_top = slate_top + "\t<title>" + self.settings["title"] + "</title>\n"
        return slate_top

    def add_slate_language_tabs_body(self):
        slate_language_tabs_body = '<body class="index" data-languages="['
        if "language_tabs" in self.settings:
            for language in self.settings["language_tabs"]:
                slate_language_tabs_body = slate_language_tabs_body + "&quot;" + language + "&quot;,"
        slate_language_tabs_body = slate_language_tabs_body[:len(slate_language_tabs_body) - 1] + ']">\n'
        return slate_language_tabs_body

    def render_toc_wrapper(self):
        toc_wrapper = self.add_slate_language_tabs_body()
        toc_wrapper = toc_wrapper + '<div class="toc-wrapper">\n<img src="images/logo-1e815a84.png" class="logo" alt="Logo"/>\n'
        toc_wrapper = toc_wrapper + self.add_language_selector()
        toc_wrapper = toc_wrapper + self.add_search()
        toc_wrapper = toc_wrapper + self.add_toc_footers()
        toc_wrapper = toc_wrapper + """
        </div>
<div class="page-wrapper">
    <div class="dark-box"></div>
    <div class="content">
        """
        return toc_wrapper

    def add_language_selector(self):
        language_selector = '<div class="lang-selector">\n'
        if "language_tabs" in self.settings:
            for language in self.settings["language_tabs"]:
                language_selector = language_selector + '<a href="#" data-language-name="' + language + '">' + language + '</a>\n'
        language_selector = language_selector + '</div>\n'
        return language_selector

    def add_search(self):
        search = """
          <div class="search">
    <input type="text" class="search" id="input-search" placeholder="Search">
  </div>
  <ul class="search-results"></ul>
  <ul id="toc" class="toc-list-h1">
        """
        search = search + self.add_search_list_items()
        search = search + "</ul>\n"

#         search = search + "</ul>\n"
#   """
#     <li>
#       <a href="#introduction" class="toc-h1 toc-link" data-title="Introduction">Introduction</a>
#     </li>
#     <li>
#       <a href="#schema" class="toc-h1 toc-link" data-title="Schema">Schema</a>
#       <ul class="toc-list-h2">
#         <li>
#           <a href="#action-type-product-type-linker" class="toc-h2 toc-link"
#              data-title="Action Type Product Type Linker"><u>Action Type Product Type Linker</u></a>
#         </li>
#       </ul>
#     </li>
#   </ul>
#         """
        return search


    def add_search_list_items(self):
        if "search_list" in self.settings:
            for search_item_l1, search_item_l2_list in self.settings["search_list"]:
                search_list_item = "<li>\n"

                search_item_l1_hashtag = search_item_l1.lower()
                if search_item_l1_hashtag[0] == "/":
                   search_item_l1_hashtag = search_item_l1_hashtag[1::].replace('/', '-')
                search_list_item = search_list_item + '<a href="#{}" class="toc-h1 toc-link" data-title="{}">{}</a>\n'.format(search_item_l1_hashtag, search_item_l1, search_item_l1)
                if len(search_item_l2_list) > 0:
                    search_list_item = search_list_item + self.add_search_list_sub_item(search_item_l2_list)
                
                search_list_item = search_list_item + "</li>\n"

        return search_list_item

    def add_search_list_sub_item(self, search_item_l2_list):
        add_search_list_sub_item = """
      <ul class="toc-list-h2">
        """

        for search_item_l2 in search_item_l2_list:
            add_search_list_sub_item = add_search_list_sub_item + "<li>\n"
            search_item_l2_hashtag = search_item_l2.lower().replace(' ', '-')
            if search_item_l2_hashtag[0] == "/":
                search_item_l2_hashtag = search_item_l2_hashtag[1::].replace('/', '-')
            add_search_list_sub_item = add_search_list_sub_item + '<a href="#{}" class="toc-h2 toc-link" data-title="{}"><u>{}</u></a>\n'.format(search_item_l2_hashtag, search_item_l2, search_item_l2)
            add_search_list_sub_item = add_search_list_sub_item + "</li>\n"


        add_search_list_sub_item = add_search_list_sub_item + """
      </ul>\n
        """
        return add_search_list_sub_item


    def add_toc_footers(self):
        toc_footers = '<ul class="toc-footer">\n'
        if "toc_footers" in self.settings:
            for toc_footer in self.settings["toc_footers"]:
                toc_footers = toc_footers + '<li>' + toc_footer + '</li>\n'
        toc_footers = toc_footers + '</ul>\n'
        return toc_footers

    def render_slate_bottom(self):
        # f = open(os.path.join(__location__, "slate_files/template_bottom.html"), "r")
        # return f.read()
        bottom = """

  </div>
  <div class="dark-box">
        """

        bottom = bottom + self.add_language_selector()

        bottom = bottom + """
  </div>
</div>
</body>
</html>
        """
        return bottom


    @staticmethod
    def escape_html(raw):
        return html.escape(html.unescape(raw)).replace('&#x27;', "'")

    @staticmethod
    def escape_url(raw):
        """
        Escape urls to prevent code injection craziness. (Hopefully.)
        """
        return html.escape(quote(html.unescape(raw), safe='/#:()*?=%@+,&'))
