Sphinx Fancyfigure Extension by Kolab
=====================================

Plugin inspired by the [sphinxcontrib-fancybox][sphinx-fancybox] extension with additional down-scaling of thumbnail images and optional text rendering onto the source images. The main purpose of this extenson is to render screen shots with dynamic text from local configuration variables. Used for Kolab client setup instructions with individual host names and URIs.

Example fancyfigure directive with rendered text:

```
.. fancyfigure:: relative/path/to/image.png
    :group: fancyboxgroup
    :width: 200
    :height: 160
    :alt: Fancy image alt text and title

    .. fancyrender::
        :font: verdana-bold
        :size: 11
        :color: #cc0000

        Some text @125,82

        Text with |variable| @186,241

        |variable| text with length limit @344,262 #64
```

Each text label to be rendered onto the image is listed as a paragraph inside 
the *fancyrender* directive. It requires a position denoted with `@<x>,<y>` at 
the end of the label and can have an optional length parameter defined with 
`#<chars>`.


Configuration options
---------------------

The following options can be specified in the Sphinx *conf.py*:

`fancyfigure_variables = {}`

  A dict with variable values used in text labels to be rendered onto the images.
  Enter key => value pairs which will substitute strings like |key| in text labels.

`fancyfigure_thumbnail_width = 200`

  Default value for the maximum thumbnail width in pixels.

`fancyfigure_thumbnail_height = 150`

  Default value for the maximum thumbnail height in pixels.

`fancyfigure_thumbnail_class = ""`

  Additional CSS classes added to the fancybox links as a space-separated string.

`fancybox_config = {}`

  A dict with options for the *fancyBox* widget. See the [fancyBox documentation][fancybox-docs] for reference.


Requirements
------------

For image rendering the Python [PIL][pypi-pil] module is required.


[sphinx-fancybox]: https://github.com/spinus/sphinxcontrib-fancybox
[fancybox-docs]:   http://fancyapps.com/fancybox/#docs
[pypi-pil]: https://pypi.python.org/pypi/PIL/
