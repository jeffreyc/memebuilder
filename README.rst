***********
MEMEBUILDER
***********

MemeBuilder is a Django implementation of the assorted meme-builder
applications available online. It provides a basic index displaying all
available images for captioning and a captioning view. It was created for use
on corporate intranets, where it is either difficult to create images online
and then import them, or where the contents of the meme are sensitive, and
should not be transmitted online (e.g., trade secrets).

Requirements
============

MemeBuilder was built using Python 2.7, Python Imaging (PIL) 1.1.7 and Django
1.4. It requires at least one OpenType/TrueType font. It may work with Bitmap
fonts, but has not been tested with that configuration. Tests require Dingus
0.3.4.

Usage
=====

MemeBuilder has three user-configuratble settings in memebuilder.settings:

  FONT_DEFAULT - the default font to use
  FONT_DIR - the full path to the fonts directory
  FONT_TYPE - the font extension

The default values are for OS X Lion, and may need to be tweaked for your
system, depending upon where your fonts are installed and what fonts are
available. Don't forget to update ADMINS while you're there. You may also want
to toggle DEBUG.

Apache and mod_wsgi
-------------------

A sample Apache site file is included as memebuilder.site. This assumes a
simple installation performed by checking out the repository to
/home/memebuilder. The log directives require the creation of
${APACHE_LOG_DIR}/memebuilder (typically /var/log/apache/memebuilder).

Static Files
------------

For production deployments, static files will also need to be configured:

  ./manage.py collectstatic

This will collect all of your static files in STATIC_ROOT. If you installed
MemeBuilder some way other than by checking out the repository to
/home/memebuilder, you will need to change STATIC_ROOT as well.

Version History
===============

1.0 -- 2012-08-10 -- initial release
