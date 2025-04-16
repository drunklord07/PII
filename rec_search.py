import paramiko

# SSH login credentials
hostname = 'your.server.com'
port = 22
username = 'your_username'
password = 'your_password'

# Output file
output_file = 'rnm_backup_files.txt'

def ssh_execute():
    try:
        # Connect to SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)

        # Step 1: Find the rnm_backup directory path
        stdin, stdout, stderr = client.exec_command('find / -type d -name "rnm_backup" 2>/dev/null')
        paths = stdout.read().decode().splitlines()

        if not paths:
            print("No 'rnm_backup' directory found.")
            client.close()
            return

        backup_path = paths[0]  # Taking the first match

        # Step 2: List all files inside rnm_backup recursively, one per line
        list_command = f'find {backup_path} -type f 2>/dev/null'
        stdin, stdout, stderr = client.exec_command(list_command)
        all_files = stdout.read().decode().strip()

        # Step 3: Save to local file (one path per line)
        with open(output_file, 'w') as f:
            f.write(all_files + '\n')  # just to ensure it ends cleanly

        print(f"All file paths saved to '{output_file}' (one per line)")

        client.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    ssh_execute()
