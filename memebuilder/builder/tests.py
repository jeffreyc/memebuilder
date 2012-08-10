import os
from os import path

import dingus
from django import test
from django.conf import settings
from PIL import ImageColor

from . import views


class MultiValueDingus(dingus.Dingus):
    """A Dingus that supports returning different return values on subsequent
    calls.

    A MultiValueDingus assumes that any return value argument is a list,
    and treats it as such.

    Dingus is not designed to support multiple return values, so this may seem
    a bit hacky. It should only be used when multiple return values are
    necessary.

    >>> d = MultiValueDingus(return_value=['a', 'b'])
    >>> d()
    'a'
    >>> d()
    'b'
    >>> d()
    'b'

    >>> d = MultiValueDingus(return_value=[['a', 'b'], ['c', 'd'], ['e', 'f']])
    >>> d()
    ['a', 'b']
    >>> d()
    ['c', 'd']
    >>> d()
    ['e', 'f']
    >>> d()
    ['e', 'f']

    >>> d = MultiValueDingus(foo__returns=['a', 'b'])
    >>> d.foo()
    'a'
    >>> d.foo()
    'b'
    >>> d.foo()
    'b'

    """
    def _get_return_value(self):
        # Overrides Dingus._get_return_value to return a value popped off of
        # self._return_values. It tracks the number of values in the list
        # so it knows when to stop popping values, thus supporting returning
        # lists.
        if self._return_value is dingus.NoReturnValue:
            self._return_value = self._create_child('()')
        if self._return_value_count == 0:
            # We've popped all there is to pop. Keep returning the last value.
            return self._return_value
        self._return_value_count -= 1
        if self._return_value_count == 0:
            # We're down to the last value. Turn [value] into value and return.
            self._return_value = self._return_value.pop(0)
            return self._return_value
        # We have more than one value remaining. Pop and return.
        return self._return_value.pop(0)

    def _set_return_value(self, value):
        self._return_value_count = len(value)
        self._return_value = value

    return_value = property(_get_return_value, _set_return_value)

    def __call__(self, *args, **kwargs):
        # Overrides Dingus.__call__ by caching self.return_value to avoid
        # accessing the property 2-3 times and thus getting 2-3 different
        # values.
        retval = self.return_value
        self._log_call('()', args, kwargs, retval)
        if self._parent:
            self._parent._log_call(self._short_name,
                                   args,
                                   kwargs,
                                   retval)

        return retval


class TestGetColors(test.SimpleTestCase):
    def setUp(self):
        self.colormap = ImageColor.colormap
        ImageColor.colormap = {'red': '#FF0000',
                               'green': '#00FF00',
                               'blue': '#0000FF',}

    def tearDown(self):
        ImageColor.colormap = self.colormap

    def test_get_colors(self):
        self.assertEqual(views.get_colors(),
                         ['blue', 'green', 'red',])


class TestGetFonts(test.SimpleTestCase):
    def setUp(self):
        self.FONT_DIR = settings.FONT_DIR
        self.FONT_TYPE = settings.FONT_TYPE
        settings.FONT_DIR = path.join(path.dirname(__file__), 'fixtures',
                                      'test', 'fonts')
        settings.FONT_DIR += path.sep
        settings.FONT_TYPE = '.ttf'

    def tearDown(self):
        settings.FONT_DIR = self.FONT_DIR
        self.FONT_TYPE = settings.FONT_TYPE

    def test_fontdir_has_non_ttf(self):
        fonts = os.listdir(settings.FONT_DIR)
        assert 'Arial.pil' in fonts

    def test_get_fonts(self):
        self.assertEqual(views.get_fonts(),
                         ['Courier', 'Impact',])


