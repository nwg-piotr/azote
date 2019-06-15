# azote
Wallpaper manager for Sway, i3 and some other WMs

**Azote** is a GTK+ 3-based picture browser and a wallpaper setter, as the frontend to [swaybg](https://github.com/swaywm/swaybg) 
(Sway / Wayland) and [feh](https://feh.finalrewind.org) (X11) commands.

## Project assumptions

The most commonly used [Nitrogen](https://github.com/l3ib/nitrogen) does not work with [sway](https://swaywm.org). 
Together with the 1.1 Sway version, the standalone `swaybg` command became available, so it's easy to give it a GUI. 
In order not to limit the application of the project to the single environment, Azote is also capable of using feh, 
when running on i3, Openbox or other X11 window managers.

### Main features:

- works on Sway
- uses own, bigger thumbnails (240 x 135 px)
- flips wallpapers vertically
- splits wallpapers between 2 or more displays

## Usage

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

Edit your `~/.config/i3/config` file. Replace the line which start Nitrogen:

```bash
exec_always --no-startup-id nitrogen --restore
```

with:

```bash
exec_always --no-startup-id ~/.fehbg
```

**Openbox**

In your `autostart` replace:

```bash
nitrogen --restore &
```

with:

```bash
~/.fehbg
```