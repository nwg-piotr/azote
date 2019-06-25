# How to contribute?

**Azote** uses simple text files to store language strings. If you'd like to see the UI in your own language, first
check what python `locale` module returns for you: 

```text
$ python3
Python 3.7.3 (default, Mar 26 2019, 21:43:19) 
[GCC 8.2.1 20181127] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import locale
>>> locale.getlocale()
('pl_PL', 'UTF-8')
>>>
```

Use the first element of returned tuple as the file name (as `pl_PL` for Polish). Copy the `en_EN` file, edit translations
and save under the name you determined. Fork the repository, add your file and make a pull request.

To force use of a certain language (if available), use the `lang` argument:

```bash
azote lang pl_PL
```

-> starts Azote in Polish.