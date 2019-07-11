# Azote

**Azote** is a GTK+ 3-based picture browser and a wallpaper setter, as the frontend to the [swaybg](https://github.com/swaywm/swaybg) 
(Sway/Wayland) and [feh](https://feh.finalrewind.org) (X windows) commands.

![screenshot](http://nwg.pl/Lychee/uploads/big/2ef98871aea09679282675e942f153ed.png)

*Pictures above come from https://wallhaven.cc*

Also see [Azote in action on YouTube](https://youtu.be/Cjqr0LRL67I).

## Project assumptions

The most commonly used *desktop background browser and setter* is aimed at X windows, and does not work with 
[sway](https://swaywm.org). Since the `swaybg` command does everything we may need, it's enough to give it a GUI. 
In order not to limit the program usage to the single environment, Azote is also capable of using feh 
when running on i3, Openbox or other X11 window managers.

### Main features:

- works on Sway
- uses own, bigger thumbnails (240x135px)
- flips wallpapers horizontally
- splits wallpapers between 2 or more displays

## Usage

Select the folder your wallpapers are stored in. If it contains a lot of big pictures, it may take some time for
Azote to create thumbnails. It's being performed once per folder, unless you clear the `~/.azote/thumbnails` folder.

Most of the buttons seem to be self-explanatory, with a little help from their tooltip text. What may not be clear
at first is the `Apply selected picture to all screens` button. Introduced on request (issue #29), it applies unchanged
selected picture to all displays, regardless of whether they are currently connected/detected. It may be useful if you
often connect and disconnect displays.

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

## Installation

### Arch Linux

Install [azote](https://aur.archlinux.org/packages/azote) from AUR.

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

**NOTE:** due to a mistake in the template, you may need to install the `python3-setuptool` package manually to prevent
Azote from crashing on start. This will be fixed in the next package revision.

## Troubleshooting

As well pictures as displays preview inherit from the Gtk.Button class. In case you don't see images inside them,
please make sure that button images are turned on in the `~/.config/gtk-3.0/settings.ini` file:

```bash
[Settings]
(...)
gtk-button-images=1
```

## Other Linux distributions:

[![Packaging status](https://repology.org/badge/vertical-allrepos/azote.svg)](https://repology.org/project/azote/versions)

Packagers wanted!

**Dependencies:**

- python
- python-setuptools
- python-gobject
- python-pillow 
- gtk3
- feh 
- xorg-xrandr
- wmctrl

**Optional:** 

- python-send2trash: trash support

Please use assets from the [latest release](https://github.com/nwg-piotr/azote/releases/latest).

Seeing Arch [PKGBUILD](https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=azote) may be informative.

### X11 / feh notice

The background color picker won't be available. You'll also be unable to select different modes 
*("scale", "max", "fill", "center", "tile")* for certain displays. The list of modes varies from what you see in Sway 
*("stretch", "fit", "fill", "center", "tile")*.
