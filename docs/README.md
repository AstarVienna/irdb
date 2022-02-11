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

We use the ``nbsphinx`` package to render iPython notebooks just like RST files.
Notebooks must be added to a ``.. toctree`` command to be found and rendered.

    .. toctree::
       docs/notebooks/example_notebook      #.ipynb

For testing purposes notebooks are not executed when the sphinx build occurs.
This can be changed (and should be for pushes to Github --> RTFD) by changing 
``conf.py`` line from ``nbsphinx_execute = "never"`` to ``"always"``.


