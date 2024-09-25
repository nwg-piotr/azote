#!/usr/bin/env bash

rm -f /usr/bin/azote

install -Dm 644 -t /usr/share/pixmaps dist/azote.svg
install -Dm 644 -t /usr/share/azote dist/indicator*.png
install -Dm 644 -t /usr/share/applications dist/azote.desktop
install -Dm 644 -t /usr/share/doc/azote README.md

python -m build --wheel --no-isolation
python -m installer dist/*.whl
