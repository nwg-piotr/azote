# Azote

[![Build Status](https://travis-ci.com/nwg-piotr/azote.svg?branch=master)](https://travis-ci.com/nwg-piotr/azote)

**1.7.2 version note**: _running Azote for the first time will move all the program data to XDG-compliant folders. From now 
on you'll find the `azoterc` file $XDG_CONFIG_HOME/azote/ (usually `~/.config/azote/azoterc`). Application data will be 
placed in $XDG_DATA_HOME/azote (`~/.local/share/azote/`). 
Thumbnails may regenerate. You may need to re-apply wallpaper settings._

**Azote** is a GTK+ 3 - based picture browser and a wallpaper setter, as the frontend to the [swaybg](https://github.com/swaywm/swaybg) 
(Sway/Wayland) and [feh](https://feh.finalrewind.org) (X windows) commands. During development I test it on sway, i3, 
Openbox, qtile and dwm, so I'm not sure if it works on others window managers.

![screenshot](http://nwg.pl/Lychee/uploads/big/a66c84b60a605b78e5fc4dd5ffbf8dbf.png)

*Pictures above come from https://wallhaven.cc*

Also see [Azote in action on YouTube](https://youtu.be/Cjqr0LRL67I).

## Project assumptions

The most commonly used *desktop background browser and setter* is aimed at X windows, and does not work with 
[sway](https://swaywm.org). Since the `swaybg` command does everything we may need, it's enough to give it a GUI. 
In order not to limit the program usage to the single environment, Azote is also capable of using feh 
when running on i3, Openbox or other X11 window managers.

*The description below takes into account the latest release. All the features may or may not be available in the
package already prepared for a certain Linux distribution.*

### Main features:

- works on Sway;
- uses own thumbnails, 240x135px by default;
- flips wallpapers horizontally;
- splits wallpapers between 2 or more displays;
- scales and crops images to detected or user-defined display dimensions;
- generates a colour palette on the basis of an image.

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

### Arch Linux

Install [azote](https://aur.archlinux.org/packages/azote) from AUR. 
For the development version install [azote-git](https://aur.archlinux.org/packages/azote-git).

### Debian & Ubuntu

Either download the .deb package or follow the instructions in [this link](https://software.opensuse.org//download.html?project=home%3AHead_on_a_Stick%3Aazote&package=azote) to add the repository and APT key.

If the repository & key are added then the package will be updated with the usual `apt update && apt upgrade` commands.

### openSUSE
azote is available in jubalhs home [repository](https://build.opensuse.org/package/show/home:jubalh/azote) on OBS.

```
zypper ar obs://home:jubalh
zypper ref
zypper in azote
```

### Void Linux

Binary package `azote` available in the Void repository. 

### Other Linux distributions:

Packagers wanted! Personally I only maintain Arch (AUR) and Void Linux packages. Please do remember to copy the 
LICENSE-COLORTHIEF file to `/usr/share/licenses/azote/`.

**Dependencies:**

- python (python3)
- python-setuptools
- python-gobject
- python-pillow
- gtk3
- feh
- xorg-xrandr

**Optional dependencies:** 

- python-send2trash: for trash support
- grim: for screen color picker on Sway
- slurp: for screen color picker on Sway
- maim: for screen color picker on X11
- imagemagick: for screen color picker on both Sway and X11
- python-yaml: (python3-yaml) for alacritty.yml toolbox

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
  "palette_quality": "10"
}
```

Azote is being developed on the 1920 x 1080 box, and some graphics dimensions may not go well with other screens.
The runtime configuration file allows to redefine them:

- `thumb_width` - thumbnail width; changing the value triggers thumbnails regeneration on startup;
- `columns` - initial number of columns in thumbnails preview;
- `color_icon_w`, `color_icon_h`, `clip_prev_size` - define dimensions of pictures which represent colors in the color 
palette view;

This may be useful to adjust settings to your machine performance:

- `palette_quality` affects quality and time of generation of the colour palette on the basis of an image; the less - the
better, but slower; default value is 10.

## Command line arguments

- `-h | --help` - displays help;
- `-l | --lang <ln_LN>` - forces a locale if available (de_DE, en_EN, fr_FR, pl_PL at the moment);
- `[-c] | [--clear]` - clears unused thumbnails;
- `[-a] | [--clear-all]` - clears all thumbnails.

## Troubleshooting

### No pictures in thumbnails / display preview

As well thumbnails, as displays preview inherit from the Gtk.Button class. In case you don't see images inside them,
please make sure that button images are turned on in the `~/.config/gtk-3.0/settings.ini` file:

```bash
[Settings]
(...)
gtk-button-images=1
```

### Open selected picture button doesn't work

![Open image menu](http://nwg.pl/Lychee/uploads/big/156b73ac880bca02ed04bd1886404ba8.png)

**Azote v1.2.0 and below** - the button does not work at all.

**Azote v1.3.0 and above** - the button opens selected picture with feh, does not allow to choose a program.

The `/usr/share/applications/mimeinfo.cache` is probably missing from your system. Regenerate it:

```bash
$ sudo update-desktop-database
```

See https://specifications.freedesktop.org/desktop-entry-spec/0.9.5/ar01s07.html

### X11 / feh notice

The background color picker won't be available. You'll also be unable to select different modes 
*("scale", "max", "fill", "center", "tile")* for certain displays. The list of modes varies from what you see in Sway 
*("stretch", "fit", "fill", "center", "tile")*.
