# IRDB Sphinx topology

This Sphinx setup is a bit different to the regular ones.
In order for Sphinx to find all the instrument specific RST docs, I needed to
move the following files:

    <TOP-DIR>/docs/source/conf.py --> <TOP-DIR>/conf.py
    <TOP-DIR>/docs/source/index.rst --> <TOP-DIR>/index.rst

## Source RST files

Because conf.py has been moved to the top-level directory, this is now the
reference path for all files. 
Any files referenced in the TOC in the index.rst file must now be referred to 
by their fill path name. E.g:

    .. toctree::
       intro

must now be

    .. toctree::
       docs/source/intro

This means that all instrument docs can also now be referenced relative to the
top-level folder. E.g:

    .. toctree::
       docs/source/intro
       metis/docs/readme

## HTML build files

All html files are still build and added to the normal sphinx path of
`<TOP-DIR>/docs/build/*.html`

## Static files

Static files (non RST files that should be available for download) like python
notebooks or images can be places in the regular static folder:

    <TOP-DIR>/docs/source/_static

Additional folders containing static files can be added to the `conf.py` list 
`html_static_path`. 
The current `conf.py` entry looks like this:

    html_static_path = ['docs/source/_static',
                        'METIS/docs/example_notebooks']

## Python notebooks

Python notebooks are by nature static files.
However they can be rendered by sphinx using the nbsphinx extension.
`.ipynb` files must be contained in a folder that exists in the `conf.py` 
static path list.
These files are referenced like normal RST files


