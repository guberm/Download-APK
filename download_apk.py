import os
import re
import sqlite3
import subprocess
from androguard.core.apk import APK  # Correct import for APK handling

# Path to ADB executable
adb_path = "adb"

# Directories to save APKs
user_apk_directory = "user_apks"
system_apk_directory = "system_apks"
os.makedirs(user_apk_directory, exist_ok=True)
os.makedirs(system_apk_directory, exist_ok=True)

# SQLite database for tracking downloaded APKs
db_file = "downloaded_apks.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS apks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name TEXT NOT NULL,
    app_name TEXT NOT NULL,
    version_name TEXT NOT NULL,
    is_system_app INTEGER NOT NULL,
    apk_path TEXT NOT NULL,
    UNIQUE(package_name, version_name)
)
''')
conn.commit()

def run_adb_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    return result.stdout.strip()

def get_app_name_from_apk(apk_path):
    # Use APK class from androguard to parse the APK and extract the application name
    apk = APK(apk_path)
    app_name = apk.get_app_name()
    return app_name

def sanitize_filename(name):
    # Replace invalid characters for filenames in Windows
    return re.sub(r'[\\/:*?"<>|]', '', name)

def is_apk_downloaded(package_name, version_name):
    cursor.execute('''
    SELECT id FROM apks WHERE package_name = ? AND version_name = ?
    ''', (package_name, version_name))
    return cursor.fetchone() is not None

def add_apk_to_db(package_name, app_name, version_name, is_system_app, apk_path):
    cursor.execute('''
    INSERT OR IGNORE INTO apks (package_name, app_name, version_name, is_system_app, apk_path)
    VALUES (?, ?, ?, ?, ?)
    ''', (package_name, app_name, version_name, is_system_app, apk_path))
    conn.commit()

def process_package(package, is_system_app=False):
    # Get the APK path from the device
    apk_paths_output = run_adb_command(f"{adb_path} shell pm path {package}")
    apk_path_match = re.search(r'package:(.+)', apk_paths_output)
    if not apk_path_match:
        print(f"Failed to get APK path for {package}")
        return
    apk_path = apk_path_match.group(1)

    # Get the version name
    version_name_output = run_adb_command(f"{adb_path} shell dumpsys package {package} | grep versionName")
    version_name_match = re.search(r'versionName=(.+)', version_name_output)
    version_name = sanitize_filename(version_name_match.group(1)) if version_name_match else "unknown"

    if is_apk_downloaded(package, version_name):
        print(f"APK for {package} version {version_name} already downloaded. Skipping.")
        return

    # Determine the appropriate directory
    apk_directory = system_apk_directory if is_system_app else user_apk_directory
    local_apk_path = os.path.join(apk_directory, f"{package}.apk")

    # Pull the APK to the local machine
    pull_result = run_adb_command(f"{adb_path} pull {apk_path} {local_apk_path}")

    if "pulled" not in pull_result:
        print(f"Failed to download APK for {package}")
        return

    # Extract the application name from the APK
    app_name = get_app_name_from_apk(local_apk_path)
    if app_name:
        app_name = sanitize_filename(app_name)
    else:
        app_name = package

    # Construct the filename as app_name + version_name + .apk
    output_file_name = f"{app_name}-{version_name}.apk"
    destination_path = os.path.join(apk_directory, output_file_name)

    # Rename the APK file to the correct app name and version
    os.rename(local_apk_path, destination_path)
    print(f"Successfully renamed {local_apk_path} to {destination_path}")

    # Store the APK info in the database
    add_apk_to_db(package, app_name, version_name, is_system_app, destination_path)

def process_apps():
    # Get the list of user apps
    user_packages_output = run_adb_command(f"{adb_path} shell pm list packages -3")
    user_packages = [line.replace('package:', '') for line in user_packages_output.splitlines()]

    # Get the list of system apps
    system_packages_output = run_adb_command(f"{adb_path} shell pm list packages -s")
    system_packages = [line.replace('package:', '') for line in system_packages_output.splitlines()]

    # Process user apps
    for package in user_packages:
        print(f"Processing user app: {package}")
        process_package(package, is_system_app=False)

    # Process system apps
    for package in system_packages:
        print(f"Processing system app: {package}")
        process_package(package, is_system_app=True)

print("Starting APK processing...")
process_apps()
print("APK processing completed.")

# Close the database connection
conn.close()
