# ImagePaste

**Only Windows is supported for now.** If you would like to use this on Linux/OSX, please see [Other Systems].

Paste an image from the clipboard into Sublime Text.

Upon pasting, the image is saved to a file and a relative path to the image is inserted into the current file.

## Installation

Clone this repository, and move the folder to `Sublime Text\Packages\`.

## Usage

Get an image into the clipboard, then paste it into Sublime Text. Default keybinding is `Ctrl+V`

## Settings

```jsonc
{
    // Certain settings support Sublime Text's variable expansion. Some
    // additional variables are also provided: $date, $datetime

    // Image Output Settings
    //
    // These settings control where the image file will be created.

    // the output folder for the pasted image
    "image_dir_name": "images",

    // the prefix to be added to the pasted image
    "image_prefix": "$file_base_name",

    // Fallback Command Settings
    //
    // If no image is in the clipboard, a fallback command will be called
    // instead. These settings let you customise the fallback command to
    // be called.

    // The type of command to be executed.
    // Must be one of: text, window, application
    "fallback_command_type": "text",

    // The fallback command to execute.
    //
    // You can also provide a map that follows Sublime Text's command syntax:
    //
    //     "fallback_command": {
    //         "command": "paste",
    //         "args": {},
    //     },
    //
    "fallback_command": "paste",

    // Link Insertion Settings
    //
    // These settings control how the image path is inserted into the document

    // Change whether the output path is relative to the currently open file,
    // or the first open folder in the sidebar.
    //
    // Must be one of: file, first_open_folder
    "inserted_path_relative_to": "file",

    // The templates used when pasting the link into the document.
    // The only supported variable is $path
    "insert_format": [
        {
            "scope": "text.html.markdown",
            "template": "![]($path)",
        },
    ]
}
```

## Other Systems

This plugin relies on the Pillow library for image processing. I've included the windows build of that library in this plugin, but I have no idea how to make this plugin download the correct version of Pillow on other systems. If anyone knows how to do this, contributions are welcome.

[Download the correct version of Pillow from pypi](https://pypi.org/project/Pillow/#files). You must download the version built for Python 3.8 - `cp38`.

Then, open it with an archive manager and extract the `PIL` folder to this plugin's `lib` folder, replacing the existing `PIL` library.
