# Azote

**Azote** is a GTK+ 3-based picture browser and a wallpaper setter, as the frontend to [swaybg](https://github.com/swaywm/swaybg) 
(Sway / Wayland) and [feh](https://feh.finalrewind.org) (X windows) commands.

![screenshot](http://nwg.pl/Lychee/uploads/big/221525787069b71288ae49718f772b33.png)

*The pictures above come from https://wallhaven.cc*

## Project assumptions

The most commonly used *desktop background browser and setter* is aimed at X windows, and does not work with [sway](https://swaywm.org). 
Together with the 1.1 Sway version, the standalone `swaybg` command became available, so it's easy to give it a GUI. 
In order not to limit the program usage to the single environment, Azote is also capable of using feh, 
when running on i3, Openbox or other X11 window managers.

### Main features:

- works on Sway
- uses own, bigger thumbnails (240 x 135 px)
- flips wallpapers vertically
- splits wallpapers between 2 or more displays

## Usage

Select the folder your wallpapers are stored in. If it contains a lot of big pictures, it may take some time for
Azote to create thumbnails. It's being performed once, unless you clear the `~/.azote/thumbnails` folder.

Azote, as well as feh, saves a batch file to your home directory.

**sway**

Edit your `~/.config/sway/config` file. Replace your current wallpaper settings, like:

```bash
output * bg /usr/share/backgrounds/sway/Sway_Wallpaper_Blue_1920x1080.png fill
```

with:

```bash
exec ~/.azotebg
```

**i3**

In your `~/.config/i3/config` file add:

```bash
exec_always --no-startup-id ~/.fehbg
```

**Openbox**

In your `autostart` add:

```bash
~/.fehbg &
```

The program has not yet been tested with other WMs.

### X11 / feh notice

Due to feh limitations, the background color picker won't be available. You'll also be unable to select different modes 
("tile", "center", "scale", "seamless") for certain displays. The list of modes varies from what you see in Sway 
("stretch", "fit", "fill", "center", "tile").

## Code status

Alpha. The first public release coming soon.