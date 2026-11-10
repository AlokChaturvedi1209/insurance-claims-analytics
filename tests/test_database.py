from insurance_analytics.database import split_sql_statements


def test_split_sql_statements_ignores_comments_and_quoted_semicolons():
    sql = """
    -- leading documentation; this is not a statement;
    /* block documentation; including a semicolon; */
    CREATE TABLE example (note TEXT DEFAULT 'value;still quoted');
    -- another comment; with a semicolon;
    INSERT INTO example VALUES ($tag$body; still quoted$tag$);
    """

    assert split_sql_statements(sql) == [
        "CREATE TABLE example (note TEXT DEFAULT 'value;still quoted')",
        'INSERT INTO example VALUES ($tag$body; still quoted$tag$)',
    ]
