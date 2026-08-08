from src.core.db import get_connection


def test_accounts_read_access():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM public.accounts
        LIMIT 5;
    """)

    rows = cur.fetchall()

    print("Accounts Sample:")
    for row in rows:
        print(row)

    assert len(rows) > 0
