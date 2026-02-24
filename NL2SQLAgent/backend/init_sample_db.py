"""初始化示例业务数据库 sample.db，填充模拟数据用于演示查询。"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "sample.db"

CATEGORIES = ["电子产品", "服装", "食品", "家居", "图书"]
REGIONS = ["华东", "华南", "华北", "华中", "西南", "西北", "东北"]
LEVELS = ["普通", "银卡", "金卡", "钻石"]

PRODUCTS = [
    ("智能手机", "电子产品", 3999),
    ("笔记本电脑", "电子产品", 6999),
    ("无线耳机", "电子产品", 599),
    ("平板电脑", "电子产品", 2999),
    ("智能手表", "电子产品", 1299),
    ("运动T恤", "服装", 129),
    ("牛仔裤", "服装", 259),
    ("羽绒服", "服装", 899),
    ("运动鞋", "服装", 499),
    ("休闲外套", "服装", 399),
    ("进口牛排", "食品", 168),
    ("有机牛奶", "食品", 68),
    ("坚果礼盒", "食品", 128),
    ("精品咖啡", "食品", 88),
    ("智能台灯", "家居", 199),
    ("记忆棉枕头", "家居", 159),
    ("空气净化器", "家居", 1299),
    ("Python编程", "图书", 79),
    ("数据分析实战", "图书", 69),
    ("AI入门指南", "图书", 59),
]

FIRST_NAMES = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
LAST_NAMES = ["伟", "芳", "强", "敏", "静", "磊", "洋", "勇", "娜", "涛"]


def create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            level TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)


def seed_data(conn: sqlite3.Connection):
    random.seed(42)

    conn.executemany(
        "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
        PRODUCTS,
    )

    customers = []
    for i in range(50):
        name = random.choice(FIRST_NAMES) + random.choice(LAST_NAMES) + str(i)
        region = random.choice(REGIONS)
        level = random.choice(LEVELS)
        customers.append((name, region, level))
    conn.executemany(
        "INSERT INTO customers (name, region, level) VALUES (?, ?, ?)",
        customers,
    )

    orders = []
    base_date = datetime(2025, 1, 1)
    for _ in range(200):
        customer_id = random.randint(1, 50)
        product_id = random.randint(1, len(PRODUCTS))
        quantity = random.randint(1, 5)
        price = PRODUCTS[product_id - 1][2]
        amount = round(price * quantity, 2)
        days_offset = random.randint(0, 364)
        order_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        orders.append((customer_id, product_id, quantity, amount, order_date))
    conn.executemany(
        "INSERT INTO orders (customer_id, product_id, quantity, amount, order_date) VALUES (?, ?, ?, ?, ?)",
        orders,
    )

    conn.commit()


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        create_tables(conn)
        seed_data(conn)
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        print(f"sample.db 初始化完成: {len(PRODUCTS)} 个产品, 50 个客户, {count} 条订单")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
