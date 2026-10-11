# calibre-string-remover

A [calibre](https://calibre-ebook.com) plugin that removes strings you specify from the text of your books, e.g. the link to a website that some source has stamped onto the end of every chapter.

It cleans books automatically when they are added to calibre, and it can go through the whole existing library in one run.

## What it does

- **Links:** a link that points to one of your strings, or shows it as its text, is removed completely, together with the paragraph or box that only existed to hold it.
- **Plain text:** other occurrences of the strings in the book text are deleted.
- **On import:** books are cleaned before they are added to the library. The file you import from is not changed.
- **Whole library:** one button scans all books, lists how many removals each book would get, and only rewrites the files after you confirm.
- **Backup:** when cleaning the library, the unchanged file can be kept next to the cleaned one as `ORIGINAL_EPUB` / `ORIGINAL_AZW3`.
- **Matching:** case-insensitive by default, optionally case-sensitive or with regular expressions.

Supported formats are **EPUB** and **AZW3**, the two formats calibre can edit. Other formats (KFX, MOBI, PDF, …) are left alone, and so are books with DRM.

## Install

1. Download `StringRemover.zip` from the [latest release](https://github.com/DerSchmachtin/calibre-string-remover/releases/latest).
2. In calibre, open **Preferences → Plugins → Load plugin from file** and choose the ZIP.
3. Restart calibre.

Or from the command line, with calibre closed:

```bash
calibre-customize -a StringRemover.zip
```

To build the ZIP yourself from a clone of this repository:

```bash
zip StringRemover.zip __init__.py cleaner.py config.py plugin-import-name-string_remover.txt
```

Requires calibre 5 or newer.

## Setup

Open **Preferences → Plugins → File type → String Remover → Customize plugin**.

- **Strings to remove:** one per line. For a watermark link, the address of the website is enough, e.g. `example.com`. That matches both the link target `https://example.com` and a link text such as `Example.com`.
- **Case sensitive:** off by default, so `example.com` also matches `Example.COM`.
- **Treat lines as regular expressions:** each line is then a Python regular expression instead of plain text.
- **Clean books automatically when they are added:** switches the cleaning on import on and off.
- **Keep the unchanged file as ORIGINAL_…:** applies to **Clean whole library now…**. If a book already has an `ORIGINAL_EPUB` / `ORIGINAL_AZW3`, that one is kept and not overwritten.

Click **OK** to save the settings.

## Cleaning the existing library

1. Enter your strings as above.
2. Click **Clean whole library now…**. The plugin scans every EPUB and AZW3 of the current library. Nothing is changed yet.
3. A dialog says how many book files would be rewritten. **Show details** lists them with the number of removals per book, and any book that had to be skipped.
4. Confirm to write the cleaned files into the library.

Once you are happy with the result, the `ORIGINAL_…` copies can be deleted like any other format.

## Notes

- Choose strings that are specific. Every occurrence in the book text is removed, so a common word would be removed everywhere.
- Only the text of the book is searched, not its metadata (title, authors, …).
- An AZW3 file is rebuilt by calibre when it is cleaned, which takes a little longer than an EPUB.

## License

[GPL-3.0](LICENSE), the same license as calibre.
