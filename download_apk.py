import os
import re
import subprocess
from androguard.core.apk import APK  # Correct import for APK handling

# Path to ADB executable
adb_path = "adb"

# Directory to save APKs
apk_directory = "apks"
os.makedirs(apk_directory, exist_ok=True)

def run_adb_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    return result.stdout.strip()

def get_app_name_from_apk(apk_path):
    # Use APK class from androguard to parse the APK and extract the application name
    apk = APK(apk_path)
    app_name = apk.get_app_name()
    return app_name

def process_package(package):
    # Get the APK path from the device
    apk_paths_output = run_adb_command(f"{adb_path} shell pm path {package}")
    apk_path = re.search(r'package:(.+)', apk_paths_output).group(1)

    # Pull the APK to the local machine
    local_apk_path = os.path.join(apk_directory, f"{package}.apk")
    run_adb_command(f"{adb_path} pull {apk_path} {local_apk_path}")

    # Extract the application name from the APK
    app_name = get_app_name_from_apk(local_apk_path)
    if app_name:
        # Sanitize app_name (remove illegal characters)
        app_name = re.sub(r'[\\/:*?"<>|]', '', app_name)
    else:
        app_name = package

    # Get the version name
    version_name_output = run_adb_command(f"{adb_path} shell dumpsys package {package} | grep versionName")
    version_name_match = re.search(r'versionName=(.+)', version_name_output)
    version_name = version_name_match.group(1) if version_name_match else "unknown"

    # Construct the filename as app_name + version_name + .apk
    output_file_name = f"{app_name}-{version_name}.apk"
    destination_path = os.path.join(apk_directory, output_file_name)

    # Rename the APK file to the correct app name and version
    os.rename(local_apk_path, destination_path)
    print(f"Successfully renamed {local_apk_path} to {destination_path}")

# Get the list of installed user apps
packages_output = run_adb_command(f"{adb_path} shell pm list packages -3")
packages = [line.replace('package:', '') for line in packages_output.splitlines()]

for package in packages:
    print(f"Processing package: {package}")
    process_package(package)

print("APK processing completed.")
