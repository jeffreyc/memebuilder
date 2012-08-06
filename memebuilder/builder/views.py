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
    """Returns a list of valid color names from PIL.ImageColor.."""
    colors = ImageColor.colormap.keys()
    colors.sort()
    return colors


def get_fonts():
    """Returns a list of valid TrueType Fonts on the system.

    The font directory is set via settings.FONT_DIR, and should be configured
    when the application is installed.

    """
    fonts = glob.glob('%s*%s' % (settings.FONT_DIR, settings.FONT_TYPE))
    for i in xrange(len(fonts)):
        fonts[i] = fonts[i].rsplit('/', 1)[-1].split('.')[0]
    fonts.sort()
    return fonts


def get_pos(im_size, txt_size, loc, align, offset):
    """Calculate the position of a line of text using the font and image sizes.

    loc - the vertical alignment
    align - the horizontal alignment
    offset - the vertical offset

    """
    if loc == 'top':
        h = offset
    elif loc == 'middle':
        h = im_size[1] / 2 - txt_size[1] / 2 + offset
    else:
        h = im_size[1] - txt_size[1] - offset
    if align == 'left':
        w = 10
    elif align == 'middle':
        w = im_size[0] / 2 - txt_size[0] / 2
    else:
        w = im_size[0] - txt_size[0] - 10
    return (w, h)


def balance((text, locs)):
    """Recalculates text locations to balance middle text.

    wrap(...) calculates offsets relative to the previous line. For middle-
    aligned text, these offsets need to be updated once we know how many lines
    there are. This function uses the number of offsets and the distance between
    them to balance the offsets correctly.

    No processing is done on text; that parameter is included to support
    wrapping wrap(...) with balance(...).

    >>> balance(([], [(0, 20), (0, 30)]))
    ([], [(0, 15), (0, 25)])
    >>> balance(([], [(0, 20), (0, 30), (0, 40)]))
    ([], [(0, 10), (0, 20), (0, 30)])
    >>> balance(([], [(0, 20), (0, 30), (0, 40), (0, 50)]))
    ([], [(0, 5), (0, 15), (0, 25), (0, 35)])

    """
    items = len(locs)
    if items == 1:
        return text, locs
    # if odd elem, distance len/2
    # if even elem, distance len/2 + 1/2
    if items % 2 == 0:
        base = items / 2 - 0.5
    else:
        base = items / 2
    distance = locs[1][1] - locs[0][1]
    offset = distance * base
    for i in xrange(len(locs)):
        locs[i] = (locs[i][0], locs[i][1] - offset)
    return text, locs


def wrap(im_size, font, text, loc, align, offset=0):
    """Wraps long lines to fit the image."""
    if font.getsize(text)[0] <= im_size[0] - 20:
        return [text], [get_pos(im_size, font.getsize(text), loc, align, offset)]
    words = text.split(' ')
    line = []
    if loc == 'bottom':
        range_ = xrange(len(words)-1, -1, -1)
    else:
        range_ = xrange(len(words))
    for i in range_:
        if font.getsize(' '.join(line + [words[i]]))[0] > im_size[0] - 20:
            break
        line.append(words[i])
    if i == 0 or i == len(words)-1 and loc == 'bottom':
        if loc == 'bottom':
            range_ = xrange(len(words[i])-1, -1, -1)
        else:
            range_ = xrange(len(words[i]))
        for j in range_:
            if font.getsize(''.join(line + [words[i][j]]))[0] > im_size[0] - 20:
                break
            line.append(words[i][j])
        if loc == 'bottom':
            words = words[:-1] + [words[-1][:j+1], words[-1][j+1:]]
            i = len(words)-2
        else:
            words = [words[i][:j], words[i][j:]] + words[1:]
            i = 1
        pass
    noffset = font.getsize(text)[1] + offset
    if loc == 'bottom':
        nwords = ' '.join(words[:i+1])
        line = ' '.join(words[i+1:])
    else:
        nwords = ' '.join(words[i:])
        line = ' '.join(words[:i])
    if nwords:
        nline, npos = wrap(im_size, font, nwords, loc, align, noffset)
    else:
        nline, npos = [], []
    return ([line] + nline,
            [get_pos(im_size, font.getsize(line), loc, align, offset)] + npos)


def caption(request, fn=None):
    """Captions an image, or renders a form to caption an image."""
    if request.method == 'POST':
        fp = path.join(templates, fn)
        im = Image.open(fp)
        format_ = im.format

        if 'height' in request.POST and request.POST['height'] and \
           'width' in request.POST and request.POST['width']:
            im = im.resize((int(request.POST['width']),
                            int(request.POST['height'])),
                           Image.ANTIALIAS)

        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype('%s%s%s' % (settings.FONT_DIR,
                                              request.POST['font'],
                                              settings.FONT_TYPE),
                                  int(request.POST['size']))
        lines, offsets = [], []
        if 'top' in request.POST and request.POST['top']:
            line, offset = wrap(im.size, font, request.POST['top'],
                                'top', request.POST.get('talign', 'left'), 10)
            lines += line
            offsets += offset
        if 'middle' in request.POST and request.POST['middle']:
            line, offset = balance(wrap(im.size, font, request.POST['middle'],
                                        'middle',
                                        request.POST.get('malign', 'left')))
            lines += line
            offsets += offset
        if 'bottom' in request.POST and request.POST['bottom']:
            line, offset = wrap(im.size, font, request.POST['bottom'],
                                'bottom', request.POST.get('balign', 'left'),
                                10)
            lines += line
            offsets += offset
        for i in xrange(len(lines)):
            draw.text(offsets[i], lines[i], font=font,
                      fill=request.POST['color'])

        response = http.HttpResponse(mimetype='image/%s' % format_)
        im.save(response, format_)
        return response
    else:
        im = Image.open(path.join(templates, fn))
        return shortcuts.render_to_response('caption.html',
                                            {'colors': get_colors(),
                                             'default_font':
                                                 settings.FONT_DEFAULT,
                                             'fonts': get_fonts(),
                                             'height': im.size[1],
                                             'image': fn,
                                             'name': name_for_image(fn),
                                             'width': im.size[0],},
                                            template.RequestContext(request))


def index(request):
    """Renders the index for the site."""
    images = os.listdir(templates)
    images.sort()
    for i in xrange(len(images)):
        name = name_for_image(images[i])
        images[i] = (name, images[i])
    return shortcuts.render_to_response('index.html',
                                        {'images': images,},
                                        template.RequestContext(request))


def name_for_image(image):
    """Translates an image's filename to a title.

    >>> name_for_image('business_cat.jpg')
    'Business Cat'

    """
    return image.split('.')[0].replace('_', ' ').title()


def thumbnail(request, fn=None, width=None, height=None):
    """Generates a thumbnail for a file."""
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
