# CHANGELOG

## v1.7.10 (2020-03-15)

"Open with" issue [#82](https://github.com/nwg-piotr/azote/issues/82) fixed.

## v1.7.9 (2020-02-10)

- path to the config dir w/ XDG_CONFIG_HOME corrected.

## v1.7.8 (2019-12-25)

- styling clicked palette button with `button#color-btn-selected` added;
- colour picker: colour image converted into the Gtk.ColorButton class, to allow the colour edition;
- tracking the current wallpapers folder for file addition / deletion: switchable, configurable (every 5 sec by default);
- tray status icon added, to indicate the tracking on/off state. 

## v1.7.7 (2019-12-07)

- Image menu button: available in the top right thumbnail corner; turn on in preferences and use if the context
menu not always appears on right mouse click (this may happen on Sway running with older gtk+ versions).

## v1.7.5 (2019-11-22)

**Changes**

- Color picker on Sway: it'll will first try to pick a clicked point instead of an area with:

`grim -g "$(slurp -p)" -t ppm - | convert - -format '%[pixel:p{0,0}]' txt:-`

*Optional packages `grim`, `slurp` and `imagemagick` required; The colorthief-based calculation of the dominant color 
of an area left as the fallback method.*

- Color picker on X11: it'll will first try to pick an area and return a color with the maim command:

`$ maim -st 0 | convert - -resize 1x1\! -format '%[pixel:p{0,0}]' info:-`

*Optional `maim` and `imagemagick` packages required. In case it fails, the colorthief-based calculation of the dominant 
color of an area will be used as the fallback method.*

*Why so? The colorthief library is cool, but calculation of the dominant colour is not accurate enough to this 
purpose. If you select a region filled with `#333333`, the calculated value will be `#343434`.*

- Colour palette steps altered to 6, 12, 18, 24.

- Several improvements to the environment detection and logging.

**New**

- Toolboxes for `.Xresources` and `alacritty.yml`; allow to find colour definitions and redefine with colours
selected from a palette or probed with the color picker. The alacritty toolbox depends on the optional `python-yaml`
package.

*Usage: click a colour on the palette or pick with the Screen color picker -> click a colour inside the toolbox to apply.
Copy - paste definitions into the .dot file. Mind the indentation in `alacritty.yml`.*

- Colour names dictionary: displays the colour name as the tooltip text.

## v1.7.4 (2019-11-10)
- Layout adjusted to look well in light and dark GTK themes;
- set_always_show_image(True) for all image buttons, to avoid setting `gtk-button-images=1` in `gtk-3.0/settings.ini`;
- toolbox windows properties modified (will only affect tiling WMs);

## v1.7.3 (2019-11-07)
New:
- Screen color picker: grabs the dominant colour of a selected screen area.

Dependencies:
- `wmctrl` dependency removed;
- `grim`, `slurp` - optional dependency added: for screen color picker on Sway;
- `maim` - optional dependency added: for screen color picker on X11; (it'll also install `slop`, necessary as well).

Bug fixes:
- prevent program from crashing in case Sway not installed;
- prevent program from crashing in case wallpaper folder manually removed;
- fix for context menu not being shown if jpg or jpeg file association not detected;
- icon_flip.svg converted from font to shape;
- hardcoded 'Copy as' string replaced with the dictionary value.

## v1.7.2 (2019-11-04)
- Scale and crop an image to dual width or height of the primary display
- Data migrated to XGD-compliant locations
- Scale & crop feature not working on X11 bug, previously fixed in 1.5.1, has been reintroduced accidentally. 
Fixed one more time.

_Running Azote for the first time will move all the program data to XDG-compliant folders. From now 
on you'll find the `azoterc` file $XDG_CONFIG_HOME/azote/ (usually `~/.config/azote/azoterc`). Application data will be 
placed in $XDG_DATA_HOME/azote (`~/.local/share/azote/`). Thumbnails may regenerate. You may need to re-apply wallpaper 
settings._

## v1.7.0 (2019-11-01)
- **Scale & crop** backgrounds to virtual, custom display dimensions; define a custom display dimensions in preferences;
- **CLI arguments** added: `-h | --help`, `-c | --clear` (clear unused thumbnails), 
`-a | --clear-all` (clear all thumbnails);
- **thumbnails**: checkered background instead of black (clear thumbnails for this to take effect);
- **Create palette**: generates a colour palette on the basis of the selected image and displays a pop-up window;
click a colour button to copy `#rrggbb` or `(r, g, b)` to the clipboard; switch hex / decimal format in preferences;
This feature uses the awesome [colorthief library](https://github.com/fengsp/color-thief-py) (c) 2015 by Shipeng Feng;
- `~/.azote.azoterc` runtime configuration added - defines thumbnail width, number of thumbnail columns, dimensions 
of palette color images, color palette quality;
- image button removed, context menu always active;
- button icons redesigned.

Installing the 1.7.0 version will trigger regeneration of thumbnails on the first run.

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