class TestViews(test.TestCase):
    def setUp(self):
        self.Image = views.Image
        views.Image = dingus.Dingus()
        self.ImageDraw = views.ImageDraw
        views.ImageDraw = dingus.Dingus()
        self.ImageFont = views.ImageFont
        views.ImageFont = dingus.Dingus()
        self.balance = views.balance
        views.balance = dingus.Dingus(return_value=(['a'], [(0, 0)]))
        self.wrap = views.wrap
        views.wrap = dingus.Dingus(return_value=(['a'], [(0, 0)]))
        self.STATICFILES_DIRS = settings.STATICFILES_DIRS
        settings.STATICFILES_DIRS = (path.join(path.dirname(__file__),
                                               'fixtures', 'test'),)

    def tearDown(self):
        views.Image = self.Image
        views.ImageDraw = self.ImageDraw
        views.ImageFont = self.ImageFont
        views.balance = self.balance
        views.wrap = self.wrap
        settings.STATICFILES_DIRS = self.STATICFILES_DIRS

    def test_caption_get(self):
        response = self.client.get('/caption/business_cat.jpg/')
        self.assertContains(response, '<form method="POST">', status_code=200)

    def test_caption_post(self):
        response = self.client.post('/caption/business_cat.jpg/',
                                    {'balign': 'right',
                                     'bottom': 'This is the bottom caption.',
                                     'color': 'white',
                                     'font': 'Impact',
                                     'malign': 'middle',
                                     'middle': 'This is the middle caption.',
                                     'size': '48',
                                     'talign': 'left',
                                     'top': 'This is the top caption.',})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(views.ImageFont.calls[0][0], 'truetype')
        assert 'Impact' in views.ImageFont.calls[0][1][0]
        self.assertEqual(views.ImageFont.calls[0][1][1], 48)
        self.assertEqual(views.wrap.calls[0][1][2], 'This is the top caption.')
        self.assertEqual(views.wrap.calls[0][1][4], 'left')
        self.assertEqual(views.wrap.calls[1][1][2],
                         'This is the middle caption.')
        self.assertEqual(views.wrap.calls[1][1][4], 'middle')
        self.assertEqual(views.wrap.calls[2][1][2],
                         'This is the bottom caption.')
        self.assertEqual(views.wrap.calls[2][1][4], 'right')
        for i in xrange(3):
            self.assertEqual(views.ImageDraw.Draw().calls[i][0], 'text')
            self.assertEqual(views.ImageDraw.Draw().calls[i][2]['fill'],
                             'white')

    def test_caption_post_resizes(self):
        response = self.client.post('/caption/business_cat.jpg/',
                                    {'balign': 'right',
                                     'bottom': 'This is the bottom caption',
                                     'color': 'white',
                                     'font': 'Impact',
                                     'height': '123',
                                     'malign': 'middle',
                                     'middle': 'This is the middle caption',
                                     'size': '48',
                                     'talign': 'left',
                                     'top': 'This is the top caption.',
                                     'width': '234',})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(views.Image.open().calls[0][0], 'resize')
        self.assertEqual(views.Image.open().calls[0][1][0], (234, 123))

    def test_index(self):
        response = self.client.get('/')
        self.assertContains(response, '/thumbnail/business_cat.jpg/',
                            status_code=200)

    def test_scaled(self):
        response = self.client.get('/scaled/business_cat.jpg/100/100/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(views.Image.open().calls[0][0], 'thumbnail')
        self.assertEqual(views.Image.open().calls[0][1][0], (100, 100))

    def test_thumbnail(self):
        response = self.client.get('/thumbnail/business_cat.jpg/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(views.Image.calls[0][0], 'open')
        assert views.Image.calls[0][1][0].endswith('business_cat.jpg')
        self.assertEqual(views.Image.open().calls[0][0], 'thumbnail')
        self.assertEqual(views.Image.open().calls[0][1][0],
                         views.thumbnail_size)
        self.assertEqual(views.Image.open().calls[1][0], 'save')


class TestUtils(test.SimpleTestCase):
    def test_balance(self):
        self.assertEqual(views.balance(([], [(0, 20), (0, 30)])),
                         ([], [(0, 15), (0, 25)]))
        self.assertEqual(views.balance(([], [(0, 20), (0, 30), (0, 40)])),
                         ([], [(0, 10), (0, 20), (0, 30)]))
        self.assertEqual(views.balance(([], [(0, 20), (0, 30), (0, 40),
                                             (0, 50)])),
                         ([], [(0, 5), (0, 15), (0, 25), (0, 35)]))

    def test_get_pos(self):
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'top', 'left', 10),
                         (10, 10))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'middle', 'left',
                                       0),
                         (10, 45))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'bottom', 'left',
                                       10),
                         (10, 80))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'top', 'middle',
                                       10),
                         (25, 10))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'middle', 'middle',
                                       0),
                         (25, 45))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'bottom', 'middle',
                                       10),
                         (25, 80))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'top', 'right',
                                       10),
                         (40, 10))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'middle', 'right',
                                       0),
                         (40, 45))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'bottom', 'right',
                                       10),
                         (40, 80))

    def test_get_pos_respects_offset(self):
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'top', 'left', 20),
                         (10, 20))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'middle', 'left',
                                       10),
                         (10, 55))
        self.assertEqual(views.get_pos((100, 100), (50, 10), 'bottom', 'left',
                                       20),
                         (10, 70))

    def test_name_for_image(self):
        self.assertEqual(views.name_for_image('business_cat.jpg'),
                         'Business Cat')

    def test_wrap_no_wrap(self):
        font = dingus.Dingus(getsize__returns=(30, 10))
        self.assertEqual(views.wrap((100, 100), font, 'abc', 'top', 'left', 10),
                         (['abc'], [(10, 10)]))

    def test_wrap_once_top(self):
        font = MultiValueDingus(getsize__returns=[(120, 10),
                                                  (40, 10),
                                                  (80, 10),
                                                  (120, 10),
                                                  (80, 10),
                                                  (40, 10)])
        self.assertEqual(views.wrap((100, 100), font, 'abc def ghi', 'top',
                                    'left', 10),
                         (['abc def', 'ghi'], [(10, 10), (10, 20)]))

    def test_wrap_twice_top(self):
        font = MultiValueDingus(getsize__returns=[(210, 10),
                                                  (70, 10),
                                                  (140, 10),
                                                  (210, 10),
                                                  (140, 10),
                                                  (70, 10),
                                                  (140, 10),
                                                  (140, 10),
                                                  (70, 10),
                                                  (70, 10),
                                                  (70, 10),
                                                  (70, 10)])
        self.assertEqual(views.wrap((100, 100), font, 'abc def ghi', 'top',
                                    'left', 10),
                         (['abc', 'def', 'ghi'],
                          [(10, 10), (10, 20), (10, 30)]))

    def test_wrap_once_bottom(self):
        font = MultiValueDingus(getsize__returns=[(120, 10),
                                                  (40, 10),
                                                  (80, 10),
                                                  (120, 10),
                                                  (80, 10),
                                                  (40, 10)])
        self.assertEqual(views.wrap((100, 100), font, 'abc def ghi', 'bottom',
                                    'left', 10),
                         (['def ghi', 'abc'], [(10, 80), (10, 70)]))

    def test_wrap_long_word_top(self):
        font = MultiValueDingus(getsize__returns=[(120, 10),
                                                  (120, 10),
                                                  (40, 10),
                                                  (80, 10),
                                                  (120, 10),
                                                  (120, 10),
                                                  (40, 10),
                                                  (40, 10),
                                                  (80, 10)])
        self.assertEqual(views.wrap((100, 100), font, 'abc', 'top',
                                    'left', 10),
                         (['ab', 'c'], [(10, 10), (10, 20)]))

    def test_wrap_long_word_bottom(self):
        font = MultiValueDingus(getsize__returns=[(120, 10),
                                                  (120, 10),
                                                  (40, 10),
                                                  (80, 10),
                                                  (120, 10),
                                                  (120, 10),
                                                  (40, 10),
                                                  (40, 10),
                                                  (80, 10)])
        self.assertEqual(views.wrap((100, 100), font, 'abc', 'bottom',
                                    'left', 10),
                         (['bc', 'a'], [(10, 80), (10, 70)]))
