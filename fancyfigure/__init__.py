# -*- coding: utf-8 -*-
__version__ = '0.1.0'
__author__ = 'Thomas Bruederli <bruederli@kolabsys.com>'
__license__ = "GPLv3"

import os
import re
import json
import posixpath
from docutils.parsers.rst import roles, directives
from docutils import nodes, utils
from sphinx.util.compat import Directive
from sphinx.util.osutil import copyfile
# requires PIL from http://www.pythonware.com/products/pil/
from PIL import Image, ImageDraw, ImageFont

JS_INLINE = r'''
<script type="text/javascript">
    $(document).ready(function() {
        $("a.fancybox").fancybox(%s);
    });
</script>
'''

CSS_FILES = [
    'fancybox/jquery.fancybox.css',
]
JS_FILES = [
    'fancybox/jquery.fancybox.pack.js',
]

THUMBNAILS_FOLDER_NAME = '_fancyfigures'


class fancyfigure_node(nodes.reference, nodes.image, nodes.General, nodes.Element):
    pass

class fancyfigure_image(nodes.image, nodes.General, nodes.Element):
    pass

class fancyfrender_spec(nodes.General, nodes.Element):
    pass

class FancyrenderDirective(Directive):
    has_content = True
    required_arguments = 0

    option_spec = {
        'font': str,
        'color': str,
        'size': directives.nonnegative_int,
    }


    def run(self):
        fontsmap = {
            'verdana': 'Verdana.ttf',
            'verdana-bold': 'Verdana-Bold.ttf',
            'opensans': 'OpenSans-Regular.ttf',
            'opensans-bold': 'OpenSans-Bold.ttf',
            'opensans-light': 'OpenSans-Light.ttf',
            'opensans-semibold': 'OpenSans-Semibold.ttf',
            'roboto': 'Roboto-Regular.ttf',
            'roboto-bold': 'Roboto-Bold.ttf',
            'roboto-black': 'Roboto-Black.ttf',
            'roboto-medium': 'Roboto-Medium.ttf',
            'roboto-light': 'Roboto-Light.ttf',
        }

        font = self.options.get('font', 'verdana')
        node = fancyfrender_spec()
        node['font'] = fontsmap.get(font.lower(), font)
        node['color'] = self.options.get('color', '#000000')
        node['size'] = self.options.get('size', 12)
        node['content'] = self.content
        return [node]


class FancyfigureDirective(Directive):
    has_content = True
    required_arguments = 1

    try:
        str = unicode
    except NameError:
        pass

    option_spec = {
        'group': str,
        'class': str,
        'alt': str,
        'width': directives.nonnegative_int,
        'height': directives.nonnegative_int,
    }

    def run(self):
        env = self.state.document.settings.env

        group = self.options.get('group', 'default')
        width = self.options.get('width', env.app.config.fancyfigure_thumbnail_width)
        height = self.options.get('height', env.app.config.fancyfigure_thumbnail_height)
        cls = self.options.get('class', env.app.config.fancyfigure_thumbnail_class).split(' ')
        alt = self.options.get('alt', '')

        dimensions = (width, height)

        # compose paths for thumbnail rendering
        rel_path = os.path.split(self.arguments[0])
        source_root = os.path.split(self.state.document.attributes['source'])[0]
        real_path = os.path.join(source_root, *rel_path)
        thumb_dir = os.path.join(source_root, THUMBNAILS_FOLDER_NAME)
        thumb_path = os.path.join(thumb_dir, 'tmb_' + rel_path[1])
        render_path = os.path.join(thumb_dir, 'rnd_' + rel_path[1])

        if not os.path.isdir(thumb_dir):
            if os.path.exists(thumb_dir):
                raise Exception('%s must be a directory' % THUMBNAILS_FOLDER_NAME)

            os.mkdir(thumb_dir)

        # parse nested content for render directives or description text
        childs = nodes.Element()
        self.state.nested_parse(self.content, 0, childs)

        description = nodes.paragraph()
        description += childs.traverse(nodes.paragraph)
        renderers = childs.traverse(fancyfrender_spec)

        # open source image and render texts onto it
        if len(renderers) > 0 and os.path.exists(real_path):
            img = Image.open(real_path)
            draw = ImageDraw.Draw(img)

            # apply render:: directives
            for render in renderers:
                font = ImageFont.truetype(
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', render['font']),
                    render['size']
                )
                for line in render['content']:
                    m = re.match('(.+)\s*@(\d+),(\d+)(\s+#(\d+))?$', line.strip())
                    if m is not None:
                        text = self._substitute_vars(m.group(1))
                        x = m.group(2)
                        y = m.group(3)

                        # truncate string
                        if m.group(4) is not None:
                            maxlen = int(m.group(5))
                            if len(text) > maxlen:
                                text = text[0:maxlen] + '...'

                        draw.text(
                            (int(x), int(y)),
                            text,
                            font=font,
                            fill=render['color']
                        )
                    elif not line.strip() == '':
                        env.app.warn('fancyfigure: Invalid text label for %s: %s' % (
                            self.arguments[0], line
                        ))

            # save rendered image
            img.save(render_path)
            real_path = render_path
            self.arguments[0] = os.path.relpath(real_path, source_root)


        def make_thumb():
            thumb = Image.open(real_path)
            thumb.thumbnail(dimensions, Image.ANTIALIAS)
            thumb.save(thumb_path)
            return thumb.size

        # render thumbnail image
        if os.path.exists(real_path):
            # check if image was updated
            if not os.path.exists(thumb_path) or os.path.getmtime(thumb_path) < os.path.getmtime(real_path):
                (width, height) = make_thumb()
            elif os.path.exists(thumb_path):
                thumb = Image.open(thumb_path)
                compare = any(i == j for i, j in zip(dimensions, thumb.size))

                if not compare:
                    (width, height) = make_thumb()
                else:
                    (width, height) = thumb.size


        img = fancyfigure_image()
        img['uri'] = directives.uri(os.path.relpath(thumb_path, source_root))
        img['size'] = (width, height)
        img['alt'] = alt

        fn = fancyfigure_node('', '', internal=True)
        fn['uri'] = directives.uri(self.arguments[0])
        fn['group'] = group
        fn['alt'] = alt
        fn['content'] = description
        fn['classes'] += cls

        fn.append(img)

        return [fn]


    def _substitute_vars(self, text):
        config = self.state.document.settings.env.app.config
        replacements = config.fancyfigure_variables if hasattr(config, 'fancyfigure_variables') else {}
        return re.sub(r'\|([^\|]+)\|', lambda m: replacements[m.group(1)] if replacements.has_key(m.group(1)) else '', text)


