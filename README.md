Cubes - Online Analytical Processing Framework for Python

ABOUT

Experimental Search backend - provides funcitonality for indexing and searching

Contains python API from Sphinx search engine: http://sphinxsearch.com/

Copyright © 2001-2010 Andrew Aksyonoff
Copyright © 2008-2010 Sphinx Technologies Inc, http://sphinxsearch.com

INSTALLATION

    python setup.py install
    
USAGE

To create search index use following source in your sphinx.config:

    source dimensions
    {
    	type					= xmlpipe2
        xmlpipe_command = python slicer-search index path_to_slicer.ini cube_name
    }


AUTHOR

Stefan Urbanek <stefan.urbanek@gmail.com>
