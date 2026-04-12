import mysql.connector

db_config = {
    'user': 'root',
    'password': 'root@1234',
    'host': '127.0.0.1',
    'database': 'cloud_cost_monitoring'
}

def check_structure():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    for table in ['companies', 'teams', 'cloud_services', 'cost_records']:
        print(f"\n--- {table} ---")
        cursor.execute(f"DESCRIBE {table}")
        for row in cursor.fetchall():
            print(row)
            
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_structure()
