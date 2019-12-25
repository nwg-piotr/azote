# Azote

[![Build Status](https://travis-ci.com/nwg-piotr/azote.svg?branch=master)](https://travis-ci.com/nwg-piotr/azote)

**Azote** is a GTK+3 - based picture browser and background setter, as the frontend to the [swaybg](https://github.com/swaywm/swaybg) 
(sway/Wayland) and [feh](https://feh.finalrewind.org) (X windows) commands. It also includes several colour management 
tools.

The program is confirmed to work on sway, i3, Openbox, Fluxbox and dwm window managers, on Arch Linux, Void Linux and 
Debian.

![screenshot](http://nwg.pl/Lychee/uploads/big/78510b1f9358767e8407d66e933f1d8c.png)

*Wallpapers above come from https://wallhaven.cc*

## Project assumptions

The most commonly used *desktop background browser and setter* is aimed at X windows, and does not work with 
[sway](https://swaywm.org). Since the `swaybg` command does everything we may need, it's enough to give it a GUI. 
In order not to limit the program usage to the single environment, Azote is also capable of using feh 
when running on i3, Openbox or other X11 window managers.

*The description below takes into account the latest release. All the features may or may not be available in the
package already prepared for a certain Linux distribution. Some features rely on 
[optional dependencies](https://github.com/nwg-piotr/azote#dependencies-as-used-in-the-azote-aur-package).*

### Main features:

- works on Sway;
- uses own thumbnails, 240x135px by default;
- flips wallpapers horizontally;
- splits wallpapers between 2 or more displays;
- scales and crops images to detected or user-defined display dimensions;
- generates a colour palette on the basis of an image;
- picks a colour from the screen;
- allows to find and edit colour definitions in `.Xresources` and `alacritty.yml` files.

## Usage

Select the folder your wallpapers are stored in. If it contains a lot of big pictures, it may take some time for
Azote to create thumbnails. It's being performed once per folder, unless you clear the thumbnails folder.

Most of the buttons seem to be self-explanatory, with a little help from their tooltip text. What may not be clear
at first is the `Apply selected picture to all screens` button. It applies unchanged
selected picture to all displays, regardless of whether they are currently connected/detected. It may be useful if you
often connect and disconnect displays. A shortcut to this feature is just to double click a thumbnail. It'll always 
use the 'fill' mode, however.

Azote, as well as feh, saves a batch file to your home directory. It needs to be executed in order to set the wallpaper 
on subsequent logins or reboot.

### sway

Edit your `~/.config/sway/config` file. Replace your current wallpaper settings, like:

```bash
output * bg /usr/share/backgrounds/sway/Sway_Wallpaper_Blue_1920x1080.png fill
```

with:

```bash
exec ~/.azotebg
```

### X window managers (i3, Openbox, dwm etc.)

You need to execute `~/.fehbg` from your window manager’s startup file.

**dwm note:**

If you start dwm from a script, it may look something like this:

```bash
# Statusbar loop
while true; do
   xsetroot -name "$( date +"%F %R" )"
   sleep 1m    # Update time every minute
done &

# Autostart section
~/.fehbg & 

exec dwm
```

## Versioning

Azote uses [Semantic Versioning 2.0.0](https://semver.org). 
For changes see [CHANGELOG](https://github.com/nwg-piotr/azote/blob/master/CHANGELOG.md).

## Installation

[![Packaging status](https://repology.org/badge/vertical-allrepos/azote.svg)](https://repology.org/project/azote/versions)

## Arch Linux

Install [azote](https://aur.archlinux.org/packages/azote) from AUR. 
For the development version install [azote-git](https://aur.archlinux.org/packages/azote-git).

## Debian & Ubuntu

Either download the .deb package or follow the instructions in [this link](https://software.opensuse.org//download.html?project=home%3AHead_on_a_Stick%3Aazote&package=azote) to add the repository and APT key.

If the repository & key are added then the package will be updated with the usual `apt update && apt upgrade` commands.

## Void Linux

Binary package `azote` available in the Void repository. 

## Other Linux distributions:

Packagers wanted! Personally I only maintain Arch (AUR) and Void Linux packages. Please do remember to copy the 
LICENSE-COLORTHIEF file to `/usr/share/licenses/azote/`.

### Dependencies (as used in the `azote` AUR package):

- `python` (`python3`)
- `python-setuptools`
- `python-gobject`
- `python-pillow`
- `gtk3`
- `feh`
- `xorg-xrandr`
- `python-send2trash`

### Optional dependencies:

- `grim`, `slurp`: for screen color picker on Sway
- `maim`, `slop`: for screen color picker on X11
- `imagemagick`: for screen color picker on both Sway and X11
- `python-yaml`: (`python3-yaml`) for alacritty.yml toolbox

Please use assets from the [latest release](https://github.com/nwg-piotr/azote/releases/latest).

Seeing Arch [PKGBUILD](https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=azote) may be informative.

## ~/.config/azote/azoterc

```json
{
  "thumb_width": "240",
  "columns": "3",
  "color_icon_w": "100",
  "color_icon_h": "50",
  "clip_prev_size": "30",
  "palette_quality": "10",
  "tracking_interval_seconds": "5"
}
```

Azote is being developed on the 1920 x 1080 box, and some graphics dimensions may not go well with other screens.
The runtime configuration file allows to redefine them:

- `thumb_width` - thumbnail width; changing the value triggers thumbnails regeneration on startup;
- `columns` - initial number of columns in thumbnails preview;
- `color_icon_w`, `color_icon_h`, `clip_prev_size` - define dimensions of pictures which represent colors in the color 
palette view;
- `palette_quality` - affects quality and time of generation of the colour palette on the basis of an image; the less - the
better, but slower; default value is 10;
- `tracking_interval_seconds` - determines how often the current wallpapers folder should be checked for file addition / 
deletion.

## Command line arguments

```text
$ azote -h

Azote wallpaper manager version 1.x.y

[-h] | [--help]			 Print help
[-l] | [--lang] <ln_LN> 	 Force a locale (de_DE, en_EN, fr_FR, pl_PL)
[-c] | [--clear]		 Clear unused thumbnails
[-a] | [--clear-all]		 Clear all thumbnails
```

## Troubleshooting

### No pictures in thumbnails / display preview

As well thumbnails, as displays preview inherit from the Gtk.Button class. In case you don't see images inside them,
please make sure that button images are turned on in the `~/.config/gtk-3.0/settings.ini` file:

```bash
[Settings]
(...)
gtk-button-images=1
```

### 'Open with...' feature doesn't work

![screenshot](http://nwg.pl/Lychee/uploads/big/4372deec10eb787fbf8f840c2abf3b67.png)

**Azote v1.2.0 and below** - no 'Open with' menu entry at all;

**Azote v1.3.0 and above** - the only program listed is feh.

The `/usr/share/applications/mimeinfo.cache` is probably missing from your system. Regenerate it:

```bash
$ sudo update-desktop-database
```

See https://specifications.freedesktop.org/desktop-entry-spec/0.9.5/ar01s07.html

### X11 / feh notice

The background color picker won't be available. You'll also be unable to select different modes 
*("scale", "max", "fill", "center", "tile")* for certain displays. The list of modes varies from what you see in Sway 
*("stretch", "fit", "fill", "center", "tile")*.
