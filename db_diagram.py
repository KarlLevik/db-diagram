#!/usr/bin/env python

# Program to help automate generation of simplified SQL database diagrams
# with enough detail to provide at least a high-level overview of the database
# schema.
#
# .svg output files are searchable and provide extra info when mouse hovering.
# Other output formats are also supported.
#
# Karl Levik - 2019-10-07
#

import html
import sys
import os
from datetime import datetime
import getopt
from pyparsing import alphas, alphanums, Literal, Word, Forward, OneOrMore, ZeroOrMore, CharsNotIn, Suppress, QuotedString, Optional, Keyword, CaselessKeyword, NotAny, Combine, White, Regex, delimitedList, commaSeparatedList
import pydot

table_colours = ["#800000", "#9A6324", "#808000", "#469990", "#000075", "#000000", "#e6194B", "#f58231", "#ffe119", "#bfef45", "#3cb44b", "#42d4f4", "#4363d8", "#911eb4", "#f032e6", "#a9a9a9", "#fabebe", "#ffd8b1", "#fffac8", "#aaffc3", "#e6beff", "#ffffff"]

text_colours = ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#000000", "#000000", "#ffffff", "#000000", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#000000", "#000000", "#000000", "#000000", "#000000", "#000000"]

class Table(object):
    name = None
    pk = None
    columns = {}
    keys = {}

    def __init__(self, name, pk = None, columns = {}, fkeys = {}):
        self.name = name
        self.pk = pk
        self.columns = columns
        self.fkeys = fkeys


def sql2table_list(tables, show_columns=True):

    def field_act(s, loc, tok):
        return " ".join(tok).replace('\n', '\\n')

    def field_list_act(s, loc, tok):
        return tok

    def create_table_act(s, loc, tok):
        table = Table(tok["tableName"], None, {}, {})
        for t in tok["fields"]:
            if str(t).startswith("FK:"):
                l = t[3:].split(":")
                if len(l) > 2:
                    table.fkeys[l[0]] = {"ftable": l[1], "fcoloumn": l[2]}
                else:
                    table.fkeys[l[0]] = {"ftable": l[1]}

            elif str(t).startswith("PK:"):
                table.pk = t[3:]
            elif str(t).startswith("KEY:"):
                pass
            else:
                l = t.split(" ")
                table.columns[l[0]] = " ".join(l[1:])
        tables.append(table)

    def add_fkey_act(s, loc, tok):
        return '{tableName}:{keyName}:{fkTable}:{fkCol}'.format(**tok)

    def fkey_act(s, loc, tok):
        return 'FK:{keyName}:{fkTable}:{fkCol}'.format(**tok)

    def fkey_nocols_act(s, loc, tok):
        return 'FK:{keyName}:{fkTable}'.format(**tok)

    # def fkey_list_act(s, loc, tok):
    #     return "\n        ".join(tok)

    def other_statement_act(s, loc, tok):
        pass

    def join_string_act(s, loc, tok):
        return "".join(tok).replace('\n', '\\n')

    def quoted_default_value_act(s, loc, tok):
        return tok[0] + " " + "".join(tok[1::])

    def pk_act(s, loc, tok):
        return 'PK:{primary_key}'.format(**tok)

    def k_act(s, loc, tok):
        pass

    def no_act(s, loc, tok):
        pass

    string = Regex('[a-zA-Z0-9=_]+')
    ws = OneOrMore(White()).suppress()
    lp = Regex('[(]').suppress()
    rp = Regex('[)]').suppress()
    c = Regex('[,]').suppress()
    q = Regex("[`]").suppress()

    parenthesis = Forward()
    parenthesis <<= "(" + ZeroOrMore(CharsNotIn("()") | parenthesis) + ")"
    parenthesis.setParseAction(join_string_act)

    quoted_string = "'" + ZeroOrMore(CharsNotIn("'")) + "'"
    quoted_string.setParseAction(join_string_act)

    quoted_default_value = "DEFAULT" + quoted_string + OneOrMore(CharsNotIn(", \n\t"))
    quoted_default_value.setParseAction(quoted_default_value_act)

    column_comment = CaselessKeyword("COMMENT") + quoted_string

    primary_key = CaselessKeyword('PRIMARY').suppress() + CaselessKeyword("KEY").suppress() + lp +  string.setResultsName('primary_key') + rp
    primary_key.ignore("`")
    primary_key.setParseAction(pk_act)

    key_def = Optional(CaselessKeyword('UNIQUE').suppress()) + CaselessKeyword('KEY').suppress() + Word(alphanums + "_") + lp + delimitedList(string.setResultsName('key'), delim=",") + rp
    key_def.ignore("`")
    key_def.setParseAction(k_act)

    fkey_def = CaselessKeyword("CONSTRAINT") + Word(alphanums + "_") + CaselessKeyword("FOREIGN") + CaselessKeyword("KEY") + lp + Word(alphanums + "_").setResultsName("keyName") + rp + CaselessKeyword("REFERENCES") +  Word(alphanums + "._").setResultsName("fkTable") + lp + Word(alphanums + "_").setResultsName("fkCol") + rp + Optional(CaselessKeyword("DEFERRABLE")) + Optional(CaselessKeyword("ON") + (CaselessKeyword("DELETE") | CaselessKeyword("UPDATE")) + ( CaselessKeyword("CASCADE") | CaselessKeyword("RESTRICT") | CaselessKeyword("NO ACTION") | CaselessKeyword("SET NULL"))) + Optional(CaselessKeyword("ON") + (CaselessKeyword("DELETE") | CaselessKeyword("UPDATE")) + ( CaselessKeyword("CASCADE") | CaselessKeyword("RESTRICT") | CaselessKeyword("NO ACTION") | CaselessKeyword("SET NULL")))
    fkey_def.ignore("`")
    if show_columns:
        fkey_def.setParseAction(fkey_act)
    else:
        fkey_def.setParseAction(fkey_nocols_act)

    #fkey_list_def = ZeroOrMore(Suppress(",") + fkey_def)
    #fkey_list_def.setParseAction(fkey_list_act)

    field_def = Word(alphanums + "_\"':-/[].") + Word(alphanums + "_\"':-/[].") + Optional(CaselessKeyword("NOT NULL") | CaselessKeyword("DEFAULT") + Word(alphanums + "_\"':-/[].") ) + Optional(OneOrMore(quoted_default_value | column_comment | Word(alphanums + "_\"'`:-/[].") | parenthesis))
    field_def.ignore("`")

