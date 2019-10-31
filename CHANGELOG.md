# CHANGELOG

## In development:
- Scale & crop backgrounds to virtual, custom display dimensions;
- CLI arguments added: `-h | --help`, `-c | --clear` (clear unused thumbnails), 
`-a | --clear-all` (clear all thumbnails);
- thumbnails: checkered background instead of black (clear thumbnails for this to take effect);
- 'Create palette':  feature added: to the context menu;
- `~/.azote.azoterc` added, defines thumbnail width, number of columns dimensions of palette color images, 
color palette quality;
- image button removed, context menu always active;
- button icons redesigned.

## v1.5.1 (2019-10-16)
- scale & crop feature not working on X11 bug 
[fixed](https://github.com/nwg-piotr/azote/commit/077806e6f72a84fdf768ac6c64d4f081a78fb579)
- small fixes to translations

## v1.5.0 (2019-10-12)
- Image menu: scale and crop the selected image to dimensions of a selected display

## v1.4.0 (2019-09-15)
- move to trash button feature moved to the image menu, button removed, context (right click) menu added
- image button now opens the image menu
- settings button added: turns image button and thumbnail context menu on/off (as right-click menu is not 100% reliable
  on Sway). Default settings determined on 1st run, depending on the sway environment detection.
- menus' gravity adjusted
- way of checking if we're running sway altered to avoid crash on qtile

## v1.3.1 (2019-08-21)
- double click on a thumbnail sets the wallpaper on all displays (mode = 'fill')
- main.py: some methods in classes replaced with static functions
- fix to the "Azote doesn't handle correctly file paths with spaces" issue #41

## v1.3.0 (2019-07-29)
- fr_FR translation by HumanG33k added
- fixed "silent" crash when running Azote w/o send2trash module
- initial window size altered
- thumbnail creation progress bar added
- fallback for missing /usr/share/applications/mimeinfo.cache added

## v1.2.0 (2019-07-07)
- issue #30 resolved: folder picker starts from the folder currently in use
- feature requested in issue #29 added: new button 'Apply to all displays'
- former 'open with feh' button now opens the menu to select from programs capable of opening the image

## v1.1.2 (2019-07-01)
- "Use python3 explicitly" PR #26 by @jubalh merged
- inconsistency in the version numbering resolved

## v1.1.1 (2019-06-30)
- launcher script for Void Linux added
- German description added to the .desktop file

## v1.1.0 (2019-06-28)
- new: German translation by xsme
- new: sorting order -> settings, sorting order button & menu
- bug fix: column width 256 -> 280 to avoid the last column that does not fit in the screen
- bug fix: clear wallpaper selection on folder changed
- bug fix: do not activate the Trash button if image path not inside the home path

## v1.0.0 (2019-06-25)
- missing check if button is not None added
- missing lang string added, lines sorted
- AUR - python-send2trash moved to optional dependencies

## v0.1.3 (pre-release, 2019.06.24)
- PR #18 by Head-on-a-Stick merged - fix to issue #17 (Wallpaper unselectable w/o python3-send2trash (Debian))

## v0.1.2 (pre-release, 2019.06.23)
- A try/except clause checks the python send2trash module availability.
  The python-send2trash dependency to be removed where unavailable.

## v0.1.1 (pre-release, 2019.06.22)
- "azote/main.py: corrected feh options" PR #8 by Head-on-a-Stick merged
- some no longer needed print commands removed
- hardcoded strings replaced with the dictionary
- all modules removed from install_requires=[] in setup.py

## v0.1.0 (pre-release, 2019.06.21)
- program icon slightly altered
- buttons and labels grouped in a single row
- new button: "Open selected with feh"
- new button: "Move selected to trash"
- new dependency: python-send2trash

## v0.0.3 (pre-release, 2019.06.18):
- "azote/tools.py: death to grep!" PR by Head-on-a-Stick merged
- folder selection button - vertical size fixed
- deprecated GTK+ code brought up to date
- clearing background color selection on image split button pressed
- other minor fixes to UI

## v0.0.2 (pre-release, 2019-06-17)
- shebangs changed to python3
- dependency on i3ipc-python dropped
- a bug manifesting on single-headed setup only (on changing the split_button sensitivity) fixed
- simple translations introduced

## v0.0.1 (pre-release, 2019-06-15)
Initial release