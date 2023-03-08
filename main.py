import datetime
import os
import hashlib
import pathlib
import argparse


def log(message):
    with open(log_file_path, "a") as log_file:
        log_file.write(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S -> "))
        log_file.write(message)
        log_file.write("\n")

    print(datetime.datetime.now())
    print(message)
    print("\n")


def copy_entire_folder(source, destination):
    # recursively copies files found in the source folders into the destination folder. Creates new destination folders
    # if they don't exist
    for file in os.listdir(source):
        file_path = os.path.join(source, file)
        destination_path = os.path.join(destination, file)

        # if it's not a folder, then just copy it
        if not os.path.isdir(file_path):
            # used \" to ensure that spaces are allowed
            log("Copying " + file_path + " to " + destination)
            os.system("copy \"" + file_path + "\" \"" + destination + "\"")
            log("Copied " + file_path + " to " + destination)

            if are_files_identical(file_path, destination_path):
                # log("Files are identical.")
                continue
            else:
                log("The copied files are not identical. Copying wasn't successful.")
        # if it's a folder then proceed recursively
        else:
            log("Folder doesn't exist. Creating " + destination_path)
            os.mkdir(destination_path)

            if os.path.isdir(destination_folder):
                log("Destination folder created.")

                log("Starting to copy the entire source folder: " + file_path + " (since the destination didn't exist)")

                copy_entire_folder(file_path, destination_path)
            else:
                log("Couldn't create the destination folder. FAIL HERE")


def generate_files_data(folder, files_dict, folders_list, root_name):
    # keeps track of all the files and folders found in the specified folder and it's hierarchy (recursively)
    folders_list.append(folder.split(root_name)[1][1:])

    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)

        if not os.path.isdir(item_path):
            file_md5 = generate_file_md5(item_path)

            if file_md5 not in files_dict:
                files_dict[file_md5] = {"copies": 1}
                files_dict[file_md5]["data"] = {}
            else:
                files_dict[file_md5]["copies"] += 1

            copies = files_dict[file_md5]["copies"]
            files_dict[file_md5]["data"][copies - 1] = {}
            files_dict[file_md5]["data"][copies - 1]["name"] = item
            files_dict[file_md5]["data"][copies - 1]["folder_path"] = folder
            files_dict[file_md5]["data"][copies - 1]["verified"] = False

        else:
            generate_files_data(item_path, files_dict, folders_list, root_name)


def generate_file_md5(file_path):
    # calculates the unique md5 used to identify a file
    file = open(file_path, 'rb')
    data = file.read()
    md5_result = hashlib.md5(data).hexdigest()
    return md5_result


