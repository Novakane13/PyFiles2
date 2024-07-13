import string
import itertools
import collections
from collections import namedtuple
from sqlquery.sqlencoding import BasicEncodings
from sqlquery.sqlencoding import Literal

from six import string_types


class InvalidQueryException(Exception):
    """
    Raised whenever invalid data is found when the query is being created via
    :py:meth:`.QueryBuilder.sql`
    """
    pass


def logical_and(conditions):
    return _LogicalOperator(conditions, "and")


def logical_or(conditions):
    return _LogicalOperator(conditions, "or")


def logical_xor(conditions):
    return _LogicalOperator(conditions, "xor")


def if_(condition, then_expr, else_expr):
    return SQLFunction("if", logical_and([condition]), then_expr, else_expr)


def count(field):
    return SQLFunction("count", field or Literal(1))


def max(field):
    return SQLFunction("max", field)


def min(field):
    return SQLFunction("min", field)


def sum(field):
    return SQLFunction("sum", field)


def utcnow():
    return SQLFunction("utcnow")


def unix_timestamp():
    return SQLFunction("unix_timestamp")


def order_descending(field):
    return _SQLOrdering(field, "desc")


def order_ascending(field):
    return _SQLOrdering(field, "asc")


class _LogicalOperator(object):
    def __init__(self, conditions, operator):
        self.conditions = conditions
        self.operator = operator


class SQLFunction(object):
    def __init__(self, function, *expressions):
        self.function = function
        self.expressions = expressions


class _SQLOrdering(object):
    def __init__(self, field, direction):
        self.field = field
        self.direction = direction


TableOptions = namedtuple(
    'TableOptions',
    [
        'schema',
        'name',
        'alias'
    ]
)


JoinOptions = namedtuple(
    'JoinOptions',
    [
        'join_type',
        'main_field',
        'join_field',
        'table'
    ]
)


QueryData = namedtuple(
    'QueryData',
    [
        'select',
        'update',
        'insert',
        'delete',
        'table',
        'where',
        'order_by',
        'group_by',
        'having',
        'offset',
        'limit',
        'duplicate_key_update',
        'insert_ignore',
        'insert_replace',
        'join',
    ]
)


_empty_query_data = QueryData(**{field: None for field in QueryData._fields})