#    if columns:
    field_def.setParseAction(field_act)
#    else:
#        field_def.setParseAction(no_act)

    field_list_def = delimitedList(\
        (primary_key.suppress() | \
        key_def.suppress() | \
        fkey_def | \
        field_def \
        ), delim=","\
    )
    #if columns else field_def.suppress()
    field_list_def.setParseAction(field_list_act)

    tablename_def = (Word(alphanums + "_.") | QuotedString("\""))
    tablename_def.ignore("`")

    create_table_def = CaselessKeyword("CREATE").suppress() + CaselessKeyword("TABLE").suppress() + tablename_def.setResultsName("tableName") + lp + field_list_def.setResultsName("fields") + rp + ZeroOrMore(Word(alphanums + "_\"'`:-/[].=")) + Word(";").suppress()
    create_table_def.setParseAction(create_table_act)

    add_fkey_def = CaselessKeyword("ALTER") + "TABLE" + "ONLY" + tablename_def.setResultsName("tableName") + "ADD" + "CONSTRAINT" + Word(alphanums + "_") + "FOREIGN" + "KEY" + "(" + Word(alphanums + "_").setResultsName("keyName") + ")" + "REFERENCES" + Word(alphanums + "._").setResultsName("fkTable") + "(" + Word(alphanums + "_").setResultsName("fkCol") + ")" + Optional(Literal("DEFERRABLE")) + Optional(Literal("ON") + "DELETE" + ( Literal("CASCADE") | Literal("RESTRICT") )) + ";"
    add_fkey_def.setParseAction(add_fkey_act)

    other_statement_def = OneOrMore(CharsNotIn(";")) + ";"
    other_statement_def.setParseAction(other_statement_act)

    comment_def = "--" + ZeroOrMore(CharsNotIn("\n"))
    comment_def.setParseAction(other_statement_act)

    return OneOrMore(comment_def | create_table_def | add_fkey_def | other_statement_def)


def table_list2diagram(tables, out_file, show_columns=True):
    g = pydot.Dot(prog="dot", graph_name="Diagram", graph_type="digraph", rankdir="LR", fontsize="8", mode="ipsep", overlap="ipsep",sep="0.01", concentrate=True)
    g.set_node_defaults(color="lightblue2", style="filled", shape='box',
                            fontname="Courier", fontsize="10")

    # Create dot
    for t in tables:
        #i = find_prefix(n.get_name())
        #if i > -1:
        #    n.set

        node = pydot.Node(t.name)
        node.add_style('filled') # dotted
        #node.set("shape", 'none')

        for k, v in t.fkeys.items():
            style = "filled"
            #if t.columns[k]["nullable"]:
            #    style = "dotted"
            g.add_edge(pydot.Edge(t.name, v["ftable"])) # , style="filled", arrowtail="crow"

        tooltip = ""
        for k in t.columns.keys():
            tooltip += k + " " + t.columns[k] + "\n"
        node.set("tooltip", tooltip)
        g.add_node(node)


    (preext, ext) = os.path.splitext(out_file)
    if ext == ".svg":
        g.write_svg(out_file)
    elif ext == ".png":
        g.write_png(out_file)
    elif ext == ".svgz":
        g.write_svgz(out_file)
    elif ext == ".dot":
        with open(out_file, 'w') as f:
            f.write(g.to_string())
    else:
        sys.stderr.write("Unsupported output file extension: %s\n" % ext)

if __name__ == '__main__':

    def print_usage():
      print("""Syntax: %s [-n] <-i sql_file> <-o out_file>
      Arguments:
           -h|--help : display this help
           -n|--nocols : don't include columns
           -i|--input : sql file with 'CREATE TABLE' statements
           -o|--output : output file (supported formats: .svg .png .jpg .dot)""" % sys.argv[0])

    sql_file = None
    out_file = None
    show_columns = True

    # Get command-line arguments
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hi:o:n", ["help", "input", "output", "nocols"])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    for o,a in opts:
        if o in ("-h", "--help"):
            print_usage()
            sys.exit()
        elif o in ("-i", "--input"):
            sql_file = a
        elif o in ("-o", "--output"):
            out_file = a
        elif o in ("-n", "--nocols"):
            show_columns = False

    # Sanity check
    if sql_file is None or out_file is None:
        print_usage()
        sys.exit()

    tables = []
    sql2table_list(tables, show_columns).setDebug(False).parseFile(sql_file)
    table_list2diagram(tables, out_file, show_columns)
