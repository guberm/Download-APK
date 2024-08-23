import os
import subprocess

# Path to ADB executable
adb_path = "adb"

# Local directory to save downloaded files
download_directory = "downloaded_files"
os.makedirs(download_directory, exist_ok=True)

def run_adb_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"Command failed: {command}")
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"An error occurred while running the command: {command}")
        print(str(e))
        return None

def download_files_from_folder(remote_folder, local_folder):
    # Use 'find' command to list all files and directories in the remote folder
    remote_folder_escaped = f'"{remote_folder}"'
    files_list_output = run_adb_command(f'{adb_path} shell find {remote_folder_escaped} -type f')

    if files_list_output is None:
        print(f"Failed to list files in {remote_folder}")
        return

    files_list = files_list_output.splitlines()

    for remote_file_path in files_list:
        local_file_path = os.path.join(local_folder, os.path.relpath(remote_file_path, remote_folder))

        local_dir = os.path.dirname(local_file_path)
        os.makedirs(local_dir, exist_ok=True)

        # Download each file
        print(f'Downloading "{remote_file_path}"...')
        remote_file_path_escaped = f'"{remote_file_path}"'
        local_file_path_escaped = f'"{local_file_path}"'
        pull_result = run_adb_command(f'{adb_path} pull {remote_file_path_escaped} {local_file_path_escaped}')

        if pull_result and "pulled" in pull_result:
            print(f'Successfully downloaded "{os.path.basename(remote_file_path)}"')
        else:
            print(f'Failed to download "{os.path.basename(remote_file_path)}"')

def download_download_folder():
    # Remote "Download" folder on the Android device
    remote_download_folder = "/storage/emulated/0/Download"

    print(f"Starting to download files from {remote_download_folder}...")
    download_files_from_folder(remote_download_folder, download_directory)
    print("Download completed.")

download_download_folder()
