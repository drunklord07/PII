import cx_Oracle
import pandas as pd

# Replace with your actual Oracle DB credentials
dsn = cx_Oracle.makedsn('hostname', 'port', service_name='your_service')  # Adjust connection details
user = 'your_username'
password = 'your_password'

# Establish the connection
connection = cx_Oracle.connect(user=user, password=password, dsn=dsn)
cursor = connection.cursor()

# Prepare a list to hold all results
all_data = []

# Step 1: Get distinct owners (schemas)
cursor.execute("SELECT DISTINCT OWNER FROM ALL_TABLES")
owners = cursor.fetchall()

# Step 2: Loop through each schema (owner)
for owner in owners:
    owner_name = owner[0]
    
    # Get all table names in the current schema
    cursor.execute(f"SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = '{owner_name}'")
    tables = cursor.fetchall()

    # Step 3: Loop through each table in the current schema
    for table in tables:
        table_name = table[0]
        
        # Step 4: Get the first 5 rows of the table
        try:
            cursor.execute(f"SELECT * FROM {owner_name}.{table_name} FETCH FIRST 5 ROWS ONLY")
            rows = cursor.fetchall()
            
            # Get column names from the table
            columns = [desc[0] for desc in cursor.description]

            # Step 5: Append the results with owner, table, and row data
            for row in rows:
                all_data.append([owner_name, table_name] + list(row))

        except Exception as e:
            print(f"Error fetching data from {owner_name}.{table_name}: {e}")

# Step 6: Create a pandas DataFrame from the results
df = pd.DataFrame(all_data, columns=['Owner', 'Table'] + columns)

# Step 7: Export to Excel
df.to_excel('database_output.xlsx', index=False)

# Close the cursor and connection
cursor.close()
connection.close()

print("Data has been written to 'database_output.xlsx'")
