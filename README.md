Cubes Search
============
Search backend for Cubes - Lightweight Python OLAP

Requires cubes 0.10 and higher.

About
-----

Experimental Search backend - provides funcitonality for indexing and searching

Cubes Project:

* [github](https://github.com/Stiivi/cubes)
* [documentation](http://packages.python.org/cubes)

Installation
------------

    python setup.py install
    
Usage
-----

To create search index use following source in your sphinx.config:

    source dimensions
    {
    	type					= xmlpipe2
        xmlpipe_command = slicer-indexer slicer.ini cube_name
    }


Author
------

Stefan Urbanek <stefan.urbanek@gmail.com>

See AUTHORS for more information about credits for included packages.
