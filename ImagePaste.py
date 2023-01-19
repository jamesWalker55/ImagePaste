import os
import sublime
import sublime_plugin
import sys
import datetime
from pathlib import Path

# add ./lib to Python's import path
package_path = Path(__file__).absolute().resolve().parent
lib_path = package_path / "lib"
if str(lib_path) not in sys.path:
    sys.path.append(str(lib_path))

from PIL import ImageGrab


def get_settings():
    return sublime.load_settings("imagepaste.sublime-settings")


def get_fallback_command():
    """Return the command to execute if this command failed to paste an image"""

    settings = get_settings()
    raw_command = settings.get("fallback_command")
    raw_command_type = settings.get("fallback_command_type")

    if raw_command_type not in ("text", "window", "application"):
        return None, None

    # allow setting fallback_command to a string
    if isinstance(raw_command, str):
        return raw_command_type, {"command": raw_command, "args": {}}

    # otherwise, fallback_command should be a dict following Sublime Text's command format
    try:
        # verify the input format
        assert isinstance(raw_command["command"], str)
        assert isinstance(raw_command["args"], dict)

        return raw_command_type, raw_command
    except:
        return None, None


def run_fallback_command(view):
    cmd_type, command = get_fallback_command()
    if command is None:
        return

    # 'text', 'application', 'window'
    if cmd_type == "text":
        view.run_command(command["command"], command["args"])
    elif cmd_type == "window":
        view.window().run_command(command["command"], command["args"])
    else:  # cmd_type == 'application'
        sublime.run_command(command["command"], command["args"])


def get_variables(window):  # -> dict
    """Return variables used for variable expansion"""

    variables = window.extract_variables()

    all_folders = window.folders()
    if len(all_folders) > 0:
        variables["folder"] = all_folders[0]

    project_file_path = window.project_file_name()
    if project_file_path is not None:
        project_file_path = Path(project_file_path)
        variables["project"] = str(project_file_path)
        variables["project_path"] = str(project_file_path.parent)
        variables["project_name"] = project_file_path.name
        variables["project_base_name"] = project_file_path.stem
        variables["project_extension"] = project_file_path.suffix

    variables["date"] = datetime.date.today().isoformat()
    variables["datetime"] = (
        datetime.datetime.now().isoformat(sep="_", timespec="seconds").replace(":", "-")
    )

    return variables


def get_prefix(variables) -> str:
    """Return image prefix, if any"""

    raw_prefix = get_settings().get("image_prefix")
    if not isinstance(raw_prefix, str):
        return ""

    # remove variables that may cause issues when used in the prefix
    variables = variables.copy()
    variables.pop("file", None)
    variables.pop("file_path", None)
    variables.pop("folder", None)
    variables.pop("packages", None)

    return sublime.expand_variables(raw_prefix, variables)


def get_dir_name(variables) -> str:
    """Return the folder to store the image"""

    raw_dir_name = get_settings().get("image_dir_name")
    if not isinstance(raw_dir_name, str):
        # default to current directory
        return "."

    return sublime.expand_variables(raw_dir_name, variables)


def generate_image_path(view):
    variables = get_variables(view.window())
    prefix = get_prefix(variables)
    dir_name = get_dir_name(variables)

    current_file = Path(view.file_name() or variables["file"])

    dest_folder = current_file.parent / dir_name
    dest_folder = dest_folder.resolve()

    num = 1

    while True:
        dest_path = dest_folder / f"{prefix}{num}.png"
        if not dest_path.exists():
            break

        num += 1

    # generate the relative path to be pasted
    relative_to = get_settings().get("inserted_path_relative_to")
    if relative_to not in ("file", "first_open_folder"):
        relative_to = "file"  # fallback to file

    # use os.path.relpath instead of pathlib's relative_to
    # relative_to doesn't support starting from a different folder from the dest path
    if relative_to == "first_open_folder" and variables["folder"] is not None:
        dest_rel_path = os.path.relpath(dest_path, variables["folder"])
    elif relative_to == "file":
        dest_rel_path = os.path.relpath(dest_path, current_file.parent)
    else:
        sublime.error_message(
            f"Invalid configuration: {relative_to.__repr__()}\n"
            "'inserted_path_relative_to' must be either 'file' or 'first_open_folder'."
        )
        raise ValueError(f"Invalid value: {relative_to.__repr__()}")

    dest_rel_path = Path(dest_rel_path)

    return dest_path, dest_rel_path


def get_insert_formats():
    formats = get_settings().get("insert_format")
    if not isinstance(formats, list):
        return []

    formats = [
        f
        for f in formats
        if isinstance(f, dict)
        and isinstance(f.get("scope"), str)
        and isinstance(f.get("template"), str)
    ]

    return formats


class ImagePasteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # print(f"Image path: {generate_image_path(self.view)}")
        # print(f"Fallback command: {get_fallback_command()}")
        # print(f"Insert formats: {get_insert_formats()}")
        # print(f"Clipboard image: {ImageGrab.grabclipboard()}")
        # print("\n\n")

        # self.view is automatically provided by Sublime Text
        view = self.view

        # get list of positions preemptively, in case saving to disk takes a long time
        positions = [x.begin() for x in view.sel()]

        image = ImageGrab.grabclipboard()

        if isinstance(image, list):
            msg = "Please paste your image into an image editor then copy it from there!\nCan't paste this image - this is a PIL bug and can't be fixed with this plugin."
            sublime.error_message(msg)
            return

        if image is None:
            print("No valid image in clipboard.")
            run_fallback_command(view)
        else:
            abs_path, rel_path = generate_image_path(self.view)

            print(f"Saving image to: {abs_path}, {rel_path}")

            if not abs_path.parent.exists():
                rv = sublime.yes_no_cancel_dialog(
                    f"Folder doesn't exist: {rel_path.parent}\nCreate the folder and contnue?"
                )
                if rv != 1:  # rv != YES
                    return

                abs_path.parent.mkdir(parents=True)

            image.save(abs_path, "PNG")

            insert_formats = get_insert_formats()
            variables = {"path": str(rel_path)}

            for pos in positions:
                scope = view.scope_name(pos)

                for fmt in insert_formats:
                    if fmt["scope"] in scope:
                        content = sublime.expand_variables(fmt["template"], variables)
                        view.insert(edit, pos, content)
                        break
                else:
                    view.insert(edit, pos, rel_path)
