#!/usr/bin/env bash

PROGRAM_NAME="azote"
MODULE_NAME="azote"
SITE_PACKAGES="$(python3 -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")"
PATTERN="$SITE_PACKAGES/$MODULE_NAME*"

# Remove from site_packages
for path in $PATTERN; do
    if [ -e "$path" ]; then
        echo "Removing $path"
        rm -r "$path"
    fi
done

[ -d "./dist" ] && rm -rf ./dist

rm -f /usr/bin/azote

install -Dm 644 -t /usr/share/pixmaps "dist/$PROGRAM_NAME.svg"
install -Dm 644 -t "/usr/share/$PROGRAM_NAME" dist/indicator*.png
install -Dm 644 -t /usr/share/applications "dist/$PROGRAM_NAME.desktop"
install -Dm 644 -t "/usr/share/doc/$PROGRAM_NAME" README.md

python -m build --wheel --no-isolation
python -m installer dist/*.whl