def are_files_identical(file_path_a, file_path_b):
    return generate_file_md5(file_path_a) == generate_file_md5(file_path_b)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Synchronize source and destination(replica) folders."
    )

    parser.add_argument("source_folder_path", help="Path to the source folder.", type=str)
    parser.add_argument("destination_folder_path", help="Path to the destination(replica) folder.", type=str)
    parser.add_argument("sync_interval", help="Time interval expressed in HOURS for synchronization.", type=int)
    parser.add_argument("log_file_path", help="Path to the log file where the info is written.", type=str)

    args = parser.parse_args()

    # to check the sync faster -> modify the "hours" to "seconds"
    # sync_interval = datetime.timedelta(hours=args.sync_interval)
    sync_interval = datetime.timedelta(seconds=args.sync_interval) # uncomment this to check it faster
    last_sync_time = datetime.datetime(2000, 3, 8, 20, 55, 38, 384292)

    source_folder = args.source_folder_path
    destination_folder = args.destination_folder_path

    # these names are used to check the hierarchy of folders (without the root) that should be identical
    source_folder_name = args.source_folder_path.split("\\")[-1]
    destination_folder_name = "destination".split("\\")[-1]

    log_file_path = args.log_file_path

    while True:
        if datetime.datetime.now() - last_sync_time > sync_interval:
            last_sync_time = datetime.datetime.now()
            if not os.path.isdir(destination_folder):
                log("Destination folder not found. Creating it...")

                os.mkdir(destination_folder)

                if os.path.isdir(destination_folder):
                    log("Destination folder created.")

                    log("Starting to copy the entire source folder (since the destination didn't exist)")

                    copy_entire_folder(source_folder, destination_folder)
                else:
                    log("Couldn't create the destination folder. FAIL HERE")

            else:
                log("Synchronisation process started.")

                # for these dictionaries the keys represent the files' md5s and the values will contain:
                # copy_number: how many times this file occurs in the whole source/destination folders
                # for each copy_number we'll have a name and a path
                source_files_dict = {}
                destination_files_dict = {}
                source_folders_list = []
                destination_folders_list = []

                generate_files_data(source_folder, source_files_dict, source_folders_list, source_folder_name)
                generate_files_data(destination_folder, destination_files_dict, destination_folders_list, destination_folder_name)

                log("Verification started.")
                # for now let's assume that the folder hierarchy didn't change
                for md5 in source_files_dict.keys():
                    # checking new files added in source
                    if md5 not in destination_files_dict.keys():
                        log("New file found. It's md5 = " + md5)

                        for new_item in range(source_files_dict[md5]["copies"]):
                            # added that [1:] at the end to avoid splitting with a lingering "\" that complicates the path join
                            new_file_destination_folder = os.path.join(destination_folder, (source_files_dict[md5]["data"]
                            [new_item]["folder_path"].split(source_folder_name))[1][1:])

                            new_file_source_path = os.path.join(source_files_dict[md5]["data"][new_item]["folder_path"],
                                                                source_files_dict[md5]["data"][new_item]["name"])

                            # if the folder already exists then just copy the new file
                            if os.path.isdir(new_file_destination_folder):
                                # used \" to ensure that spaces are allowed
                                log("Copying " + new_file_source_path + " in the destination folder: "
                                    + new_file_destination_folder)
                                os.system("copy \"" + new_file_source_path + "\" \"" + new_file_destination_folder + "\"")
                                log("Copied " + new_file_source_path + " in the destination folder: "
                                    + new_file_destination_folder)

                                new_file_destination_path = os.path.join(new_file_destination_folder,
                                                                         source_files_dict[md5]["data"][new_item]["name"])

                                if are_files_identical(new_file_source_path, new_file_destination_path):
                                    log("Files are identical.")

                                    source_files_dict[md5]["data"][new_item]["verified"] = True
                                else:
                                    log("The copied files are not identical. Copying wasn't successful.")
                            else:
                                # might have to create a new folder, or the folder was just renamed and needs to be identified
                                continue

                    else:
                        # validating the files that didn't move and weren't renamed
                        for source_item in range(source_files_dict[md5]["copies"]):
                            for destination_item in range(destination_files_dict[md5]["copies"]):
                                if not source_files_dict[md5]["data"][source_item]["verified"]:
                                    if source_files_dict[md5]["data"][source_item]["folder_path"].split(source_folder_name) \
                                            == destination_files_dict[md5]["data"][destination_item]["folder_path"]\
                                            .split(destination_folder_name):
                                        if source_files_dict[md5]["data"][source_item]["name"] == \
                                                destination_files_dict[md5]["data"][destination_item]["name"]:
                                            source_files_dict[md5]["data"][source_item]["verified"] = True
                                            destination_files_dict[md5]["data"][destination_item]["verified"] = True
                                        else:
                                            # rename the file in the destination folder or mark it as possibly moved
                                            continue
                                    else:
                                        # perhaps moved or deleted
                                        continue
                                else:
                                    continue

                        if source_files_dict[md5]["copies"] > destination_files_dict[md5]["copies"]:
                            # new copies were added so just copy them in the desired folders
                            continue

                # log("Checking unverified source files.")
                for md5 in source_files_dict.keys():
                    for source_item in range(source_files_dict[md5]["copies"]):
                        if not source_files_dict[md5]["data"][source_item]["verified"]:
                            # log(source_files_dict[md5]["data"][source_item]["name"] + " found at "
                                  # + source_files_dict[md5]["data"][source_item]["folder_path"] + " wasn't validated")

                            new_path = os.path.join(destination_folder, source_files_dict[md5]["data"][source_item]["folder_path"].split(source_folder_name)[1][1:])

                            if not os.path.isdir(new_path):
                                pathlib.Path(new_path).mkdir(parents=True, exist_ok=True)
                                # os.mkdir(new_path)
                                copy_entire_folder(source_files_dict[md5]["data"][source_item]["folder_path"], new_path)
                                log(new_path + " doesn't exist")
                            else:
                                source_file_path = os.path.join(source_files_dict[md5]["data"][source_item]["folder_path"], source_files_dict[md5]["data"][source_item]["name"])
                                log("Copying " + source_file_path + " to " + new_path)
                                os.system("copy \"" + source_file_path + "\" \"" + new_path + "\"")
                                log("Copied " + source_file_path + " to " + new_path)

                # log("Checking unverified destination files.")
                for md5 in destination_files_dict.keys():
                    for destination_item in range(destination_files_dict[md5]["copies"]):
                        if not destination_files_dict[md5]["data"][destination_item]["verified"]:
                            # log(destination_files_dict[md5]["data"][destination_item]["name"] + " found at " + destination_files_dict[md5]["data"][destination_item]["folder_path"] + " wasn't validated")
                            # perhaps it was deleted or renamed, but I'm going to ignore renaming for this task
                            file_path_to_delete = os.path.join(destination_files_dict[md5]["data"][destination_item]["folder_path"], destination_files_dict[md5]["data"][destination_item]["name"])
                            log(file_path_to_delete + " file has been removed from the source, but still exists in the destination file. Deleting it...")
                            os.system("del  \"" + file_path_to_delete + "\"")
                            log("Deleted " + file_path_to_delete)

                # Sorting the folder list by "path depth" in order to eliminate the remaining empty folders
                # this really is a stretch, but it works. with more time I could try a different approach cuz this
                # feels like a workaround
                for i in range(len(destination_folders_list)):
                    for j in range(i + 1, len(destination_folders_list)):
                        if len(destination_folders_list[i].split("\\")) < len(destination_folders_list[j].split("\\")):
                            tmp = destination_folders_list[i]
                            destination_folders_list[i] = destination_folders_list[j]
                            destination_folders_list[j] = tmp

                for folder in destination_folders_list:
                    if folder not in source_folders_list:
                        log(folder + " from the destination folder has not been found in the source folder. Removing it...")
                        os.system("rmdir \"" + os.path.join(destination_folder, folder) + "\"")
                        log(folder + " removed")

                log("All files and folders have been checked and synced.")





