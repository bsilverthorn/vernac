Vernac: programming (in) language 📖
====================================

Vernac is a tool for writing software in "vernacular"—plain language.

Vernac isn't for turning English into code; it's for turning English into _programs_:

```console
$ cat fizzbuzz.vn
print all the numbers between 1 and 100
print 'fizz' instead of the number if it’s divisible by 3
print 'buzz' if it’s divisible by 5
$ vernac fizzbuzz.vn -o fizzbuzz
$ ./fizzbuzz | head -n 5
1
2
fizz
4
buzz
```

Caution
-------

Be careful: Vernac is an **unstable** and somewhat whimsical **experiment**.

You shouldn't use it in production. You might, however, find it more useful than you expect.

Motivation
----------

To state the obvious: Vernac just does some LLM prompting and generates code under the hood.

Its value is in bundling together known prompts and annoying packaging steps so you can go from English to an executable program in one step.

The dream is that you check the _English_ into git, not the code.

Every modern programmer already uses ChatGPT to generate code, then copies the code into their own source file. That’s a bit like writing your application in assembly and occasionally pasting in output from your compiler. Stay in the highest-level language you have for as long as you can! Today, in the GPT era, our highest-level language is English.

Usage
-----

### Prerequisites

- Python 3.10+
- OpenAI API key with GPT-4

### Install

- `pip install vernac` or (recommended →) `pipx install vernac`

### Run

- `export OPENAI_API_KEY=<key>`
- `vernac <source_in> -o <executable_out>`

The executable bundles its dependencies _except_ for a Python interpreter.

Examples
--------

### Hitting an API: `emoji`

ChatGPT may remember _some_ stale information about an API, but often it's best to paste in relevant details:

````markdown
- fetch all emoji from https://emojihub.yurace.pro/api/all
- if a keyword is given as command line arg, pick the emoji with the most similar name
- otherwise pick a random emoji
- convert its unicode code point into a character and print that

# references

the emojihub API returns data like this:

```
{'name': 'minidisc', 'category': 'objects', 'group': 'objects', 'htmlCode': ['&#128189;'], 'unicode': ['U+1F4BD']}
```
````

### Writing tests: `fizzbuzz-with-tests`

Describe test cases and Vernac will run them during compilation:

```markdown
accept N as a command line arg
print all the numbers between 1 and N
print 'fizz' instead of the number if it’s divisible by 3
print 'buzz' if it’s divisible by 5

# tests

do the right thing with N=20
```

### Splitting code into modules: `todo`

Vernac can accept multiple input files. It will compile each one separately, guessing which are modules and which is the main program.

#### `todo-storage.vn`

```markdown
# storage module

todo list entries have

- number
- description
- status (done, not done)

todo list entries are stored in `~/.todo` as a json list of objects
```

#### `todo-tui.vn`

```markdown
# terminal-based todo list

todo list entries have

- number
- description
- status (done, not done)

## usage

- running the program shows a list of all todo list entries ordered by number
- one entry is selected at a time
- up/down arrow keys change the selection
- pressing d toggles the status of the selected entry
- pressing the del key removes the selected entry
- pressing c pops creates a new entry
- pressing s saves to the file
- pressing q saves and quits
- running with `--help` prints instructions and exits immediately

*Note: Ensure that any HTML strings are properly formatted, i.e., all tags are correctly opened and closed.*

## creating a new entry

- to create a new entry, present a dialog to the user
- it should have one text field to provide the description
- pressing esc should close the dialog without creating an entry
- new entries are selected automatically after they are created
```

Related work
------------

- https://github.com/PrefectHQ/marvin
- https://github.com/jina-ai/gptdeploy

FAQs
----

### What prevents my programs from behaving differently every time I recompile?

Nothing.

### What about non-English languages?

They are likely to work, but less likely than English.

### This is a joke, right?

Is it? You tell me. :)
