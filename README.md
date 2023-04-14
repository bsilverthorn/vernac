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

### Install

- `pip install vernac` or (recommended →) `pipx install vernac`

### Run

- `export OPENAI_API_KEY=<key>`
- `vernac <source_in> -o <executable_out>`

The executable bundles its dependencies _except_ for a Python interpreter.

Missing features
----------------

- Modules
- Documentation
- API lookup
- Error messages
- Configuration
- Implicit self-tests
- Explicit self-tests
- IDE plugins
- Integration with other languages
- Shebang mode
- Non-OpenAI models
- Anything non-Linux or non-Python
- Anything to prevent your programs from behaving differently every time you recompile
- …

Related work
------------

- https://github.com/PrefectHQ/marvin

FAQs
----

### What about non-English languages?

They are likely to work, but less likely than English.

### This is a joke, right?

Is it? You tell me. :)
