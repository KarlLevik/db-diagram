# DB Diagram

DB Diagram is a small Python script that can help automate generation of simplified SQL database diagrams with enough detail to provide at least a high-level overview of the database schema.

.svg output files are searchable and provide extra info when mouse hovering. Other output formats are also supported.

### Dependencies

* [Graphviz](http://www.graphviz.org/)
* [pyparsing](https://pypi.python.org/pypi/pyparsing/2.0.3)

Grapviz can be installed with your package manager, e.g.

```bash
dnf install graphviz
```
pyparsing can be installed e.g. with pip:

```bash
pip install --user pyparsing
```
or with conda:

```bash
conda install pyparsing
```

### Usage

Using MariaDB, for example, to generate an SVG file:

```bash
mysqldump ${OPTIONS} --no-data dbname > tables.sql
python db_diagram.py -i tables.sql -o /tmp/dbname.svg -n
```

### Example

![SVG](https://rawgithub.com/Karl_levik/db_diagram/master/example.svg)

## Credits

Forked from https://github.com/rm-hull/sql_graphviz

... which was extended from http://energyblog.blogspot.co.uk/2006/04/blog-post_20.html by [EnErGy [CSDX]](https://www.blogger.com/profile/09096585177254790874)


## References

* http://pythonhosted.org/pyparsing/

## The MIT License (MIT)

Copyright (c) 2014 Richard Hull & EnErGy [CSDX]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