class QueryBuilder(object):
    """
    This is the main workhorse for modifying/creating queries.
    Unless otherwise stated, all methods return a copy of the class and do not
    modifying the query of the reference class. This allows both method
    chaining and the ability to easily reuse queries.
    """
    def __init__(self, query_data=None):
        if not query_data:
            query_data = _empty_query_data

        self._query_data = query_data

    def _replace(self, **kwargs):
        return self.copy(self._query_data._replace(**kwargs))

    def copy(self, new_query_data):
        """
        Returns a copy of this class.
        """
        return self.__class__(new_query_data)

    def select(self, *names):
        """
        See :py:func:`~.queryapi.select`
        """
        return self._replace(select=names)

    def update(self, **data):
        """
        See :py:func:`~.queryapi.update`
        """
        return self._replace(update=data)

    def insert(self, *data):
        """
        See :py:func:`~.queryapi.insert`
        """
        assert all(isinstance(x, dict) for x in data)
        return self._replace(insert=data)

    def insert_ignore(self, *data):
        """
        See :py:func:`~.queryapi.insert_ignore`
        """
        ret = self.insert(*data)
        return ret._replace(insert_ignore=True)

    def replace(self, *data):
        """
        See :py:func:`~.queryapi.replace`
        """
        ret = self.insert(*data)
        return ret._replace(insert_replace=True)

    def delete(self):
        """
        See :py:func:`~.queryapi.delete`
        """
        return self._replace(delete=True)

    def on_table(self, table, schema=None):
        """
        Identifies the main table the query should be executed upon. E.g. if
        `table` were `users` then the equivalent result would be:

        ::

            SELECT * FROM users

        """
        if not self._query_data.table:
            table = TableOptions(name=table, schema=schema, alias=None)
        else:
            table = self._query_data.table._replace(table=table, schema=schema)
        return self._replace(table=table)

    def on_duplicate_key_update(self, **col_values):
        """
        With one of the insertion statements, this causes an `UPDATE` to be
        executed if the insert causes an integrity error. Generates the
        relevant

        ::

            INSERT ... ON DUPLICATE KEY UPDATE ...

        *col_values* should be a list of columns/values to be updated. If
        column/values is not given, then the main columns will be used
        resulting in a query like:

        ::

            INSERT INTO table (x) VALUES (1)
            ON DUPLICATE KEY UPDATE x = VALUES(1)

        """
        return self._replace(duplicate_key_update=(True, col_values))

    def where(self, *conditions):
        """
        Used to create a `WHERE` clause. All items in *conditions* must either
        be a tuple of the form:

        ::

            >>> ("column__operator", value)

        where `column` is the name of the DB column. `operator` should be one
        of the comparison operators support as specified in
        :py:data:`.sqlencoding.OPERATOR_MAPPING`. These two are joined
        together in a string, separated by ``__``.
        `value` should either be a raw value (which will be part of the
        arguments returned and not included in the query itself), a
        `:py:class:Literal` (which will be part of the query and not arguments
        - use carefully, this will not undergo sanitization) or a "column
        reference" (this is achieved by prefixing the table name followed by a
        period, e.g. `table.column`).

        Alteratively an item can represent a complex condition joined by a
        boolean operator like `AND`. You can use the

        :py:func:`~.queryapi.AND`
        :py:func:`~.queryapi.OR`
        :py:func:`~.queryapi.XOR`

        functions in this module to created these. For example

        ::

            >>> QueryBuilder().where(
                    logical_or(("field__eq", 2), ("field2__eq", 4))
                )
        """
        assert conditions
        return self._replace(where=logical_and(conditions))

    def join(self, join_table, main_field, join_field=None, schema=None):
        """
        Joins the current query with the given *join_table* on *join_field*
        which is a field on *join_table* and *main_field* which is a field
        represented on the current table.

        If *join_field* is not given then it uses *main_field* on the
        *join_table*.
        """
        return self._replace(
            join=JoinOptions(
                join_type="inner",
                main_field=main_field,
                join_field=join_field or main_field,
                table=TableOptions(
                    name=join_table,
                    schema=schema,
                    alias=None
                )
            )
        )

    def having(self, *conditions):
        """
        Used to create a `HAVING` clause. The *conditions* argument has the
        same semantics as in :py:meth:`~.where`
        """
        assert conditions
        return self._replace(having=logical_and(conditions))

    def order_by(self, *fields):
        """
        Used to create an `ORDER BY` clause. Each item in *fields* should be a
        column name or you can use the
        :py:func:`~.queryapi.ASC`
        :py:func:`~.queryapi.DESC`
        to change the ordering of the field.
        For example

        ::

            >>> QueryBuilder().order_by(DESC("field1"), "field2")

        will make an ORDER BY clause which would create something equivalent
        to:

        ::

            ORDER BY field1 DESC, field2

        """
        assert all(
            [isinstance(field, (string_types, _SQLOrdering))
             for field in fields]
        )
        return self._replace(order_by=tuple(fields))

    def group_by(self, *fields):
        """
        Used to create a `GROUP BY` clause. Each item in *fields* should be a
        column name.
        """
        assert all(
            [isinstance(field, string_types) for field in fields]
        )
        return self._replace(group_by=tuple(fields))

    def offset(self, offset):
        """
        Used to create an `OFFSET` clause. Warning, this may result in an
        ineffecient query if a large offset is chosen.
        """
        return self._replace(offset=int(offset))

    def limit(self, count):
        """
        Used to create an `LIMIT` clause. This reduces the number of rows that
        will be returned.
        """
        return self._replace(limit=int(count))

    def compiler(self, encoder=None):
        """
        Returns the compiler that will be used to generate the final query. In
        most cases you won't need to call this, and instead :py:meth:`~.sql`
        will all that's needed.
        """
        return SQLCompiler(self._query_data, encoder=encoder)

    def sql(self, encoder=None):
        """
        Composes the current query and returns a tuple containing:

        ::

            >>> ("<query_string>",
                 (
                     # tuple of arguments
                 )
                )

        `query_string` is the final string that can be passed to the DB client
        library. `arguments` is the list of arguments that are required for the
        query and should also be passed to the DB client library. Each argument
        will have a "%s" placeholder in the query string.
        """
        return self.compiler(encoder=encoder).sql()


def _query_joiner(query, iterable, join_with=", "):
    for index, data in enumerate(iterable):
        yield data
        if len(iterable) > 1 and index < len(iterable) - 1:
            query.append(join_with)


class _QueryState(object):
    def __init__(self, query=None, args=None):
        self.query = query or []
        self.args = args or []

    def extend(self, query=None, args=None):
        if query:
            self.query.extend(list(query))
        if args:
            self.args.extend(list(args))

    def append(self, query=None, arg=None):
        if query:
            self.query.append(query)
        if arg:
            self.args.append(arg)

    def __len__(self):
        return 2

    def __iter__(self):
        return iter((self.query, self.args))

    def __str__(self):
        return "<_QueryState: {}: {}>".format(self.query, self.args)


