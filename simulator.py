import psycopg2
import faker
from datetime import datetime
import random
import argparse
import os
import sys

fake = faker.Faker()

def generator_transactions(n):
    transactions = []
    for _ in range(n):
        user = fake.simple_profile()
        transaction = {
            'transaction_id': fake.uuid4(),
            'user_id': user['username'],
            'amount': fake.random_number(digits=7)/100,
            'timestamp': datetime.utcnow().timestamp(),
            'currency': fake.random_element(elements=(*['USD'] * 5, *['EUR'] * 30, *['GBP'] * 55, *['CHF'] * 10)),
            'city': fake.city(),
            'country': fake.country(),
            'ip_address': fake.ipv4(),
            'payment_method': fake.random_element(elements=('credit_card', 'debit_card', 'paypal', 'bank_transfer')),
            'voucher_code': random.choice([*[''] * 20, 'DISCOUNT10', 'FREESHIP', 'SUMMER21', 'WELCOME']),
            'affiliate_id': fake.uuid4(),
            'status': fake.random_element(elements=(*['completed'] * 95, 'pending', 'failed')),
        }
        transactions.append(transaction)
    return transactions

def create_table(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                transaction_id UUID PRIMARY KEY,
                user_id VARCHAR(255),
                amount NUMERIC(10, 2),
                timestamp TIMESTAMP,
                currency VARCHAR(3),
                city VARCHAR(255),
                country VARCHAR(255),
                ip_address VARCHAR(15),
                payment_method VARCHAR(50),
                voucher_code VARCHAR(50),
                affiliate_id UUID,
                status VARCHAR(50)
            )
        """)
        conn.commit()
    
    with conn.cursor() as cur:
        cur.execute(f"ALTER TABLE {table_name} REPLICA IDENTITY FULL") # we need this to check the 'before' and 'after' values in the trigger - temp workaround
        conn.commit()


def insert_transactions(conn, transactions, table_name):
    with conn.cursor() as cur:
        for transaction in transactions:
            cur.execute(f"""
                INSERT INTO {table_name} (transaction_id, user_id, amount, timestamp, currency, city, country, ip_address, payment_method, voucher_code, affiliate_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (transaction_id) DO NOTHING
            """, (
                transaction['transaction_id'],
                transaction['user_id'],
                transaction['amount'],
                datetime.fromtimestamp(transaction['timestamp']),
                transaction['currency'],
                transaction['city'],
                transaction['country'],
                transaction['ip_address'],
                transaction['payment_method'],
                transaction['voucher_code'],
                transaction['affiliate_id'],
                transaction['status']
            ))
        return(conn.commit())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate simulated transactions and store them in a PostgreSQL database.')
    #check if run is present in the command line, is so proceed, if not show help

    parser.add_argument('--run',        action ='store_true',                                                           help='Run script - necessary to generate transactions, if empty command line arguments.')
    parser.add_argument('--count',      type=int,  default     = os.getenv('SIMULATOR_COUNT', 10),                      help='Number of transactions to generate')
    parser.add_argument('--db',         type=str,  default     = os.getenv('SIMULATOR_DATABASE_NAME', 'default_db'),    help='Database name, will not be created if it does not exist')
    parser.add_argument('--table-name', type=str,  default     = os.getenv('SIMULATOR_DATABASE_TABLE', 'transactions'), help='Table name')
    parser.add_argument('--user',       type=str,  default     = os.getenv('SIMULATOR_DATABASE_USER', 'postgres'),      help='Database user')
    parser.add_argument('--password',   type=str,  default     = os.getenv('SIMULATOR_DATABASE_PASSWORD', 'postgres'),  help='Database password')
    parser.add_argument('--host',       type=str,  default     = os.getenv('SIMULATOR_DATABASE_HOST', 'localhost'),     help='Database host')
    parser.add_argument('--port',       type=int,  default     = os.getenv('SIMULATOR_DATABASE_PORT', 5432),            help='Database port')
    if len(sys.argv) == 1:
        print("No arguments provided. Use --help for more information.")
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    print(f"Arguments:\n {args}")

    try:
        conn = psycopg2.connect(
            dbname=args.db,
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port
        )

        print("Connected to the database.")

    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit(1)

    else:
        transactions = generator_transactions(args.count)
        print(f"Generated {len(transactions)} transactions.")
        create_table(conn, args.table_name)
        insert_transactions(conn, transactions, args.table_name)

    finally:
        print("Done")
    