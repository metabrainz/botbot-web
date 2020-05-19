"""Near duplicate of Django's `urlizetrunc` with support for image classes"""

from urllib.parse import parse_qs, urlparse, urlunparse
from django.template.base import Node
from django.template.library import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe, SafeData
from django.utils.encoding import force_text
from django.utils.html import (TRAILING_PUNCTUATION_CHARS, WRAPPING_PUNCTUATION,
                               word_split_re, simple_url_re, smart_urlquote,
                               simple_url_2_re, escape)
import re


register = Library()

image_file_types = [".png", ".jpg", ".jpeg", ".gif"]
IMAGE = 1
YOUTUBE = 2

email_re = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


@register.filter(is_safe=True, needs_autoescape=True)
@stringfilter
def bbme_urlizetrunc(value, limit, autoescape=None):
    """
    Converts URLs into clickable links, truncating URLs to the given character
    limit, and adding 'rel=nofollow' attribute to discourage spamming.

    Argument: Length to truncate URLs to.
    """
    return mark_safe(urlize_impl(value, trim_url_limit=int(limit), nofollow=True,
                                 autoescape=autoescape))


def is_embeddable(url):
    """
    Given a url can we embed a vidoe or an image
    :param url: The url of the content
    :return: Type of content, bool if possible.
    """
    # Check if path ends with a image file type
    if any([url.path.endswith(ending) for ending in image_file_types]):
        return IMAGE, True

    elif url.hostname in ['www.youtube.com'] and \
            url.path.startswith('/watch') and 'v' in parse_qs(url.query, False):
        return YOUTUBE, True

    elif url.hostname == "cl.ly":
        return IMAGE, True

    return None, False


def parse_url(word):
    """
    If word is url, return a parsed version of it.
    :param word: string
    :return: None or parsed url
    """
    url = None

    if simple_url_re.match(word):
        url = smart_urlquote(word)
    elif simple_url_2_re.match(word):
        url = smart_urlquote('http://%s' % word)
    elif ':' not in word and email_re.match(word):
        local, domain = word.rsplit('@', 1)
        try:
            domain = domain.encode('idna').decode('ascii')
        except UnicodeError:
            return

        url = 'mailto:%s@%s' % (local, domain)

    if url:
        return urlparse(url)


def embed_image(url):
    """
    Returns two urls, one for display and other where to source the image. This also
    handles cases like drobox where you need to use another hostname.

    :param url: Url parts as returned from urlparse
    :return: two urls
    """
    if url.hostname in ["www.dropbox.com", "dropbox.com"]:
        src = urlunparse((url.scheme, "dl.dropboxusercontent.com",
                         url.path, url.params, url.query,
                         url.fragment))
        link = urlunparse(url)

        return link, src

    elif url.hostname == "cl.ly":
        match = re.match(r"^/image/(?P<image_id>[\-\w\.]+)", url.path)
        if not match:
            match = re.match(r"^/(?P<image_id>[\-\w\.]+)", url.path)

        if match:
            image_id = match.group('image_id')

            src = urlunparse((
                url.scheme, url.hostname, f"/{image_id}/content",
                url.params, url.query, url.fragment))
            return urlunparse(url), src

    return urlunparse(url), urlunparse(url)


def build_html_attrs(html_attrs):
    """
    Builds a string from a dict of html attributes
    :param html_attrs:
    :return:
    """
    result = ""
    for key, value in html_attrs.items():
        if isinstance(value, (list, tuple)):
            if value:
                value = " ".join(map(str, value))
            else:
                value = None
        if not value:
            continue

        result += f' {key}="{value}"'

    return result


def embed_youtube(url):
    """
    Generates two urls, one for display, and another to embed the content.
    :param url:
    :return: display link, src
    """
    video_id = parse_qs(url.query)['v'][0]

    return urlunparse(
        url), f"//www.youtube.com/embed/{video_id}"


def urlize_impl(text, trim_url_limit=None, nofollow=False, autoescape=False):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links, and also on links ending in one of
    the original seven gTLDs (.com, .edu, .gov, .int, .mil, .net, and .org).
    Links can have trailing punctuation (periods, commas, close-parens) and
    leading punctuation (opening parens) and it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """

    # Remove control characters form the text input. The Github IRC bot
    # sends a "Shift Up" control character we need to strip out, so the
    # urlify function does not grab it.
    try:
        mpa = dict.fromkeys(list(range(32)))
        text = text.translate(mpa)

        trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
        safe_input = isinstance(text, SafeData)
        words = word_split_re.split(force_text(text))

        for i, word in enumerate(words):
            match = None
            if '.' in word or '@' in word or ':' in word:
                # Deal with punctuation.
                lead, middle, trail = '', word, ''
                for punctuation in TRAILING_PUNCTUATION_CHARS:
                    if middle.endswith(punctuation):
                        middle = middle[:-len(punctuation)]
                        trail = punctuation + trail
                for opening, closing in WRAPPING_PUNCTUATION:
                    if middle.startswith(opening):
                        middle = middle[len(opening):]
                        lead = lead + opening
                    # Keep parentheses at the end only if they're balanced.
                    if (middle.endswith(closing)
                        and middle.count(closing) == middle.count(opening) + 1):
                        middle = middle[:-len(closing)]
                        trail = closing + trail

                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)

                # Make URL we want to point to.
                url = parse_url(middle)
                if url:
                    html_attrs = {'class': []}

                    if not url.scheme == "mailto" and nofollow:
                        html_attrs['rel'] = 'nofollow'

                    _type, embeddable = is_embeddable(url)
                    if embeddable:
                        link, src = None, None
                        if _type == IMAGE:
                            link, src = embed_image(url)
                            html_attrs['class'].append('image')
                            html_attrs['data-type'] = "image"
                        elif _type == YOUTUBE:
                            link, src = embed_youtube(url)
                            html_attrs['class'].append('image')
                            html_attrs['data-type'] = "youtube"

                        html_attrs['href'] = link
                        html_attrs['data-src'] = src

                    if 'href' not in html_attrs:
                        html_attrs['href'] = urlunparse(url)

                    trimmed = trim_url(middle)
                    middle = f"<a{build_html_attrs(html_attrs)}>{trimmed}</a>"

                    words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
                else:
                    if safe_input:
                        words[i] = mark_safe(word)
                    elif autoescape:
                        words[i] = escape(word)
            elif safe_input:
                words[i] = mark_safe(word)
            elif autoescape:
                words[i] = escape(word)
        return ''.join(words)
    except ValueError:
        return text


def strip_empty_lines(block):
    return '\n'.join(
        [l.strip() for l in block.splitlines() if l.strip()]).strip()


class WhiteLinelessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return strip_empty_lines(self.nodelist.render(context))


@register.tag
def whitelineless(parser, token):
    nodelist = parser.parse(('endwhitelineless',))
    parser.delete_first_token()
    return WhiteLinelessNode(nodelist)
