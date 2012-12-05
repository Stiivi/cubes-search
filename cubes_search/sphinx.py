"""Multidimensional searching using Sphinx search engine

WARNING: This is just preliminary prototype, use at your own risk of having your application broken
later.

"""
import cubes
import sphinxapi
import xml.sax.saxutils
from xml.sax.xmlreader import AttributesImpl
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
import sqlalchemy
import indexer
import collections

EMPTY_ATTRS = AttributesImpl({})

class SphinxSearchResult(object):
    def __init__(self, browser):
        super(SphinxSearchResult, self).__init__()
        self.browser = browser
        self.matches = None
        # self.dimension_paths = collections.OrderedDict()
        self.total_found = 0
        self.error = None
        self.warning = None

    # @property
    # def dimensions(self):
    #     return self.dimension_paths.keys()

    def values_old(self, dimension, zipped = False):
        """Return values of search result.

        :Attributes:
        * `zipped` - (experimental, might become standard) if ``True`` then
          return tuples: (`path`, `record`)
        """
        cell = self.browser.full_cube()
        if dimension in self.dimension_paths:
            paths = self.dimension_paths[dimension]

            cut = cubes.SetCut(dimension, paths)
            cell.cuts = [cut]
            values = cell.values(dimension)
            if zipped:
                return zip(self.dimension_paths[dimension],values)
            else:
                return values
        else:
            return []

    def dimension_matches(self, dimension):
        matches = []
        for match in self.matches:
            if match["dimension"] == dimension:
                dup = dict(match)

                path_str = match["path"]
                path = cubes.path_from_string(path_str)
                dup["path"] = path
                dup["path_string"] = path_str
                matches.append(dup)

        return matches

    def values(self, dimension, zipped=False):
        """Return values of search result.

        Attributes:

        * `zipped` - (experimental, might become standard) if ``True`` then
          returns tuples: (`path`, `record`)

        """

        raise NotImplementedError("Fetching values for search matches is not implemented")
        cell = self.browser.full_cube()

        paths = []
        for match in self.matches:
            if match["dimension"] == dimension:
                path_str = match["path"]
                path = cubes.path_from_string(path_str)
                paths.append(path)

        if paths:
            cut = cubes.SetCut(dimension, paths)
            cell.cuts = [cut]
            values = self.browser.values(cell, dimension)
            if zipped:
                # return 0
                return [ {"meta": r[0], "record":r[1]} for r in zip(self.matches, values) ]
            else:
                return values
        else:
            return []


class SphinxSearcher(object):
    """docstring for SphinxSearch"""
    def __init__(self, browser, host=None, port=None, **config):
        """Create sphing search object.

        :Parameters:
            * `browser` - Aggregation browser
            * `host` - host where searchd is running (optional)
            * `port` - port where searchd is listening (optional)
        """
        super(SphinxSearcher, self).__init__()
        self.browser = browser
        self.host = host
        self.port = port
        self.config = config

    def _dimension_tag(self, dimension):
        """Private method to get integer value from dimension name. Currently it uses
        index in ordered list of dimensions of the browser's cube"""

        tag = None
        tdim = self.browser.cube.dimension(dimension)
        for i, dim in enumerate(self.browser.cube.dimensions):
            if dim.name == tdim.name:
                tag = i
                break
        return tag

    def search(self, query, dimension=None, locale_tag=None):
        """Peform search using Sphinx. If `dimension` is set then only the one dimension will
        be searched."""
        print "SEARCH IN %s QUERY '%s' LOCALE:%s" % (str(dimension), query,
                locale_tag)

        sphinx = sphinxapi.SphinxClient(**self.config)

        if self.host:
            sphinx.SetServer(self.host, self.port)

        if dimension:
            tag = self._dimension_tag(dimension)
            if not tag:
                raise Exception("No dimension %s" % dimension)

            sphinx.SetFilter("dimension_tag", [tag])

        if locale_tag is not None:
            sphinx.SetFilter("locale_tag", [locale_tag])

        # FIXME: Quick hack for Matej Kurian
        sphinx.SetLimits(0, 1000)

        index_name = self.browser.cube.name

        sphinx.SetSortMode(sphinxapi.SPH_SORT_ATTR_ASC, "level_label")
        results = sphinx.Query(query, index = str(index_name))

        result = SphinxSearchResult(self.browser)

        if not results:
            return result

        result.total_found = results["total_found"]

        grouped = collections.OrderedDict()

        result.matches = [match["attrs"] for match in results["matches"]]

        # 
        # for match in results["matches"]:
        #     attrs = match["attrs"]
        #     key = tuple( (attrs["dimension"], attrs["path"]) )
        # 
        #     if key in grouped:
        #         exmatch = grouped[key]
        #         exattrs = exmatch["attributes"]
        #         exattrs.append(attrs["attribute"])
        #     else:
        #         exmatch = {"attributes": [attrs["attribute"]]}
        #         grouped[key] = exmatch
        # 
        # for (key, attrs) in grouped.items():
        #     (dim, path_str) = key
        #     path = cubes.browser.path_from_string(path_str)
        #     if dim in result.dimension_paths:
        #         result.dimension_paths[dim].append(path)
        #     else:
        #         result.dimension_paths[dim] = [path]

        result.error = sphinx.GetLastError()
        result.warning = sphinx.GetLastWarning()

        return result

