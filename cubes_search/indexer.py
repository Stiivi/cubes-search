import cubes

class Indexer(object):
    """Dimension indexer"""
    def __init__(self, browser):
        """Creates a cube dimension indexer - object that will generate
        records for search indexing. You should override this class to create
        concrete indexers.

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

        Subclasses should override `add(record)` and optionally
        `initialize()`, `finalize()`

        """
        super(Indexer, self).__init__()

        self.browser = browser
        self.cube = browser.cube

        # FIXME: temporary for sphinx
        self.locale_tag = 0

    def initialize(self):
        """Initializes index creation. Default implementation does nothing.

        Possible uses: Create database table here, emit XML headers, ...
        """
        pass

    def finalize(self):
        """Finalizes index creation. Default implementation does nothing.

        Possible uses: flush buffer, close streams, emit XML closings...
        """
        pass

    def index(self, locales, **options):
        """Create index records for all dimensions in the cube"""
        # FIXME: this works only for one locale - specified in browser

        # for dimension in self.cube.dimensions:
        self.initialize()
        for locale_tag, locale in enumerate(locales):
            for dim_tag, dimension in enumerate(self.cube.dimensions):
                self.index_dimension(dimension, dim_tag,
                                     locale=locale,
                                     locale_tag=
                                     locale_tag,
                                     **options)

        self.finalize()

    def index_dimension(self, dimension, dimension_tag, locale,
                        locale_tag, **options):
        """Create dimension index records."""

        hierarchy = dimension.hierarchy()

        # Switch browser locale
        self.browser.locale = locale
        cell = cubes.Cell(self.cube)

        label_only = bool(options.get("labels_only"))

        for depth_m1, level in enumerate(hierarchy.levels):
            depth = depth_m1 + 1

            levels = hierarchy.levels[0:depth]
            keys = [level.key.ref() for level in levels]
            level_key = keys[-1]
            level_label = (level.label_attribute.ref())

            for record in self.browser.values(cell, dimension, depth):
                path = [record[key] for key in keys]
                path_string = cubes.string_from_path(path)

                for attr in level.attributes:
                    if label_only and str(attr) != str(level.label_attribute):
                        continue

                    fname = attr.ref()
                    irecord = {
                        "locale_tag": locale_tag,
                        "dimension": dimension.name,
                        "dimension_tag": dimension_tag,
                        "level": level.name,
                        "depth": depth,
                        "path": path_string,
                        "attribute": attr.name,
                        "value": record[fname],
                        "level_key": record[level_key],
                        "level_label": record[level_label]
                        }

                    self.add(irecord)

    def add(self, irecord):
        """Add index record to the index."""
        raise NotImplementedError("Subclasses should override %s.add()" % self.__class__.__name__)