class SQLCompiler(object):
    def __init__(self, query_data, alias_gen=None, encoder=None):
        # generate the aliases
        self._encoder = encoder or BasicEncodings()
        if alias_gen:
            self.alias_gen = alias_gen
        else:
            self.alias_gen = itertools.cycle(string.ascii_lowercase)

        query_data = query_data._replace(
            table=query_data.table._replace(alias=next(self.alias_gen))
        )
        if query_data.join:
            query_data = query_data._replace(
                join=query_data.join._replace(
                    table=query_data.join.table._replace(
                        alias=next(self.alias_gen)
                    )
                )
            )
        self.query_data = query_data

    # Encoding to valid SQL functions
    def _encode_main_table_name(self, include_alias=True):
        return self._encoder.encode_table_name(
            self.query_data.table.name,
            self.query_data.table.alias,
            self.query_data.table.schema,
            include_alias=include_alias
        )

    def _encode_join_table_name(self):
        return self._encoder.encode_table_name(
            self.query_data.join.table.name,
            self.query_data.join.table.alias,
            self.query_data.join.table.schema,
            include_alias=True
        )

    def _encode_field(self, field):
        return self._encoder.encode_field(
            field,
            self.query_data.table.name,
            self.query_data.table.alias,
            include_alias=True
        )

    def _encode_value(self, value):
        return self._encoder.encode_value(
            value,
            self.query_data.table.name,
            self.query_data.table.alias,
            include_alias=True
        )

    def _encode_join_field(self, field):
        return self._encoder.encode_field(
            field,
            self.query_data.join.table.name,
            self.query_data.join.table.alias,
            include_alias=True
        )

    def _smart_encode_field(self, field):
        if (
            self.query_data.join and
            isinstance(field, string_types) and
            field.startswith(self.query_data.join.table.name + '.')
        ):
            return self._encode_join_field(field)

        return self._encode_field(field)

    def _quoted(self, value):
        return self._encoder.quoted(value)

    # Parsing user-data functions
    @staticmethod
    def _parse_field_spec(field_spec):
        """
        Returns (func, field, op)
        """
        try:
            field, op = field_spec.split('__')
            return field, op
        except ValueError:
            raise InvalidQueryException(
                "Invalid where clause <{}>".format(field_spec)
            )

    def _parse_where_clause_spec(self, clause):
        if isinstance(clause, dict):
            assert len(clause) == 1
            clause = clause.items()

        if isinstance(clause, (tuple, list)):
            if len(clause) == 3:
                return clause
            if len(clause) == 2:
                field_op, value = clause
                field, op = self._parse_field_spec(field_op)
                return field, op, value

        raise InvalidQueryException("Unknown where element %s" % clause)

    # Generating sequences of valid SQL functions
    def _generate_field(self, field):
        state = _QueryState()
        if isinstance(field, SQLFunction):
            func = self._encoder.encode_func_name(field.function)
            state.query.append(func)
            with self._encoder.in_brackets(state.query):
                for field in _query_joiner(state.query, field.expressions):
                    state.extend(*self._generate_field(field))
        elif isinstance(field, _LogicalOperator):
            state.extend(*self._generate_conditional(field))
        else:
            state.append(self._smart_encode_field(field))

        return state

    def _generate_join(self):
        return _QueryState(
            [
                self._encoder.encode_join_type(self.query_data.join.join_type),
                self._encode_join_table_name(),
                u"ON",
                self._encode_field(self.query_data.join.main_field),
                u"=",
                self._encode_join_field(self.query_data.join.join_field),
            ]
        )

    def _generate_update(self):
        state = _QueryState([
            u"UPDATE",
            self._encode_main_table_name(),
        ])
        if self.query_data.join:
            state.extend(*self._generate_join())

        state.append("SET")
        for field in _query_joiner(state, self.query_data.update):
            state.append(self._encode_field(field))
            state.append(u"=")
            state.append(u"%s", self.query_data.update[field])

        return state

    def _generate_insert(self):
        if self.query_data.insert_ignore:
            insert = u"INSERT IGNORE INTO"
        elif self.query_data.insert_replace:
            insert = u"REPLACE INTO"
        else:
            insert = u"INSERT INTO"

        state = _QueryState([
            insert,
            self._encode_main_table_name(include_alias=False),
        ])
        columns = self.query_data.insert[0].keys()
        with self._encoder.in_brackets(state):
            state.append(u", ".join(map(self._quoted, columns)))
        state.append(u"VALUES")

        for col_values in self.query_data.insert:
            if len(col_values.keys()) != len(columns):
                raise InvalidQueryException("Invalid number of column values")

            with self._encoder.in_brackets(state):
                for col in _query_joiner(state, columns):
                    state.append(u"%s", col_values[col])

        if self.query_data.duplicate_key_update:
            state.append(u"ON DUPLICATE KEY UPDATE")
            update_col_values = self.query_data.duplicate_key_update[1]
            if not update_col_values:
                for col in _query_joiner(state, columns):
                    state.append(u"{0}=VALUES({0})".format(self._quoted(col)))
            else:
                for col in _query_joiner(state, update_col_values):
                    state.append(
                        u"{}=VALUES(%s)".format(self._quoted(col)),
                        update_col_values[col]
                    )

        return state

    def _generate_select(self):
        state = _QueryState([u"SELECT"])
        for field in _query_joiner(state, self.query_data.select):
            state.extend(*self._generate_field(field))

        state.extend(["FROM", self._encode_main_table_name()])
        if self.query_data.join:
            state.extend(*self._generate_join())
        return state

    def _generate_single_where_clause(self, field, op, value):
        state = _QueryState()
        with self._encoder.in_brackets(state):
            state.extend(*self._generate_field(field))

            state.append(self._encoder.encode_op(op))
            if isinstance(value, QueryBuilder):
                with self._encoder.in_brackets(state):
                    state.extend(
                        *list(SQLCompiler(
                            value._query_data, self.alias_gen
                        )._raw_sql())
                    )
            elif value is None:
                state.append(self._encoder.encode_null())
            elif (
                not isinstance(value, string_types) and
                isinstance(value, collections.Iterable)
            ):
                with self._encoder.in_brackets(state):
                    for single_value in _query_joiner(state, value,
                                                      join_with=","):
                        state.extend(*self._encode_value(single_value))
            else:
                state.extend(*self._encode_value(value))

        return state

    def _generate_conditional(self, clause):
        state = _QueryState()
        for sub_clause in _query_joiner(
            state,
            clause.conditions,
            self._encoder.encode_logical_op(clause.operator)
        ):
            if isinstance(sub_clause, _LogicalOperator):
                with self._encoder.in_brackets(state):
                    state.extend(*self._generate_conditional(sub_clause))
            else:
                field, op, value = self._parse_where_clause_spec(sub_clause)
                state.extend(*self._generate_single_where_clause(
                    field, op, value
                ))

        return state

    def _generate_where(self):
        if not self.query_data.where:
            return _QueryState()

        state = _QueryState([u"WHERE"])
        state.extend(*self._generate_conditional(self.query_data.where))
        return state

    def _generate_offset(self):
        if self.query_data.offset is None:
            return _QueryState()

        return _QueryState([u"OFFSET %s"], [self.query_data.offset])

    def _generate_limit(self):
        if self.query_data.limit is None:
            return _QueryState()

        return [u"LIMIT %s"], [self.query_data.limit]

    def _generate_order_by(self):
        if not self.query_data.order_by:
            return _QueryState()

        state = _QueryState([u"ORDER BY"])
        for order_by in _query_joiner(state, self.query_data.order_by):
            if isinstance(order_by, string_types):
                state.append(self._smart_encode_field(order_by))
            else:
                state.extend(
                    [
                        self._smart_encode_field(order_by.field),
                        self._encoder.encode_order_by_dir(order_by.direction)
                    ]
                )

        return state

    def _generate_group_by(self):
        if not self.query_data.group_by:
            return _QueryState()

        state = _QueryState([u"GROUP BY"])
        for field in _query_joiner(state, self.query_data.group_by):
            state.append(self._smart_encode_field(field))

        return state

    def _generate_having(self):
        if not self.query_data.having:
            return _QueryState()

        state = _QueryState([u"HAVING"])
        state.extend(*self._generate_conditional(self.query_data.having))
        return state

    def _generate_query_operation(self):
        if self.query_data.select:
            return self._generate_select()

        if self.query_data.delete is True:
            return _QueryState([u"DELETE"])

        if self.query_data.update is not None:
            return self._generate_update()

        if self.query_data.insert is not None:
            return self._generate_insert()

        raise InvalidQueryException

    def _raw_sql(self):
        if not self.query_data.table:
            raise Exception("requires both select and from")

        main = self._generate_query_operation()
        where = self._generate_where()
        group_by = self._generate_group_by()
        having = self._generate_having()
        order_by = self._generate_order_by()
        offset = self._generate_offset()
        limit = self._generate_limit()

        query, args = zip(
            main, where, group_by, having, order_by, offset, limit
        )
        return (
            itertools.chain(*query), tuple(itertools.chain(*args))
        )

    def sql(self):
        sql, sql_args = self._raw_sql()

        return (
            self._encoder.serialize_query_tokens(sql),
            sql_args
        )