class XMLSphinxIndexer(indexer.Indexer):
    """Create a SQL index for Sphinx"""
    def __init__(self, browser, out = None):
        """Creates a cube indexer - object that will provide xmlpipe2 data source for Sphinx
        search engine (http://sphinxsearch.com).

        :Attributes:
            * `browser` - configured AggregationBrowser instance

        Generated attributes:
            * id
            * dimension
            * dimension_tag: integer identifying a dimension
            * (hierarchy) - assume default
            * level
            * level key
            * dimension attribute
            * attribute value

        """
        super(XMLSphinxIndexer, self).__init__(browser)

        self.output = xml.sax.saxutils.XMLGenerator(out = out, encoding = 'utf-8')
        self._counter = 1

    def initialize(self):
        self.output.startDocument()

        self.output.startElement( u'sphinx:docset', EMPTY_ATTRS)

        # START schema
        self.output.startElement( u'sphinx:schema', EMPTY_ATTRS)

        fields = ["value"]

        attributes = [
                      ("locale_tag", "int"),
                      ("dimension", "string"),
                      ("dimension_tag", "int"),
                        ("level", "string"),
                        ("depth", "int"),
                        ("path", "string"),
                        ("attribute", "string"),
                        ("attribute_value", "string"),
                        ("level_key", "string"),
                        ("level_label", "string")]

        for field in fields:
            attrs = AttributesImpl({"name":field})
            self.output.startElement(u'sphinx:field', attrs)
            self.output.endElement(u'sphinx:field')

        for (name, ftype) in attributes:
            attrs = AttributesImpl({"name":name, "type":ftype})
            self.output.startElement(u'sphinx:attr', attrs)
            self.output.endElement(u'sphinx:attr')

        # END schema
        self.output.endElement(u'sphinx:schema')

    def finalize(self):
        self.output.endElement( u'sphinx:docset')
        self.output.endDocument()

    def add(self, irecord):
        """Emits index record (sphinx document) to the output XML stream."""

        attrs = AttributesImpl({"id":str(self._counter)})
        self._counter += 1

        self.output.startElement( u'sphinx:document', attrs)

        record = dict(irecord)
        record["attribute_value"] = record["value"]

        attrs = AttributesImpl({})
        for key, value in record.items():
            self.output.startElement( key, attrs)
            self.output.characters(unicode(value))
            self.output.endElement(key)

        self.output.endElement( u'sphinx:document')

class SQLSphinxIndexer(indexer.Indexer):
    def __init__(self, browser, connection, table_name, schema = None):
        super(SQLSphinxIndexer, self).__init__(browser)

        self.connection = connection
        self.engine = connection.engine
        self.metadata = sqlalchemy.MetaData()
        self.metadata.bind = self.engine
        self.schema = schema
        self.table_name = table_name

    def initialize(self):
        table = sqlalchemy.Table(self.table_name, self.metadata, autoload = False,
                                 schema = self.schema)

        if table.exists():
            table.drop()

        sequence = sqlalchemy.schema.Sequence(self.table_name + '_seq', optional = True)
        table = sqlalchemy.Table(self.table_name, self.metadata, schema = self.schema)

        table.append_column(Column('id', Integer, sequence, primary_key=True))
        table.append_column(Column('dimension', String))
        table.append_column(Column('dimension_tag', Integer))
        table.append_column(Column('level', String))
        table.append_column(Column('depth', Integer))
        table.append_column(Column('path', String))
        table.append_column(Column('attribute', String))
        table.append_column(Column('level_key', String))
        table.append_column(Column('level_label', String))

        table.create()

        self.insert = table.insert()
        self.buffer = []
        self.buffer_size = 1000

    def add(self, irecord):
        self.buffer.append(irecord)

        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        if self.buffer:
            self.connection.execute(self.insert, self.buffer)
            self.buffer = []

        # self.insert.values(irecord)

    def finalize(self):
        self.flush()
