import cx_Oracle
import pandas as pd

# Replace with your actual Oracle DB credentials
dsn = cx_Oracle.makedsn('hostname', 'port', service_name='your_service')
user = 'your_username'
password = 'your_password'

# Establish the connection
connection = cx_Oracle.connect(user=user, password=password, dsn=dsn)
cursor = connection.cursor()

# Fetch all owners from the database
cursor.execute("""
    SELECT DISTINCT OWNER
    FROM ALL_TABLES
""")
owners = cursor.fetchall()

# Prepare list to store all results for export
all_data = []

# Loop over each owner
for owner in owners:
    owner_name = owner[0]
    
    # Fetch all tables for this owner
    cursor.execute("""
        SELECT TABLE_NAME
        FROM ALL_TABLES
        WHERE OWNER = :owner_name
    """, owner_name=owner_name)
    
    tables = cursor.fetchall()
    
    # Loop over each table for this owner
    for table in tables:
        table_name = table[0]
        
        # Fetch column names for the table
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM ALL_TAB_COLUMNS
            WHERE OWNER = :owner_name AND TABLE_NAME = :table_name
        """, owner_name=owner_name, table_name=table_name)
        
        columns = cursor.fetchall()
        column_headers = [col[0] for col in columns]
        
        # Fetch top 5 rows for the table
        cursor.execute(f"""
            SELECT * FROM {owner_name}.{table_name} FETCH FIRST 5 ROWS ONLY
        """)
        
        rows = cursor.fetchall()
        
        # Store the results in the list
        for row in rows:
            all_data.append([owner_name, table_name] + list(row))

# Close the cursor and connection
cursor.close()
connection.close()

# Create a DataFrame and save it to a CSV file
df = pd.DataFrame(all_data, columns=['Owner', 'Table'] + column_headers)
df.to_csv('database_output.csv', index=False)

print("Data has been written to database_output.csv")
