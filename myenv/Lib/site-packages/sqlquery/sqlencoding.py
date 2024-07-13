import contextlib

from datetime import datetime
from datetime import date

import six


class _Func(str):
    pass


class Literal(object):
    def __init__(self, value):
        self.value = value


class BasicEncodings(object):
    OPERATOR_MAPPING = {
        # Comparison
        'eq': "=",
        'neq': "<>",
        'gte': ">=",
        'gt': ">",
        'lt': "<",
        'is': "IS",
        'isnot': "IS NOT",
        'like': "LIKE",
        "in": "IN",
        "not_in": "NOT IN",

        # Arithmetic
        'idiv': "DIV",
        'div': "/",
        'mult': "*",
        'add': "+",
        'sub': "-",
        'mod': "%",
    }

    FUNC_MAPPING = {
        'if': "IF",
        'count': "COUNT",
        'avg': "AVG",
        'max': "MAX",
        'min': "MIN",
        'sum': "SUM",
        'utcnow': "UTC_TIMESTAMP",
        'unix_timestamp': "UNIX_TIMESTAMP",
    }

    SQL_NULL = "NULL"

    ORDERING_MAPPING = {
        "asc": "ASC",
        "desc": "DESC",
    }

    BOOLEAN_MAPPING = {
        "and": "AND",
        "or": "OR",
        "xor": "XOR",
    }

    JOIN_TYPES_MAPPING = {
        "inner": "INNER JOIN",
        "outer": "OUTER JOIN",
    }

    @contextlib.contextmanager
    def in_brackets(self, query):
        query.append("(")
        yield
        query.append(")")

    def encode_null(self):
        return self.SQL_NULL

    def quoted(self, element):
        if element.startswith("`") and element.endswith("`"):
            return element
        return u"`{!s}`".format(element)

    def stringified(self, element):
        return "'{}'".format(element)

    def encode_func_name(self, funcname):
        sql_func = self.FUNC_MAPPING.get(funcname, funcname)
        return _Func(sql_func)

    def encode_op(self, op):
        return self.OPERATOR_MAPPING[op]

    def encode_logical_op(self, op):
        return self.BOOLEAN_MAPPING[op]

    def encode_order_by_dir(self, direction):
        return self.ORDERING_MAPPING[direction]

    def encode_join_type(self, join_type):
        return self.JOIN_TYPES_MAPPING[join_type]

    def marshal_python_value(self, value):
        if isinstance(value, six.string_types):
            return value

        if isinstance(value, bool):
            return str(int(value))

        if isinstance(value, six.integer_types):
            return str(value)

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        return value

    def split_literals_from_values(self, values):
        literals = [x for x in values if isinstance(x, Literal)]
        non_literals = [x for x in values if not isinstance(x, Literal)]
        return literals, non_literals

    def encode_value(self, value, table_name,
                     table_alias, include_alias=True):
        if isinstance(value, Literal):
            marshalled = self.marshal_python_value(value.value)
            if isinstance(value.value, (six.string_types, datetime, date)):
                return [self.stringified(marshalled)], []

            return [marshalled], []

        if (
            not isinstance(value, six.string_types) or
            not value.startswith(table_name + '.')
        ):
            return ["%s"], [value]

        value = value[len(table_name + '.'):]
        if include_alias:
            prefix = table_alias
        else:
            prefix = table_name

        return [self.quoted(prefix) + '.' + self.quoted(value)], []

    def encode_field(self, field, table_name,
                     table_alias, include_alias=True):
        if isinstance(field, Literal):
            return self.marshal_python_value(field.value)

        field = self.marshal_python_value(field)
        if not include_alias:
            return self.quoted(field)

        prefix = table_alias
        if field.startswith(table_name + '.'):
            field = field[len(table_name + '.'):]
            prefix = table_alias

        return self.quoted(prefix) + '.' + self.quoted(field)

    def encode_table_name(self, table_name, table_alias, table_schema,
                          include_alias=True):
        if table_schema:
            name = "{}.{}".format(
                self.quoted(table_schema), self.quoted(table_name)
            )
        else:
            name = self.quoted(table_name)

        if not include_alias:
            return name

        return (
            name
            + " AS "
            + self.quoted(table_alias)
        )

    def is_space(self, value):
        return len(value.strip()) == 0

    def is_literal(self, value):
        return isinstance(value, Literal)

    def is_function(self, value):
        return isinstance(value, _Func)

    def should_skip_next_space(self, token, next_token):
        return (
            self.is_function(token) or
            token.endswith("(") or
            next_token.startswith(")") or
            token.endswith(" ") or
            next_token.startswith(" ") or
            token.endswith(",") or
            next_token.startswith(",")
        )

    def spaced_query(self, query):
        if not isinstance(query, list):
            query = list(query)

        final_index = len(query) - 1
        for index, token in enumerate(query):
            if self.is_space(token) and index in (0, final_index):
                continue

            yield token

            if index == final_index:
                continue

            next_token = query[index + 1]
            if self.should_skip_next_space(token, next_token):
                continue

            yield " "

    def serialize_query_tokens(self, query):
        return u"".join(map(str, self.spaced_query(query)))


class ANSIEncodings(BasicEncodings):
    def quoted(self, element):
        if element.startswith('"') and element.endswith('"'):
            return element
        return u'"{!s}"'.format(element)
