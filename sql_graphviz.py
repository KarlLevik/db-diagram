#!/usr/bin/env python

import html
import sys
import os
from datetime import datetime
import getopt
from pyparsing import alphas, alphanums, Literal, Word, Forward, OneOrMore, ZeroOrMore, CharsNotIn, Suppress, QuotedString, Optional, Keyword, CaselessKeyword, NotAny, Combine, White, Regex, delimitedList, commaSeparatedList
import pydot

table_colours = ["#800000", "#9A6324", "#808000", "#469990", "#000075", "#000000", "#e6194B", "#f58231", "#ffe119", "#bfef45", "#3cb44b", "#42d4f4", "#4363d8", "#911eb4", "#f032e6", "#a9a9a9", "#fabebe", "#ffd8b1", "#fffac8", "#aaffc3", "#e6beff", "#ffffff"]

text_colours = ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#000000", "#000000", "#ffffff", "#000000", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#000000", "#000000", "#000000", "#000000", "#000000", "#000000"]

def field_act(s, loc, tok):
    fieldName = tok[0].replace('"', '')
    fieldSpec = html.escape(' '.join(tok[1::]).replace('"', '\\"'))
    return '<tr><td bgcolor="grey96" align="left" port="{0}"><font face="Times-bold">{0}</font>  <font color="#535353">{1}</font></td></tr>'.format(fieldName, fieldSpec)

def field_list_act(s, loc, tok):
    return "".join([t + "\n" for i,t in enumerate(tok) if t != ""])

def create_table_act(s, loc, tok):
    fks = ""
    fields = ""
    if "fields" in tok:
        for field in tok["fields"].split("\n"):
            if field.startswith("FK:"):
                if len(field[3:].split(":")) > 1:
                    fks +='  "' + tok["tableName"] + '":' + field[3:] + "\n"
                else:
                    fks +='  "' + tok["tableName"] + '"' + field[3:] + "\n"
            else:
                fields += "        " + field + "\n"

    tok["fields"] = fields
    tok["fks"] = fks

    return '''
  "{tableName}" [
    shape=none
    label=<
      <table border="0" cellspacing="0" cellborder="1">
        <tr><td bgcolor="lightblue2"><font face="Times-bold" point-size="20">{tableName}</font></td></tr>
        {fields}
      </table>
    >];
    {fks}'''.format(**tok)

def add_fkey_act(s, loc, tok):
    return '  "{tableName}":{keyName} -> "{fkTable}":{fkCol}'.format(**tok)

def fkey_act(s, loc, tok):
    return 'FK:{keyName} -> "{fkTable}":{fkCol}'.format(**tok)

def fkey_nocols_act(s, loc, tok):
    return 'FK: -> "{fkTable}"'.format(**tok)

def fkey_list_act(s, loc, tok):
    return "\n        ".join(tok)

def other_statement_act(s, loc, tok):
    return ""

def join_string_act(s, loc, tok):
    return "".join(tok).replace('\n', '\\n')

def quoted_default_value_act(s, loc, tok):
    return tok[0] + " " + "".join(tok[1::])

def pk_act(s, loc, tok):
    return ""

def k_act(s, loc, tok):
    return ""

def no_act(s, loc, tok):
    return ""

def grammar(columns=True):
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
    if columns:
        fkey_def.setParseAction(fkey_act)
    else:
        fkey_def.setParseAction(fkey_nocols_act)

    #fkey_list_def = ZeroOrMore(Suppress(",") + fkey_def)
    #fkey_list_def.setParseAction(fkey_list_act)

    field_def = OneOrMore(quoted_default_value | column_comment | Word(alphanums + "_\"'`:-/[].") | parenthesis)
    if columns:
        field_def.setParseAction(field_act)
    else:
        field_def.setParseAction(no_act)

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


def graphviz(filename, out_file, columns=True):
    dot_string = """
    /*
     * Graphviz of '%s', created %s
     * Generated from https://github.com/rm-hull/sql_graphviz
     */
    digraph g { graph [ rankdir = \"LR\" ];""" % (filename, datetime.now())

    results = grammar(columns).setDebug(False).parseFile(filename)
    for i in results:
        if i != "":
            dot_string += i
    dot_string += "}"

    graphs = pydot.graph_from_dot_data( dot_string )
    (preext, ext) = os.path.splitext(out_file)
    if ext == ".svg":
        graphs[0].write_svg(out_file)
    elif ext == ".png":
        graphs[0].write_png(out_file)
    else:
        sys.stderr.write("Unsupported output file extension: %s\n" % ext)

if __name__ == '__main__':

    def print_usage():
      print("""Syntax: %s [-n] <-i sql_file> <-o out_file>
      Arguments:
           -h|--help : display this help
           -n|--nocols : don't include columns
           -i|--input : sql file with 'CREATE TABLE' statements
           -o|--output : output file (only .svg + .png support so far)""" % sys.argv[0])

    sql_file = None
    out_file = None
    columns = True

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
            columns = False

    # Sanity check
    if sql_file is None or out_file is None:
        print_usage()
        sys.exit()

    graphviz(sql_file, out_file, columns)
