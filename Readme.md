# todo

A command line todo list written in Python.

## Installation

First clone to repo, then do the following 

### Setting up

Create a new environment variable `todoPath` with the following command:

#### Windows (powershell)
```powershell
$Env:todoPath = "<path-to-dir-of-todo>"
```

#### Most Linux and MacOS (bash/zsh/similar shell scripts)
```bash
export todoPath "<path-to-dir-of-todo>"
```

`<path-to-dir-of-todo>` is the path to the project directory.

### The `todo` Command

#### Windows (powershell)
Add this to your `$profile` 
```powershell
function todo {
    python <path-to-main.py> $args
}
```

#### Most Linux and MacOS (bash/zsh/similar shell scripts)

Add this to your `~/.bashrc` or `~/.zshrc` or `~/.<shell>rc` file, with `<shell>` being the name of your shell:
```bash
alias todo="python3 <path-to-main.py>"
```

With `<path-to-main.py>` being the path to the `main.py` file of `todo`.

## Usage

### Configuration

The configuration file path is stored in the environment variable `todo_configPath`, and here are the discription to each of the configuration vairbales
|Config Var|<center>Description</center>|
|--|--|
|`dataPath`|The Path to a json file where the data is stored, usually `.../data.json`|
|`archivePath`|The Path to a json file where data is archived, usually `.../archived.json`|
|`dateSeperator`|The separator for the format of the date|
|`autoClearCompletedPastTasks`|If `true`, will then allow the todo list to automatically clear completed tasks in previous days|
|`autoAddUncompletedTasks`|If `true`, will allow the todo list to automatically add any uncompleted task form previous days to today, adding a `-overdue-` tag alongside|
|`done`|Simply the symbol for marking a task done, defaults to `\u2713`, or `✓`|
|`important`|The symbol for marking a task important, which is put on higher priority, defaults to `!`|
|`outputLength`|The length of which the task names are trimmed at for calendar view, defaults to 19|
|`ntask`|The number of tasks to be displayed per day in the calendar view, defaults to 4|
|`tagColors`|See next section|

### Tags

Just specity it when adding a task, tags are separated by `", "`. There are 4 special tags, `-important-`, `-overdue-`, `-done-`, `-undone-`, see `todo --help` for more information.

#### tagColors

This is a list of colors for each special, default tags or custom tags. Specify the hex string of the color for a tag, an empty string means the color will mean no extra color effects is applied to it. For tags that do not have their color specified, this will be equivalent to having their color set to an empty string.

### Command Line Mode (CLI)

Everything is in `todo --help`, examples can be found with `todo --examples cli`.

#### Special notes

Ensure the terminal is resized large enough for the calendar view option, otherwise the output may not look good.

### Interactive Mode (interactive)

To be implemented `:)`

## Future

The following features will be planned for the future:
- Interactive Mode
- Warning for small terminals when using `--calendar`
