Django Uploadtemplate allows users to upload zip files containing
theme templates and static files, then access the contents of those
files to override the default templates and static files of the sites.

Using templates
===============

To use templates, all you need to do is add the following line to
your settings file::

    TEMPLATE_LOADERS = (
        'uploadtemplate.loader.Loader',
        ...
    )


Using static files
==================

In your templates, you just need to replace all instances of
``{% load staticfiles %}`` and ``{% load static %}`` with
``{% load uploadtemplate %}``. This is not compatible with using
``{{ STATIC_URL }}`` - but really, you shouldn't be using that anyway.