def fancyfigure_image_html(self, node):
    # make links local
    if node['uri'] in self.builder.images:
        node['uri'] = posixpath.join(self.builder.imgpath, self.builder.images[node['uri']])

    self.body.append(
        '<img src="%s" width="%s" height="%s" alt="%s" />' % (
            node['uri'], node['size'][0], node['size'][1], node['alt']
        )
    )

def fancyfigure_node_html(self, node):
    # make links local
    if node['uri'] in self.builder.images:
        node['uri'] = posixpath.join(self.builder.imgpath, self.builder.images[node['uri']])

    self.body.append(
        self.starttag(
            node,
            'a',
            HREF=node['uri'],
            REL='%s' % node['group'],
            CLASS=' '.join(['fancybox'] + node['classes']),
            TITLE=node['alt'] or node['content'].astext()
        )
    )

def fancyfigure_node_after(self, node):
    self.body.append('</a>')

def pass_node(self, node):
    pass


def add_stylesheet(app):
    for file in CSS_FILES:
        app.add_stylesheet(file)


def add_javascript(app):
    for file in JS_FILES:
        app.add_javascript(file)


def copy_stylesheet(app, exception=None):
    on_rtd = (os.environ.get('READTHEDOCS', None) == 'True')

    if not on_rtd and (app.builder.name != 'html' or exception):
        return

    # TODO: change _static to variable from config (something like that exists?)
    if on_rtd:
        base_path = os.path.join(app.builder.srcdir, '_static')
    else:
        base_path = os.path.join(app.builder.outdir, '_static')
    path = os.path.abspath(os.path.join(base_path, 'fancybox'))

    if not os.path.exists(path):
        os.makedirs(path)

    app.info('Copying fancybox stylesheets... ', nonl=True)
    for file in CSS_FILES:
        copyfile(
            os.path.join(os.path.dirname(__file__), file),
            os.path.join(base_path, file)
        )
    app.info('done')
    app.info('Copying fancybox javascript... ', nonl=True)
    for file in JS_FILES:
        copyfile(
            os.path.join(os.path.dirname(__file__), file),
            os.path.join(base_path, file)
        )
    app.info('done')


def html_page_context(app, pagename, templatename, context, event_arg):
    if context.has_key('body'):
        context['body'] += JS_INLINE % (json.dumps(app.config.fancybox_config))


def setup(app):
    # define config vars
    app.add_config_value('fancybox_config', {}, 'env')
    app.add_config_value('fancyfigure_variables', {}, 'env')
    app.add_config_value('fancyfigure_thumbnail_width', 200, 'env')
    app.add_config_value('fancyfigure_thumbnail_height', 150, 'env')
    app.add_config_value('fancyfigure_thumbnail_class', '', 'env')

    # register directives
    app.add_directive('fancyfigure', FancyfigureDirective)
    app.add_directive('fancyrender', FancyrenderDirective)

    # register visitors
    app.add_node(fancyfigure_node,
                 html=(fancyfigure_node_html, fancyfigure_node_after),
                 latex=(pass_node, pass_node),
                 man=(pass_node, pass_node),
                 texinfo=(pass_node, pass_node),
                 text=(pass_node, pass_node),
    )
    app.add_node(fancyfigure_image,
                 html=(fancyfigure_image_html, pass_node),
                 latex=(pass_node, pass_node),
                 man=(pass_node, pass_node),
                 texinfo=(pass_node, pass_node),
                 text=(pass_node, pass_node),
    )

    # register event hooks
    app.connect('html-page-context', html_page_context)
    app.connect('builder-inited', add_stylesheet)
    app.connect('builder-inited', add_javascript)
    app.connect('builder-inited', copy_stylesheet)
