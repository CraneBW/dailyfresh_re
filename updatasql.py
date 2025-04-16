import pymysql
from datetime import datetime

# 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'dailyfresh',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 目标时间
target_time = datetime(2025, 3, 25, 12, 30, 0)
target_time_str = target_time.strftime('%Y-%m-%d %H:%M:%S')

try:
    # 连接数据库
    connection = pymysql.connect(**db_config)

    with connection.cursor() as cursor:
        # 1. 查找所有包含create_time字段的表
        cursor.execute("""
            SELECT DISTINCT TABLE_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND COLUMN_NAME = 'create_time'
        """, (db_config['db'],))

        tables = cursor.fetchall()

        if not tables:
            print("没有找到包含create_time字段的表")
            exit()

        # 2. 对每个表执行更新
        for table in tables:
            table_name = table['TABLE_NAME']
            try:
                # 构建更新SQL
                update_sql = f"UPDATE `{table_name}` SET create_time = %s WHERE 1"

                # 执行更新
                cursor.execute(update_sql, (target_time_str,))
                affected_rows = cursor.rowcount

                print(f"表 {table_name} 更新成功，影响了 {affected_rows} 行")

            except Exception as e:
                print(f"更新表 {table_name} 时出错: {e}")
                connection.rollback()
                continue

        # 提交所有更改
        connection.commit()
        print("所有表更新完成")

except Exception as e:
    print(f"数据库操作出错: {e}")

finally:
    if connection:
        connection.close()