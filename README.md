<img src="https://github.com/nwg-piotr/azote/assets/20579136/6ee4b9aa-e73d-4c9f-9665-a86bd76c045b" width="90" style="margin-right:10px" align=left alt="nwg-shell logo">
<H1>Azote</H1><br>

This application is a part of the [nwg-shell](https://nwg-piotr.github.io/nwg-shell) project.

**Azote** is a GTK+3 - based picture browser and background setter, as the frontend to the [swaybg](https://github.com/swaywm/swaybg) 
(sway/Wayland) and [feh](https://feh.finalrewind.org) (X windows) commands. The user interface is being developed with
multi-headed setups in mind. Azote also includes several colour management tools.

[![Packaging status](https://repology.org/badge/vertical-allrepos/azote.svg)](https://repology.org/project/azote/versions)

The program, written primarily for sway, should work on all wlroots-based Wayland compositors, as well as on
some X11 window managers. GNOME is not supported.

Azote relies on numerous external packages. Some of them determine if the program is capable of working in a certain
environment (sway / another wlroots-based compositor / X11). It's **up to the packager** which of them come preinstalled.
It's recommendable to first run `azote` from terminal:

- if one of missing packages disallows Azote to work at all (e.g. `python-xlib` or `feh` on X11, `wlr-randr` or 
`swaybg` on Wayfire), the program will display a message and terminate with exit code 1.

- If a missing dependency just stops some feature from working, Azote will display a message and start normally.

```text
$ azote
python-send2trash package not found - deleting pictures unavailable
Running on Wayland, but not sway
Available screen height: 1030 px; measurement delay: 5 ms
```

<img src="https://user-images.githubusercontent.com/20579136/170864580-840e1c27-702d-40f4-a98c-a460826b805c.png" width=640 alt="screenshot"><br>

## Project assumptions

The most commonly used *desktop background browser and setter* is aimed at X windows, and does not work with 
wlroots-based compositors. Since the `swaybg` command does everything we may need, it's enough to give it a GUI. 
In order not to limit the program usage to the single environment, Azote is also capable of using feh 
when running on i3, Openbox or other X11 window managers.

*The description below takes into account the current `master` branch. All the features may or may not be available in the
package already released for a certain Linux distribution. Some features rely on 
[optional dependencies](https://github.com/nwg-piotr/azote#dependencies-as-used-in-the-azote-aur-package).*

### Main features:

- works on wlroots;
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

### Hyprland

Add `exec-once = ~/.azotebg-hyprland` to your hyprland.conf. 

Since v1.12.0, we no longer use common ~/.azotebg file on sway and Hyprland, as they don't detect generic 
display names the same way.

### Wayfire

In `~/.config/wayfire.ini` set `autostart_wf_shell = false`, and replace `background = wf-background` with 
`background = ~/.azotebg`.

**Important:** optional `wlr-randr` / `wlr-randr-git` and `swaybg` packages are necessary.

### X window managers (i3, Openbox, dwm etc.)

You need to execute `~/.fehbg` from your window manager’s startup file.
You'll also need optional `feh` and `python-xlib` (or `python3-xlib`, depending on the distro) packages.

**Important:** optional `python-xlib` and `feh` packages are necessary.

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

### Dependencies (as used in the `azote` Arch package):

- `python` (`python3`)
- `python-setuptools`
- `python-gobject`
- `python-pillow`
- `gtk3`
- `python-cairo`
- `python-send2trash`

### Optional dependencies:

- `python-pillow-jxl-plugin` | `python-pillow-jpegxl-plugin`: for JPEG XL support in Pillow
- `python-pillow-heif`: for HEIF support in Pillow
- `python-pillow-avif-plugin`: for AVIF support in Pillow, also needed for HEIF support
- `imagemagick`: for screen color picker in every environment
- `grim`, `slurp`: for screen color picker on sway / wlroots
- `maim`, `slop`: for screen color picker on X11
- `libappindicator-gtk3`: for tray status icon
- `python-yaml`: for alacritty.yml toolbox
- `swaybg`: for setting background on wlroots-based compositors other than sway
- `feh`: for setting background on X11-based WMs
- `python-xlib`: for checking outputs on X11-based WMs
- `wlr-randr` (`wlr-randr-git`): for checking outputs on wlroots-based compositors other than sway

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
  "tracking_interval_seconds": "5",
  "screen_measurement_delay": "300"
}
```

Azote is being developed on the 1920x1080 box, and some graphics dimensions may not go well with other screens.
The runtime configuration file allows to redefine them:

- `thumb_width` - thumbnail width; changing the value triggers thumbnails regeneration on startup;
- `columns` - initial number of columns in thumbnails preview;
- `color_icon_w`, `color_icon_h`, `clip_prev_size` - define dimensions of pictures which represent colors in the color 
palette view;
- `palette_quality` - affects quality and time of generation of the colour palette on the basis of an image; the less - the
better, but slower; default value is 10;
- `tracking_interval_seconds` - determines how often the current wallpapers folder should be checked for file addition / 
deletion;
- `screen_measurement_delay` (ms) - introduced to resolve [#108](https://github.com/nwg-piotr/azote/issues/108).
Since `Gdk.Screen.height` has been deprecated, there's no reasonable way to determine the screen dimensions. 
We need to open a temporary window and measure its height to open the Azote window with maximum allowed vertical dimension.
Different hardware and window managers need different time to accomplish the task. Increase the value if the (floating) 
window does not scale to the screen height. Decrease as much as possible to speed up launching Azote.

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

### [sway] My outputs use random names, wallpapers get lost after restart

Turn the "Use generic display names" preferences switch on (since v1.9.1).
See [#143](https://github.com/nwg-piotr/azote/issues/143).

### No pictures in thumbnails / display preview

As well thumbnails, as displays preview inherit from the Gtk.Button class. In case you don't see images inside them,
please make sure that button images are turned on in the `~/.config/gtk-3.0/settings.ini` file:

```bash
[Settings]
(...)
gtk-button-images=1
```

### 'Open with...' feature doesn't work

**Azote v1.2.0 and below** - no 'Open with' menu entry at all;

**Azote v1.3.0 and above** - the only program listed is feh.

The `/usr/share/applications/mimeinfo.cache` is probably missing from your system. Regenerate it:

```bash
$ sudo update-desktop-database
```

See https://specifications.freedesktop.org/desktop-entry-spec/0.9.5/ar01s07.html

### Floating Azote window does not scale to the screen height

Since `Gdk.Screen.height` has been deprecated, there's no reasonable way to determine the screen dimensions. 
We need to open a temporary window (maximized or fullscreened on sway) and measure its height to open the Azote 
window with maximum allowed vertical dimension.

*This does not apply to sway, where we measure the screen in another way.*

In `~/.config/azote/azoterc` you'll find the `"screen_measurement_delay": "300"` value. Different hardware 
and window managers need different time to open the temporary window. Increase the value if the (floating) 
window does not scale to the screen height. Decrease as much as possible to speed up launching Azote (and not to 
see the black screen on sway). On my development machine the minimum value is 30 ms on sway and 5 ms on Wayfire.

## X11 / feh notice

You'll be unable to select different modes
*("scale", "max", "fill", "center", "tile")* for certain displays. The list of modes varies from what you see in Sway 
*("stretch", "fit", "fill", "center", "tile")*.
