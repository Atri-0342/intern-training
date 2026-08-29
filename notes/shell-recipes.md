# Shell Recipes

## 1. Find Python Files Modified in the Last Two Days

  ```find . -type f -name "*.py" -mtime -2```

## Or Python files exclude .venv files

  ```find . -type f -name "*.py" \ 
  -not -path "./.venv/*" \
  -not -path "./.venv-windows/*" \
  -mtime -2```

## What it does

find . — search from the current directory
-type f — search files only
-name "*.py" — search only Python files
-not -path "./.venv/*" — exclude the Linux virtual environment
-not -path "./.venv-windows/*" — exclude the Windows virtual environment
-mtime -2 — find files modified within the last two days

## 2. Count Total Lines of Code

  ```find . -type f -name "*.py" -mtime -2 | xargs wc -l```

## Or 

  ```find . -type f -name "*.py" \
  -not -path "./.venv/*" \
  -not -path "./.venv-windows/*" \
  -mtime -2 \
  | xargs wc -l```

find — finds the Python files.
-mtime -2 — only files modified in the last 2 days.
xargs — passes the filenames to wc.
wc -l — counts the lines.

## 3. Find Every File Containing TODO

   ```grep -Rni "TODO" .```
   
grep — searches for text inside files.
-R — searches recursively through directories.
-n — displays the line number where the match occurs.
-i — ignores uppercase/lowercase differences.
"TODO" — the text we are searching for.
. — starts the search from the current directory.
