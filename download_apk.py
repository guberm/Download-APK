import os
import re
import subprocess
from androguard.core.apk import APK  # Correct import for APK handling

# Path to ADB executable
adb_path = "adb"

# Directories to save APKs
user_apk_directory = "user_apks"
system_apk_directory = "system_apks"
os.makedirs(user_apk_directory, exist_ok=True)
os.makedirs(system_apk_directory, exist_ok=True)

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

def process_package(package, is_system_app=False):
    # Determine the appropriate directory
    apk_directory = system_apk_directory if is_system_app else user_apk_directory

    # Get the APK path from the device
    apk_paths_output = run_adb_command(f"{adb_path} shell pm path {package}")
    apk_path_match = re.search(r'package:(.+)', apk_paths_output)
    if not apk_path_match:
        print(f"Failed to get APK path for {package}")
        return
    apk_path = apk_path_match.group(1)

    # Pull the APK to the local machine
    local_apk_path = os.path.join(apk_directory, f"{package}.apk")
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

    # Get the version name
    version_name_output = run_adb_command(f"{adb_path} shell dumpsys package {package} | grep versionName")
    version_name_match = re.search(r'versionName=(.+)', version_name_output)
    version_name = sanitize_filename(version_name_match.group(1)) if version_name_match else "unknown"

    # Construct the filename as app_name + version_name + .apk
    output_file_name = f"{app_name}-{version_name}.apk"
    destination_path = os.path.join(apk_directory, output_file_name)

    # Rename the APK file to the correct app name and version
    os.rename(local_apk_path, destination_path)
    print(f"Successfully renamed {local_apk_path} to {destination_path}")

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
