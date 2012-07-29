import glob
import os
from os import path

from django import http
from django import shortcuts
from django import template
from django.conf import settings
from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont


templates = path.join(path.dirname(__file__), 'static', 'templates')
thumbnail_size = (128, 128)


def get_colors():
    colors = ImageColor.colormap.keys()
    colors.sort()
    return colors


def get_fonts():
    fonts = glob.glob('%s*%s' % (settings.FONT_DIR, settings.FONT_TYPE))
    for i in xrange(len(fonts)):
        fonts[i] = fonts[i].rsplit('/', 1)[-1].split('.')[0]
    return fonts


def get_pos(im_size, txt_size, loc, align, offset):
    """Calculate the position of a line of text using the font and image sizes.

    loc - the vertical alignment
    align - the horizontal alignment
    offset - the vertical offset

    """
    if loc == 'top':
        h = offset # 10
    elif loc == 'middle':
        h = im_size[1] / 2 - txt_size[1] / 2
    else:
        h = im_size[1] - txt_size[1] - offset # 10
    if align == 'left':
        w = 10
    elif align == 'middle':
        w = im_size[0] / 2 - txt_size[0] / 2
    else:
        w = im_size[0] - txt_size[0] - 10
    return (w, h)


def caption(request, fn=None):
    if request.method == 'POST':
        fp = path.join(templates, fn)
        im = Image.open(fp)
        format_ = im.format

        if 'height' in request.POST and request.POST['height'] and \
           'width' in request.POST and request.POST['width']:
            im = im.resize((int(request.POST['width']),
                            int(request.POST['height'])),
                           Image.ANTIALIAS)

        # TODO: wrap long lines
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype('%s%s%s' % (settings.FONT_DIR,
                                              request.POST['font'],
                                              settings.FONT_TYPE),
                                  int(request.POST['size']))
        if 'top' in request.POST and request.POST['top']:
            draw.text(get_pos(im.size, font.getsize(request.POST['top']),
                              'top', request.POST.get('talign', 'left'), 10),
                      request.POST['top'],
                      font=font, fill=request.POST['color'])
        if 'middle' in request.POST and request.POST['middle']:
            draw.text(get_pos(im.size, font.getsize(request.POST['middle']),
                              'middle', request.POST.get('malign', 'left')),
                      request.POST['middle'],
                      font=font, fill=request.POST['color'])
        if 'bottom' in request.POST and request.POST['bottom']:
            draw.text(get_pos(im.size, font.getsize(request.POST['bottom']),
                              'bottom', request.POST.get('balign', 'left'), 10),
                      request.POST['bottom'],
                      font=font, fill=request.POST['color'])

        response = http.HttpResponse(mimetype='image/%s' % format_)
        im.save(response, format_)
        return response
    else:
        im = Image.open(path.join(templates, fn))
        return shortcuts.render_to_response('caption.html',
                                            {'colors': get_colors(),
                                             'fonts': get_fonts(),
                                             'height': im.size[1],
                                             'image': fn,
                                             'name': name_for_image(fn),
                                             'width': im.size[0],},
                                            template.RequestContext(request))


def index(request):
    images = os.listdir(templates)
    images.sort()
    for i in xrange(len(images)):
        name = name_for_image(images[i])
        images[i] = (name, images[i])
    return shortcuts.render_to_response('index.html',
                                        {'images': images,},
                                        template.RequestContext(request))


def name_for_image(image):
    return image.split('.')[0].replace('_', ' ').title()


def thumbnail(request, fn=None, width=None, height=None):
    if fn is None:
        raise http.Http404
    fp = path.join(templates, fn)
    im = Image.open(fp)
    format_ = im.format
    if height and width:
        im.thumbnail((int(width), int(height)), Image.ANTIALIAS)
    else:
        im.thumbnail(thumbnail_size, Image.ANTIALIAS)
    response = http.HttpResponse(mimetype='image/%s' % format_)
    im.save(response, format_)
    return response
