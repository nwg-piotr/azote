#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
Wallpaper and colour manager for Sway, i3 and some other WMs, as a frontend to swaybg and feh

Author: Piotr Miller & Contributors
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/azote
License: GPL3

"""
import os
import sys
import subprocess
import stat
import gi
import cairo
from PIL import Image
from azote import common

# send2trash module may or may not be available
try:
    from send2trash import send2trash

    common.env['send2trash'] = True
except Exception:
    common.env['send2trash'] = False
    print('python-send2trash package not found - deleting pictures unavailable')

from colorthief import ColorThief

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
from gi.repository.GdkPixbuf import InterpType
from azote.tools import set_env, hash_name, create_thumbnails, file_allowed, update_status_bar, flip_selected_wallpaper, \
    copy_backgrounds, create_pixbuf, split_selected_wallpaper, scale_and_crop, clear_thumbnails, current_display, \
    save_json, load_json
from azote.color_tools import rgba_to_hex, hex_to_rgb, rgb_to_hex, rgb_to_rgba
from azote.plugins import Alacritty, Xresources
from azote.color_tools import WikiColours

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3

    common.env['app_indicator'] = True
except:
    common.env['app_indicator'] = False
    print('libappindicator-gtk3 package not found - tray icon unavailable')

from azote.__about__ import __version__

def get_files():
    try:
        inames = "-iname \"*."+"\" -o -iname \"*.".join(common.allowed_file_types)+"\""
        files = subprocess.check_output("find '%s' -mindepth 1 %s" %(common.settings.src_path, inames), shell=True).decode().split("\n")[:-1]
        file_names = [f.replace(common.settings.src_path+"/", "") for f in files]
    except FileNotFoundError:
        common.settings.src_path = os.getenv('HOME')
        file_names = [f for f in os.listdir(common.settings.src_path)
                      if os.path.isfile(os.path.join(common.settings.src_path, f))]

    if common.settings.sorting == 'new':
        file_names.sort(reverse=True, key=lambda f: os.path.getmtime(os.path.join(common.settings.src_path, f)))
    elif common.settings.sorting == 'old':
        file_names.sort(key=lambda f: os.path.getmtime(os.path.join(common.settings.src_path, f)))
    elif common.settings.sorting == 'az':
        file_names.sort()
    elif common.settings.sorting == 'za':
        file_names.sort(reverse=True)

    return file_names


class Preview(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

        self.set_border_width(10)
        self.set_propagate_natural_height(True)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)

        common.thumbnails_list = []
        self.grid = Gtk.FlowBox()
        self.grid.set_valign(Gtk.Align.START)
        # self.grid.set_max_children_per_line(30)
        self.grid.set_selection_mode(Gtk.SelectionMode.NONE)

        create_thumbnails(common.settings.src_path)
        self.files_dict = dict([(f, None) for f in os.listdir(common.settings.src_path)])

        src_pictures = get_files()

        for file in src_pictures:
            if file_allowed(file):
                thumbnail = Thumbnail(common.settings.src_path, file)
                common.thumbnails_list.append(thumbnail)
                self.grid.add(thumbnail)

        self.add(self.grid)

    def refresh(self, create_thumbs=True):
        self.files_dict = dict([(f, None) for f in os.listdir(common.settings.src_path)])

        if create_thumbs:
            create_thumbnails(common.settings.src_path)

        for thumbnail in common.thumbnails_list:
            self.grid.remove(thumbnail)
            thumbnail.destroy()

        src_pictures = get_files()

        for file in src_pictures:
            if file_allowed(file):
                thumbnail = Thumbnail(common.settings.src_path, file)
                common.thumbnails_list.append(thumbnail)
                self.grid.add(thumbnail)

                thumbnail.show_all()
                thumbnail.toolbar.hide()

        update_status_bar()


class Thumbnail(Gtk.VBox):
    def __init__(self, folder, filename):
        super().__init__()
        self.toolbar = ImageToolbar(self)
        self.add(self.toolbar)

        self.image_button = Gtk.Button()
        self.image_button.set_property("name", "thumb-btn")
        self.image_button.set_always_show_image(True)

        self.folder = folder
        self.filename = filename
        self.source_path = os.path.join(folder, filename)

        self.img = Gtk.Image()
        self.thumb_file = "{}.png".format(os.path.join(common.thumb_dir, hash_name(self.source_path)))
        self.img.set_from_file(self.thumb_file)

        self.image_button.set_image(self.img)
        self.image_button.set_image_position(2)  # TOP
        self.image_button.set_tooltip_text(common.lang['thumbnail_tooltip'])

        if len(filename) > 30:
            filename = '…{}'.format(filename[-28::])
        self.image_button.set_label(filename)
        self.selected = False

        # self.connect('clicked', self.on_button_press)
        self.image_button.connect('button-press-event', self.on_image_button_press)

        self.add(self.image_button)

    def on_image_button_press(self, button, event):

        self.select(button)

        if event.type == Gdk.EventType._2BUTTON_PRESS:
            on_thumb_double_click(button)
        if event.button == 3:
            show_image_menu(self)

    def on_menu_button_press(self, button):
        show_image_menu(self)

    def select(self, thumbnail):
        if common.split_button:
            common.split_button.set_sensitive(True)

        common.apply_to_all_button.set_sensitive(True)

        self.image_button.selected = True
        common.selected_wallpaper = self
        deselect_all()
        if common.settings.image_menu_button:
            self.toolbar.show_all()
        thumbnail.set_property("name", "thumb-btn-selected")

        with Image.open(self.source_path) as img:
            filename = self.filename
            if len(filename) > 30:
                filename = '…{}'.format(filename[-28::])
            common.selected_picture_label.set_text("{} ({} x {})".format(filename, img.size[0], img.size[1]))

    def deselect(self, thumbnail):
        self.selected = False
        self.toolbar.hide()
        thumbnail.image_button.set_property("name", "thumb-btn")


def deselect_all():
    for thumbnail in common.thumbnails_list:
        thumbnail.deselect(thumbnail)


class ImageToolbar(Gtk.HBox):
    def __init__(self, thumbnail):
        super().__init__()
        self.parent_thumbnail = thumbnail
        self.set_spacing(0)
        self.set_border_width(0)

        test_label = Gtk.Label()
        test_label.set_text('')
        self.pack_start(test_label, True, True, 0)

        self.menu_btn = Gtk.EventBox()
        img = Gtk.Image()
        img.set_from_file('images/icon_image_menu.svg')
        self.menu_btn.add(img)
        self.menu_btn.connect('button-press-event', self.on_menu_button_press)
        self.pack_start(self.menu_btn, False, False, 0)

    def on_menu_button_press(self, button, event):
        show_image_menu(self.parent_thumbnail, from_toolbar=True)


class DisplayBox(Gtk.Box):
    """
    The box contains elements to preview certain displays and assign wallpapers to them
    """

    def __init__(self, name, width, height, path=None, thumb=None, xrandr_idx=None):
        super().__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)

        # Values to assigned to corresponding display when apply button pressed
        self.display_name = name
        self.wallpaper_path = path
        self.thumbnail_path = thumb
        self.mode = 'fill' if common.sway or common.env['wayland'] else 'scale'
        self.color = None
        self.xrandr_idx = xrandr_idx
        self.include = True

        if thumb and os.path.isfile(thumb):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(thumb)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file('images/empty.png')
        pixbuf = pixbuf.scale_simple(common.settings.thumb_size[0], common.settings.thumb_size[1], InterpType.BILINEAR)

        self.img = Gtk.Image.new_from_pixbuf(pixbuf)

        self.select_button = Gtk.Button()
        self.select_button.set_always_show_image(True)
        self.select_button.set_label("{} ({} x {})".format(name, width, height))  # label on top: name (with x height)
        self.select_button.set_image(self.img)  # preview of selected wallpaper
        self.select_button.set_image_position(3)  # label on top, image below
        self.select_button.set_property("name", "display-btn")  # to assign css style
        self.select_button.set_tooltip_text(common.lang['set_selected_wallpaper'])

        self.pack_start(self.select_button, False, False, 10)

        self.select_button.connect_after('clicked', self.on_select_button)

        # Combo box to choose a mode to use for the image
        mode_selector = Gtk.ListStore(str)

        if common.sway or common.env['wayland']:
            for mode in common.modes_swaybg:
                mode_selector.append([mode])
        else:
            for mode in common.modes_feh:
                mode_selector.append([mode])

        # Let's display the mode combo and the color button side-by-side in a vertical box
        options_box = Gtk.Box()
        options_box.set_spacing(15)
        options_box.set_border_width(0)
        options_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.pack_start(options_box, True, False, 0)

        check_button = Gtk.CheckButton()
        check_button.set_active(self.include)
        check_button.set_tooltip_text(common.lang["include_when_splitting"])
        check_button.connect("toggled", self.switch_included)
        options_box.pack_start(check_button, False, False, 0)

        self.mode_combo = Gtk.ComboBox.new_with_model(mode_selector)
        self.mode_combo.set_active(2)
        self.mode_combo.connect("changed", self.on_mode_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.mode_combo.pack_start(renderer_text, True)
        self.mode_combo.add_attribute(renderer_text, "text", 0)
        self.mode_combo.set_tooltip_text(common.lang['display_mode'])
        options_box.add(self.mode_combo)

        if common.sway or common.env['wayland']:
            # Color button
            self.color_button = Gtk.ColorButton()
            color = Gdk.RGBA()
            color.red = 0.0
            color.green = 0.0
            color.blue = 0.0
            color.alpha = 1.0
            self.color_button.set_rgba(color)
            self.color_button.connect("color-set", self.on_color_chosen, self.color_button)
            self.color_button.set_tooltip_text(common.lang['background_color'])
            options_box.add(self.color_button)

        self.flip_button = Gtk.Button()
        self.flip_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_flip.svg')
        self.flip_button.set_image(img)
        self.flip_button.set_tooltip_text(common.lang['flip_image'])
        self.flip_button.set_sensitive(False)
        self.flip_button.connect('clicked', self.on_flip_button)
        self.flip_button.set_tooltip_text(common.lang['flip_wallpaper_horizontally'])
        options_box.pack_start(self.flip_button, True, True, 0)

    def switch_included(self, ckb):
        self.include = ckb.get_active()

    def clear_color_selection(self):
        # If not on sway / swaybg, we have no color_button in UI
        if common.sway or common.env['wayland']:
            # clear color selection: image will be used
            color = Gdk.RGBA()
            color.red = 0.0
            color.green = 0.0
            color.blue = 0.0
            color.alpha = 1.0
            self.color_button.set_rgba(color)
            self.color = None

    def on_select_button(self, button):
        if common.selected_wallpaper:
            self.img.set_from_file(common.selected_wallpaper.thumb_file)
            self.wallpaper_path = common.selected_wallpaper.source_path
            self.thumbnail_path = common.selected_wallpaper.thumb_file
            button.set_property("name", "display-btn-selected")
            self.flip_button.set_sensitive(True)

            self.clear_color_selection()

            common.apply_button.set_sensitive(True)

    def on_mode_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            mode = model[tree_iter][0]
            self.mode = mode

        # If our backend is feh, not swaybg, we can not set mode for each wallpaper separately.
        # Let's copy the same selection to all displays.
        if not common.sway and common.env['wayland'] and common.display_boxes_list:
            selection = combo.get_active()
            for box in common.display_boxes_list:
                box.mode_combo.set_active(selection)

    def on_color_chosen(self, user_data, button):
        self.color = rgba_to_hex(button.get_rgba())
        # clear selected image to indicate it won't be used
        self.img.set_from_file("images/empty.png")
        common.apply_button.set_sensitive(True)

    def on_flip_button(self, button):
        # convert images and get (thumbnail path, flipped image path)
        images = flip_selected_wallpaper()
        self.img.set_from_file(images[0])
        self.wallpaper_path = images[1]
        self.thumbnail_path = images[0]
        self.flip_button.set_sensitive(False)


class SortingButton(Gtk.Button):
    def __init__(self):
        super().__init__()
        self.set_always_show_image(True)
        self.img = Gtk.Image()
        self.refresh()
        self.set_tooltip_text(common.lang['sorting_order'])
        self.connect('clicked', self.on_sorting_button)

    def refresh(self):
        if common.settings.sorting == 'old':
            self.img.set_from_file('images/icon_old.svg')
        elif common.settings.sorting == 'az':
            self.img.set_from_file('images/icon_az.svg')
        elif common.settings.sorting == 'za':
            self.img.set_from_file('images/icon_za.svg')
        else:
            self.img.set_from_file('images/icon_new.svg')
        self.set_image(self.img)

    def on_sorting_button(self, widget):
        menu = Gtk.Menu()
        i0 = Gtk.MenuItem.new_with_label(common.lang['sorting_new'])
        i0.connect('activate', self.on_i0)
        menu.append(i0)
        i1 = Gtk.MenuItem.new_with_label(common.lang['sorting_old'])
        i1.connect('activate', self.on_i1)
        menu.append(i1)
        i2 = Gtk.MenuItem.new_with_label(common.lang['sorting_az'])
        i2.connect('activate', self.on_i2)
        menu.append(i2)
        i3 = Gtk.MenuItem.new_with_label(common.lang['sorting_za'])
        i3.connect('activate', self.on_i3)
        menu.append(i3)
        menu.show_all()
        menu.popup_at_widget(widget, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_WEST, None)

    def on_i0(self, widget):
        common.settings.sorting = 'new'
        common.settings.save()
        self.refresh()
        common.preview.refresh()

    def on_i1(self, widget):
        common.settings.sorting = 'old'
        common.settings.save()
        self.refresh()
        common.preview.refresh()

    def on_i2(self, widget):
        common.settings.sorting = 'az'
        common.settings.save()
        self.refresh()
        common.preview.refresh()

    def on_i3(self, widget):
        common.settings.sorting = 'za'
        common.settings.save()
        self.refresh()
        common.preview.refresh()


def on_apply_button(button):
    """
    Create the command for swaybg (Sway) or feh (X11)
    """
    # Copy modified wallpapers (if any) from temporary to backgrounds folder
    copy_backgrounds()

    if common.sway or common.env['wayland']:
        # On next startup we'll want to restore what we're setting here. Let's save it to json files
        # instead of parsing .azoteb / .fehbg. We only save pictures.
        restore_from_file = os.path.join(common.data_home, "swaybg.json")
        restore_from = []

        # Prepare, save and execute the shell script for swaybg. It'll be placed in ~/.azotebg for further use.
        batch_content = ['#!/usr/bin/env bash', 'pkill swaybg']
        for box in common.display_boxes_list:
            if box.color:
                # if a color chosen, the wallpaper won't appear
                batch_content.append("swaybg -o {} -c{} &".format(box.display_name, box.color))
            elif box.wallpaper_path:
                # see: https://github.com/nwg-piotr/azote/issues/143
                if common.settings.generic_display_names:
                    display_name = ""
                    for item in common.displays:
                        if item["name"] == box.display_name:
                            display_name = item["generic-name"]
                else:
                    display_name = box.display_name

                # Escape some special characters which would mess up the script
                wallpaper_path = box.wallpaper_path.replace('\\', '\\\\').replace("$", "\$").replace("`",
                                                                                                     "\\`").replace('"',
                                                                                                                    '\\"')

                batch_content.append(
                    "swaybg -o '{}' -i \"{}\" -m {} &".format(display_name, wallpaper_path, box.mode))

                # build the json file content
                if box.wallpaper_path.startswith("{}/backgrounds-sway/flipped-".format(common.data_home)):
                    thumb = "thumbnail-{}".format(box.wallpaper_path.split("flipped-")[1])
                    thumb = os.path.join(common.data_home, "backgrounds-sway", thumb)

                elif box.wallpaper_path.startswith("{}/backgrounds-sway/part".format(common.data_home)):
                    thumb = "thumb-part{}".format(box.wallpaper_path.split("part")[1])
                    thumb = os.path.join(common.data_home, "backgrounds-sway", thumb)

                else:
                    thumb = "{}.png".format(hash_name(box.wallpaper_path))
                    thumb = os.path.join(common.data_home, "thumbnails", thumb)

                entry = {"name": box.display_name, "path": box.wallpaper_path, "thumb": thumb}
                restore_from.append(entry)

        with open(common.cmd_file, 'w') as f:
            for item in batch_content:
                f.write("%s\n" % item)
        # make the file executable
        st = os.stat(common.cmd_file)
        os.chmod(common.cmd_file, st.st_mode | stat.S_IEXEC)

        subprocess.call(common.cmd_file, shell=True)

        save_json(restore_from, restore_from_file)

    else:
        # As above
        restore_from_file = os.path.join(common.data_home, "feh.json")
        restore_from = []

        # Prepare and execute the feh command. It's being saved automagically to ~/.fehbg
        mode = common.display_boxes_list[0].mode  # They are all the same, just check the 1st one
        command = "feh --bg-{}".format(mode)
        c = common.display_boxes_list.copy()
        c = sorted(c, key=lambda x: x.xrandr_idx)
        for box in c:
            command += " '{}'".format(box.wallpaper_path)

            # build the json file content
            if box.wallpaper_path.startswith("{}/backgrounds-feh/flipped-".format(common.data_home)):
                thumb = "thumbnail-{}".format(box.wallpaper_path.split("flipped-")[1])
                thumb = os.path.join(common.data_home, "backgrounds-feh", thumb)

            elif box.wallpaper_path.startswith("{}/backgrounds-feh/part".format(common.data_home)):
                thumb = "thumb-part{}".format(box.wallpaper_path.split("part")[1])
                thumb = os.path.join(common.data_home, "backgrounds-feh", thumb)

            else:
                thumb = "{}.png".format(hash_name(box.wallpaper_path))
                thumb = os.path.join(common.data_home, "thumbnails", thumb)

            entry = {"name": box.display_name, "path": box.wallpaper_path,
                     "thumb": thumb}
            restore_from.append(entry)

        subprocess.call(command, shell=True)

        save_json(restore_from, restore_from_file)


def on_split_button(button):
    if common.selected_wallpaper:
        common.apply_button.set_sensitive(True)
        num_parts = 0
        for item in common.display_boxes_list:
            if item.include:
                num_parts += 1
        paths = split_selected_wallpaper(num_parts)
        i = 0
        for box in common.display_boxes_list:
            if box.include:
                box.wallpaper_path = paths[i][0]
                box.img.set_from_file(paths[i][1])
                box.thumbnail_path = paths[i][1]
                i += 1

    if common.display_boxes_list:
        for box in common.display_boxes_list:
            box.clear_color_selection()


def open_with(item, opener):
    # if feh selected as the opener, let's start it with options as below
    if opener == 'feh':
        command = 'feh --start-at "{}" --scale-down --no-fehbg -d --output-dir {}'.format(
            common.selected_wallpaper.source_path, common.selected_wallpaper.folder)
    # elif could specify options for other certain programs here
    elif opener == 'swappy':
        command = 'swappy -f {}'.format(common.selected_wallpaper.source_path)
    else:
        command = '{} "{}"'.format(opener, common.selected_wallpaper.source_path)
    subprocess.Popen(command, shell=True)


def clear_wallpaper_selection():
    common.selected_wallpaper = None
    common.selected_picture_label.set_text(common.lang['no_picture_selected'])
    if common.split_button:
        common.split_button.set_sensitive(False)
    common.apply_button.set_sensitive(False)
    common.apply_to_all_button.set_sensitive(False)


def on_about_button(button):
    dialog = Gtk.AboutDialog()
    dialog.set_program_name('Azote')

    try:
        # version = pkg_resources.require(common.app_name)[0].version
        dialog.set_version("v{}".format(__version__))
    except Exception as e:
        print("Couldn't check version: {}".format(e))
        pass

    logo = GdkPixbuf.Pixbuf.new_from_file_at_size('images/azote.svg', 96, 96)

    dialog.set_keep_above(True)
    dialog.set_logo(logo)
    dialog.set_copyright('(c) 2019-2023 Piotr Miller & Contributors')
    dialog.set_website('https://github.com/nwg-piotr/azote')
    dialog.set_comments(common.lang['app_desc'])
    dialog.set_license_type(Gtk.License.GPL_3_0)
    dialog.set_authors(['Piotr Miller (nwg) and Contributors', 'Libraries and dependencies:',
                        '- colorthief python module (c) 2015 Shipeng Feng',
                        '- python-pillow (c) 1995-2011, Fredrik Lundh, 2010-2019 Alex Clark and Contributors',
                        '- pygobject (c) 2005-2019 The GNOME Project',
                        '- GTK+ (c) 2007-2019 The GTK Team',
                        '- feh (c) 1999,2000 Tom Gilbert, 2010-2018 Daniel Friesel',
                        '- swaybg (c) 2016-2019 Drew DeVault',
                        '- wlr-randr (c) 2019 Purism SPC and Contributors',
                        '- send2trash python module (c) 2017 Virgil Dupras',
                        '- grim, slurp (c) 2018 emersion',
                        '- maim, slop (c) 2014 Dalton Nell and Contributors',
                        '- imagemagick (c) 1999-2019 ImageMagick Studio LLC',
                        '- PyYAML (c) 2017-2019 Ingy döt Net Copyright (c) 2006-2016 Kirill Simonov'])
    dialog.set_translator_credits('xsme, Leon-Plickat (de_DE), HumanG33k (fr_FR)')
    dialog.set_artists(['edskeye'])

    dialog.show()

    dialog.run()
    dialog.destroy()
    return False


def move_to_trash(widget):
    send2trash(common.selected_wallpaper.source_path)
    if os.path.isfile(common.selected_wallpaper.thumb_file):
        send2trash(common.selected_wallpaper.thumb_file)
    clear_wallpaper_selection()
    common.preview.refresh()


def show_image_menu(widget, event=None, parent=None, from_toolbar=False):
    cd = current_display()
    if common.selected_wallpaper:
        if common.associations:  # not None if /usr/share/applications/mimeinfo.cache found and parse
            openers = common.associations[common.selected_wallpaper.source_path.split('.')[-1]]
            menu = Gtk.Menu()
            if openers:
                for opener in openers:
                    # opener = (Name, Exec)
                    item = Gtk.MenuItem.new_with_label(common.lang['open_with'].format(opener[0]))
                    item.connect('activate', open_with, opener[1])
                    menu.append(item)
                item = Gtk.SeparatorMenuItem()
                menu.append(item)

            item = Gtk.MenuItem.new_with_label(common.lang['create_palette'])
            menu.append(item)
            submenu = Gtk.Menu()

            # Hell knows why the library does not return the tuple of expected length for some num_colors values
            # Let's cheat a little bit
            subitem = Gtk.MenuItem.new_with_label('6 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 6)
            submenu.append(subitem)

            subitem = Gtk.MenuItem.new_with_label('12 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 13)
            submenu.append(subitem)

            subitem = Gtk.MenuItem.new_with_label('18 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 19)
            submenu.append(subitem)

            subitem = Gtk.MenuItem.new_with_label('24 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 25)
            submenu.append(subitem)

            item.set_submenu(submenu)

            item = Gtk.MenuItem.new_with_label(common.lang['scale_and_crop'])
            menu.append(item)
            submenu = Gtk.Menu()

            # Scale and crop to detected displays dimension
            for i in range(len(common.displays)):
                display = common.displays[i]
                width, height = display['width'], display['height']
                subitem = Gtk.MenuItem.new_with_label(
                    '{} x {} ({})'.format(width, height, display['name']))
                subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path, width, height)
                submenu.append(subitem)

            # Scale and crop to double width of the primary display
            display = common.displays[cd]
            width, height = display['width'] * 2, display['height']
            subitem = Gtk.MenuItem.new_with_label(
                '{} x {} ({} {} {})'.format(width, height, common.lang['current'], display['name'],
                                            common.lang['dual_width']))
            subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path, width, height)
            submenu.append(subitem)

            # Scale and crop to double height of the primary display
            display = common.displays[cd]
            width, height = display['width'], display['height'] * 2
            subitem = Gtk.MenuItem.new_with_label(
                '{} x {} ({} {} {})'.format(width, height, common.lang['current'], display['name'],
                                            common.lang['dual_height']))
            subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path, width, height)
            submenu.append(subitem)

            # Scale and crop to triple width of the primary display
            display = common.displays[cd]
            width, height = display['width'] * 3, display['height']
            subitem = Gtk.MenuItem.new_with_label(
                '{} x {} ({} {} {})'.format(width, height, common.lang['current'], display['name'],
                                            common.lang['triple_width']))
            subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path, width, height)
            submenu.append(subitem)

            # Scale and crop to triple height of the primary display
            display = common.displays[cd]
            width, height = display['width'], display['height'] * 3
            subitem = Gtk.MenuItem.new_with_label(
                '{} x {} ({} {} {})'.format(width, height, common.lang['current'], display['name'],
                                            common.lang['triple_height']))
            subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path, width, height)
            submenu.append(subitem)

            # Scale and crop to user-defined dimensions
            if common.settings.custom_display:
                subitem = Gtk.MenuItem.new_with_label(
                    '{} x {} ({})'.format(common.settings.custom_display[1], common.settings.custom_display[2],
                                          common.settings.custom_display[0]))
                subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path,
                                int(common.settings.custom_display[1]), int(common.settings.custom_display[2]))
                submenu.append(subitem)

            item.set_submenu(submenu)

            if common.env['send2trash']:
                item = Gtk.SeparatorMenuItem()
                menu.append(item)
                item = Gtk.MenuItem.new_with_label(common.lang['remove_image'])
                menu.append(item)
                submenu = Gtk.Menu()
                item1 = Gtk.MenuItem.new_with_label(common.lang['move'])
                item1.connect('activate', move_to_trash)
                submenu.append(item1)
                item.set_submenu(submenu)

            menu.show_all()
            # We don't want the menu to stick out of the window on Sway, as it may be partially not clickable

            menu.popup_at_pointer(None)

        else:  # fallback in case mimeinfo.cache not found
            print("No registered program found. Does the /usr/share/applications/mimeinfo.cache file exist?")
            command = 'feh --start-at {} --scale-down --no-fehbg -d --output-dir {}'.format(
                common.selected_wallpaper.source_path, common.selected_wallpaper.folder)
            subprocess.Popen(command, shell=True)


def on_refresh_clicked(button):
    clear_wallpaper_selection()
    common.preview.refresh()


def generate_palette(item, thumb_file, filename, image_path, num_colors):
    color_thief = ColorThief(image_path)
    # dominant = color_thief.get_color(quality=10)
    palette = color_thief.get_palette(color_count=num_colors, quality=common.settings.palette_quality)
    if common.cpd:
        common.cpd.close()
    common.cpd = ColorPaletteDialog(thumb_file, filename, palette)


def on_folder_clicked(button):
    dialog = Gtk.FileChooserDialog(title=common.lang['open_folder'], parent=button.get_toplevel(),
                                   action=Gtk.FileChooserAction.SELECT_FOLDER)
    dialog.set_current_folder(common.settings.src_path)
    dialog.add_button(Gtk.STOCK_CANCEL, 0)
    dialog.add_button(Gtk.STOCK_OK, 1)
    dialog.set_default_response(1)
    dialog.set_default_size(800, 600)

    response = dialog.run()
    if response == 1:
        common.settings.src_path = dialog.get_filename()
        common.settings.save()
        dialog.destroy()
        common.preview.refresh()
        text = common.settings.src_path
        if len(text) > 40:
            text = '…{}'.format(text[-38::])
        button.set_label(text)

    dialog.destroy()
    clear_wallpaper_selection()


def destroy(self):
    Gtk.main_quit()


def check_height_and_start(window):
    w, h = window.get_size()
    window.destroy()
    if common.sway or common.env['wm'] == "i3":
        h = int(h * 0.95)
    print(
        "Available screen height: {} px; measurement delay: {} ms".format(h, common.settings.screen_measurement_delay))
    app = GUI(h)


class TransparentWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.connect('draw', self.draw)
        self.set_title("Checking...")
        # Credits for transparency go to KurtJacobson:
        # https://gist.github.com/KurtJacobson/374c8cb83aee4851d39981b9c7e2c22c
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

    def draw(self, widget, context):
        context.set_source_rgba(0, 0, 0, 0.0)
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)


class GUI:
    def __init__(self, height):

        # set app_id for Wayland
        GLib.set_prgname('azote')

        window = Gtk.Window()
        h = height

        window.set_default_size(common.settings.thumb_width * (common.settings.columns + 1), h)
        common.main_window = window

        window.set_title("Azote~")
        window.set_icon_name("azote")
        window.set_role("azote")

        window.connect_after('destroy', destroy)
        window.connect("key-release-event", self.handle_keyboard)

        main_box = Gtk.Box()
        main_box.set_spacing(5)
        main_box.set_border_width(10)
        main_box.set_orientation(Gtk.Orientation.VERTICAL)

        common.progress_bar = Gtk.ProgressBar()
        common.progress_bar.set_fraction(0.0)
        common.progress_bar.set_text('0')
        common.progress_bar.set_show_text(True)
        main_box.pack_start(common.progress_bar, True, False, 0)
        window.add(main_box)
        window.show_all()

        # This contains a Gtk.ScrolledWindow with Gtk.Grid() inside, filled with ThumbButton(Gtk.Button) instances
        common.preview = Preview()

        main_box.pack_start(common.preview, False, False, 0)

        # We need a horizontal container to display outputs in columns
        displays_box = Gtk.Box()
        displays_box.set_spacing(15)
        displays_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # Restore saved wallpapers if any
        f_name = "swaybg.json" if common.sway or common.env['wayland'] else "feh.json"
        f_path = os.path.join(common.data_home, f_name)

        if os.path.isfile(f_path):
            restore_from = load_json(f_path)
        else:
            restore_from = None

        # Buttons below represent displays preview
        common.display_boxes_list = []
        for display in common.displays:
            name = display.get('name')
            # Check if we have stored values
            path, thumb = None, None
            if restore_from:
                for item in restore_from:
                    if item["name"] == name:
                        path = item["path"]
                        thumb = item["thumb"]

            # Label format: name (width x height)
            try:
                xrandr_idx = display.get('xrandr-idx')
            except KeyError:
                xrandr_idx = None
            display_box = DisplayBox(name, display.get('width'), display.get('height'), path, thumb, xrandr_idx)
            common.display_boxes_list.append(display_box)
            displays_box.pack_start(display_box, True, False, 0)

        main_box.pack_start(displays_box, False, False, 0)

        # Bottom buttons will also need a horizontal container
        bottom_box = Gtk.Box()
        bottom_box.set_spacing(5)
        bottom_box.set_border_width(5)
        bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # Button to change sorting order
        sorting_button = SortingButton()
        bottom_box.add(sorting_button)

        # Button to refresh currently selected folder thumbnails
        refresh_button = Gtk.Button()
        refresh_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_refresh.svg')
        refresh_button.set_image(img)
        refresh_button.set_tooltip_text(common.lang['refresh_folder_preview'])
        bottom_box.add(refresh_button)
        refresh_button.connect_after('clicked', on_refresh_clicked)

        # Button to set the wallpapers folder
        folder_button = Gtk.Button.new_with_label(common.settings.src_path)
        folder_button.set_property("name", "folder-btn")
        folder_button.set_tooltip_text(common.lang['open_another_folder'])
        bottom_box.pack_start(folder_button, True, True, 0)
        folder_button.connect_after('clicked', on_folder_clicked)

        # Label to display details of currently selected picture
        common.selected_picture_label = Gtk.Label()
        common.selected_picture_label.set_property("name", "selected-label")
        common.selected_picture_label.set_text(common.lang['no_picture_selected'])

        bottom_box.pack_start(common.selected_picture_label, True, True, 0)

        # Button to split wallpaper between displays
        if len(common.displays) > 1:
            common.split_button = Gtk.Button()
            common.split_button.set_always_show_image(True)
            img = Gtk.Image()
            img.set_from_file('images/icon_split.svg')
            common.split_button.set_image(img)
            bottom_box.add(common.split_button)
            common.split_button.set_sensitive(False)
            common.split_button.set_tooltip_text(common.lang['split_selection_between_displays'])
            common.split_button.connect('clicked', on_split_button)

        # Button to apply selected wallpaper to all displays (connected at the moment or not)
        common.apply_to_all_button = Gtk.Button()
        common.apply_to_all_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_all.svg')
        common.apply_to_all_button.set_image(img)
        common.apply_to_all_button.connect('clicked', on_apply_to_all_button)
        common.apply_to_all_button.set_sensitive(False)
        common.apply_to_all_button.set_tooltip_text(common.lang['apply_to_all'])
        bottom_box.add(common.apply_to_all_button)

        # Button to apply settings
        names = ''
        for display in common.displays:
            names += '{} '.format(display['name'])

        common.apply_button = Gtk.Button()
        common.apply_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_apply.svg')
        common.apply_button.set_image(img)
        common.apply_button.connect('clicked', on_apply_button)
        common.apply_button.set_sensitive(False)
        common.apply_button.set_tooltip_text(common.lang['apply_settings'].format(names))
        bottom_box.add(common.apply_button)

        main_box.add(bottom_box)

        h_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.add(h_separator)

        # Another horizontal container for the status line + button(s)
        status_box = Gtk.Box()
        status_box.set_spacing(5)
        status_box.set_border_width(5)
        status_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # Button to call About dialog
        about_button = Gtk.Button()
        about_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_about.svg')
        about_button.set_image(img)
        about_button.set_tooltip_text(common.lang['about_azote'])
        about_button.connect('clicked', on_about_button)
        status_box.add(about_button)

        # Button to display settings menu
        settings_button = Gtk.Button()
        settings_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_menu.svg')
        settings_button.set_image(img)
        settings_button.set_tooltip_text(common.lang['preferences'])
        settings_button.connect('clicked', on_settings_button)
        status_box.add(settings_button)

        # Color picker button
        picker_button = Gtk.Button()
        picker_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_picker.svg')
        picker_button.set_image(img)
        picker_button.set_sensitive(common.picker)
        if common.sway or common.env['wayland']:
            tt = common.lang['screen_color_picker'] if common.picker else common.lang['grim_slurp_required']
        else:
            tt = common.lang['screen_color_picker'] if common.picker else common.lang['maim_slop_required']
        picker_button.set_tooltip_text(tt)
        picker_button.connect('clicked', on_picker_button)
        status_box.add(picker_button)

        # dotfiles button
        dotfiles_button = Gtk.Button()
        dotfiles_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_config.svg')
        dotfiles_button.set_image(img)
        active = common.xresources or common.alacritty_config and common.env['yaml']
        if active:
            dotfiles_button.set_tooltip_text(common.lang['dotfiles'])
        else:
            dotfiles_button.set_tooltip_text(common.lang['check_log'].format(common.log_file))
            dotfiles_button.set_sensitive(False)
        dotfiles_button.connect('clicked', on_dotfiles_button)
        status_box.add(dotfiles_button)

        common.status_bar = Gtk.Statusbar()
        common.status_bar.set_property("name", "status-bar")
        common.status_bar.set_halign(Gtk.Align.CENTER)
        status_box.pack_start(common.status_bar, True, True, 0)
        update_status_bar()

        btn = Gtk.Button.new_with_label(common.lang["close"])
        btn.connect("clicked", Gtk.main_quit)
        btn.set_property("valign", Gtk.Align.CENTER)
        status_box.pack_end(btn, False, False, 0)

        main_box.add(status_box)

        window.show_all()
        deselect_all()

        common.progress_bar.hide()

    def handle_keyboard(self, item, event):
        if event.type == Gdk.EventType.KEY_RELEASE and event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
        return True


def on_apply_to_all_button(button):
    """
    This will create a single command to set the same wallpaper to all displays, CONNECTED at the time OR NOT.
    Menu for modes needs to differ for swaybg and feh.
    """
    menu = Gtk.Menu()
    if common.sway or common.env['wayland']:
        for mode in common.modes_swaybg:
            item = Gtk.MenuItem.new_with_label(mode)
            item.connect('activate', apply_to_all_swaybg, mode)
            menu.append(item)
        menu.show_all()
        menu.popup_at_widget(button, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_EAST, None)
    else:
        for mode in common.modes_feh:
            item = Gtk.MenuItem.new_with_label(mode)
            item.connect('activate', apply_to_all_feh, mode)
            menu.append(item)
        menu.show_all()
        menu.popup_at_widget(button, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_EAST, None)


def on_settings_button(button):
    menu = Gtk.Menu()

    item = Gtk.MenuItem.new_with_label(common.lang['custom_display'])
    item.connect('activate', show_custom_display_dialog)
    menu.append(item)

    item = Gtk.CheckMenuItem.new_with_label(common.lang['color_dictionary'])
    item.set_active(common.settings.color_dictionary)
    item.connect('activate', switch_color_dictionary)
    menu.append(item)

    item = Gtk.CheckMenuItem.new_with_label(common.lang['image_menu_button'])
    item.set_active(common.settings.image_menu_button)
    item.connect('activate', switch_image_menu_button)
    menu.append(item)

    item = Gtk.CheckMenuItem.new_with_label(common.lang['track_file_changes'])
    item.set_active(common.settings.track_files)
    item.connect('activate', switch_tracking_files)
    menu.append(item)

    item = Gtk.CheckMenuItem.new_with_label(common.lang['use_display_names'])
    item.set_active(common.settings.generic_display_names)
    item.connect('activate', switch_generic_display_names)
    menu.append(item)

    menu.show_all()
    menu.popup_at_widget(button, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_WEST, None)


def pick_color():
    """
    In sway we'll just use grim & slurp to pick a color: it returns accurate values.
    On X11 same should be possible with maim & slop, but it happens to crash.
    In both cases we'll use the same fallback: calculate the dominant colour of a selected region with colorthief.
    This is less accurate, alas.
    :return: tuple (rrr, ggg, bbb)
    """
    color = (255, 255, 255)
    if common.sway or common.env['wayland']:
        try:
            color = hex_to_rgb(subprocess.check_output(
                'grim -g "$(slurp -p)" -t ppm - | convert - -format \'%[pixel:p{0,0}]\' txt:- | awk \'NR==2 {print $3}\'',
                shell=True).decode("utf-8"))
        except:
            try:
                color = get_dominant_from_area()
            except:
                pass
    else:
        try:
            output = subprocess.check_output('maim -st 0 | convert - -resize 1x1! -format \'%[pixel:p{0,0}]\' info:-',
                                             shell=True).decode("utf-8")
            values = output[6:-1].split(",")
            color = (int(values[0]), int(values[1]), int(values[2]))
        except:
            try:
                color = get_dominant_from_area()
            except:
                pass
    return color


def get_dominant_from_area():
    """
    Saves selected area with `grim -g "$(slurp)" common.tmp_dir/azote/temp/area.png`,
    then calculates the dominant color with the colorthief module.
    :return: tuple (r, g, b) or (255, 255, 255) if nothing selected
    """
    dominant = (255, 255, 255)
    if common.sway or common.env['wayland']:
        cmd = 'grim -g "$(slurp)" {}'.format(os.path.join(common.tmp_dir, 'area.png'))
    else:
        cmd = 'maim -s {}'.format(os.path.join(common.tmp_dir, 'area.png'))

    res = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL).returncode
    if res == 0:
        color_thief = ColorThief(os.path.join(common.tmp_dir, 'area.png'))
        try:
            dominant = color_thief.get_color(quality=common.settings.palette_quality)
        except:
            pass

    return dominant


def on_picker_button(button):
    if common.picker_window:
        common.picker_window.close()
    color = pick_color()
    common.picker_window = ColorPickerDialog(color)


def on_dotfiles_button(button):
    if common.xresources or common.alacritty_config:
        menu = Gtk.Menu()
        if common.xresources:
            item = Gtk.MenuItem.new_with_label(common.xresources)
            item.connect('activate', open_dotfile, 'xresources')
            menu.append(item)

        if common.env['yaml'] and common.alacritty_config:
            item = Gtk.MenuItem.new_with_label(common.alacritty_config)
            item.connect('activate', open_dotfile, 'alacritty')
            menu.append(item)
        menu.show_all()
        menu.popup_at_widget(button, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_WEST, None)


def open_dotfile(widget, which):
    if common.dotfile_window:
        common.dotfile_window.close()

    if which == 'alacritty' and common.alacritty_config:
        common.dotfile_window = Alacritty()

    elif which == 'xresources' and common.xresources:
        common.dotfile_window = Xresources()


def show_custom_display_dialog(item):
    cdd = CustomDisplayDialog()


def switch_color_dictionary(item):
    if item.get_active():
        common.settings.color_dictionary = True
        common.settings.save()
    else:
        common.settings.color_dictionary = False
        common.settings.save()


def switch_image_menu_button(item):
    if item.get_active():
        common.settings.image_menu_button = True
        common.settings.save()
    else:
        common.settings.image_menu_button = False
        common.settings.save()


def switch_tracking_files(item):
    if item.get_active():
        common.settings.track_files = True
        common.settings.save()
        GLib.timeout_add_seconds(common.settings.tracking_interval_seconds, track_changes)
    else:
        common.settings.track_files = False
        common.settings.save()
    if common.indicator:
        common.indicator.switch_indication(item)


def switch_generic_display_names(item):
    if item.get_active():
        common.settings.generic_display_names = True
        common.settings.save()
    else:
        common.settings.generic_display_names = False
        common.settings.save()


class ColorPaletteDialog(Gtk.Window):
    def __init__(self, thumb_file, filename, palette):
        super().__init__()

        self.image = Gtk.Image.new_from_file(thumb_file)
        self.label = Gtk.Label()
        self.label.set_text(filename)
        self.label.set_property('name', 'image-label')

        self.set_title(filename)
        self.set_role("toolbox")
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        # self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.MOUSE)
        self.set_keep_above(True)
        self.all_buttons = []

        try:
            self.copy_as = common.settings.copy_as
        except AttributeError:
            self.copy_as = '#rgb'

        self.vbox = Gtk.VBox()
        self.vbox.set_spacing(5)
        self.vbox.set_border_width(15)

        self.vbox.pack_start(self.image, True, True, 15)
        self.vbox.add(self.label)

        self.hbox = Gtk.HBox()
        self.hbox.set_spacing(5)
        self.hbox.set_border_width(5)

        for i in range(len(palette)):
            color = palette[i]
            hex_color = rgb_to_hex(color)

            pixbuf = create_pixbuf((common.settings.color_icon_w, common.settings.color_icon_h), color)
            gtk_image = Gtk.Image.new_from_pixbuf(pixbuf)

            button = Gtk.Button.new_with_label(hex_color)
            button.set_always_show_image(True)
            button.set_image(gtk_image)
            button.set_image_position(2)  # TOP
            if common.settings.color_dictionary:
                exact, closest = common.color_names.get_colour_name(hex_color)
                if exact:
                    name = common.lang['exact'].format(exact)
                else:
                    name = common.lang['closest'].format(closest)
                button.set_tooltip_text('{}'.format(name))
            else:
                button.set_tooltip_text(common.lang['copy'])

            button.connect_after('clicked', self.to_clipboard)
            self.all_buttons.append(button)

            self.hbox.pack_start(button, False, False, 0)

            if (i + 1) % 6 == 0:
                self.vbox.add(self.hbox)
                self.hbox = Gtk.HBox()
                self.hbox.set_spacing(5)
                self.hbox.set_border_width(5)

        button1 = Gtk.RadioButton(label='#rgb')
        button1.connect('toggled', self.rgb_toggled)

        button2 = Gtk.RadioButton.new_with_label_from_widget(button1, 'r, g, b')
        button2.set_label('r, g, b')
        button2.connect('toggled', self.rgb_toggled)

        for button in [button1, button2]:
            if button.get_label() == self.copy_as:
                button.set_active(True)

        label = Gtk.Label()
        label.set_text(common.lang['copy_as'])

        hbox = Gtk.HBox()
        hbox.set_spacing(5)
        hbox.set_border_width(5)

        hbox.pack_start(label, True, False, 0)

        hbox.pack_start(button1, True, False, 0)
        hbox.pack_start(button2, True, False, 0)

        self.vbox.pack_start(hbox, True, True, 0)

        hbox = Gtk.HBox()
        hbox.set_spacing(5)
        hbox.set_border_width(5)

        self.clipboard_preview = ClipboardPreview()
        hbox.pack_start(self.clipboard_preview, False, False, 0)

        self.clipboard_label = Gtk.Label()
        self.clipboard_label.set_text(common.lang['clipboard_empty'])
        hbox.pack_start(self.clipboard_label, True, True, 0)

        button = Gtk.Button.new_with_label(common.lang['close'])
        button.connect_after('clicked', self.close_window)
        hbox.pack_start(button, False, False, 0)

        self.vbox.add(hbox)

        self.add(self.vbox)
        self.show_all()

    def rgb_toggled(self, button):
        state = 'on' if button.get_active() else 'off'
        if state == 'on':
            common.settings.copy_as = button.get_label()
            common.settings.save()

    def close_window(self, widget):
        self.close()

    def show(self):
        self.show_all()

    def to_clipboard(self, widget):
        # clear selection
        for button in self.all_buttons:
            button.set_property("name", "color-btn")
        # mark selected
        widget.set_property("name", "color-btn-selected")

        common.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        if common.settings.copy_as == 'r, g, b':
            t = hex_to_rgb(widget.get_label())
            content = '{}, {}, {}'.format(t[0], t[1], t[2])
        else:
            content = widget.get_label()

        common.clipboard.set_text(content, -1)
        common.clipboard_text = widget.get_label()

        label = '{}'.format(content)
        self.clipboard_preview.update(widget.get_label())
        self.clipboard_label.set_text(label)


class ClipboardPreview(Gtk.ColorButton):
    def __init__(self):
        super().__init__()
        rgba = rgb_to_rgba((255, 255, 255))

        color = Gdk.RGBA()
        color.red = rgba[0]
        color.green = rgba[1]
        color.blue = rgba[2]
        color.alpha = rgba[3]
        self.set_rgba(color)
        self.connect("color-set", self.to_clipboard)

    def update(self, color):
        rgb = hex_to_rgb(color)
        rgba = rgb_to_rgba(rgb)

        color = Gdk.RGBA()
        color.red = rgba[0]
        color.green = rgba[1]
        color.blue = rgba[2]
        color.alpha = rgba[3]
        self.set_rgba(color)

    def to_clipboard(self, widget):
        common.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        rgba = self.get_rgba()
        if common.settings.copy_as == 'r, g, b':
            hex = rgba_to_hex(rgba)
            t = hex_to_rgb(hex)
            content = '{}, {}, {}'.format(t[0], t[1], t[2])
        else:
            content = rgba_to_hex(rgba)
            hex = content

        common.clipboard.set_text(content, -1)
        common.clipboard_text = hex
        label = '{}'.format(content)
        common.cpd.clipboard_label.set_text(label)


class ColorPickerDialog(Gtk.Window):
    def __init__(self, color):
        super().__init__()

        if not color:
            color = (255, 255, 255)

        self.set_title(common.lang['screen_color_picker'])
        self.set_role("toolbox")
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        # self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.MOUSE)
        self.set_keep_above(True)

        try:
            self.copy_as = common.settings.copy_as
        except AttributeError:
            self.copy_as = '#rgb'

        self.vbox = Gtk.VBox()
        self.vbox.set_spacing(5)
        self.vbox.set_border_width(5)

        rgba = rgb_to_rgba(color)

        self.color_button = Gtk.ColorButton()
        rgba_color = Gdk.RGBA()
        rgba_color.red = rgba[0]
        rgba_color.green = rgba[1]
        rgba_color.blue = rgba[2]
        rgba_color.alpha = 1.0
        self.color_button.set_rgba(rgba_color)
        self.color_button.connect("color-set", self.on_color_chosen, self.color_button)
        self.color_button.set_tooltip_text(common.lang['background_color'])
        self.vbox.pack_start(self.color_button, False, False, 0)

        self.label = Gtk.Label()
        self.label.set_text(rgb_to_hex(color))
        self.vbox.add(self.label)

        if common.settings.color_dictionary:
            self.closest_label = Gtk.Label()
            self.closest_label.set_property('name', 'closest')
            exact, closest = common.color_names.get_colour_name(rgb_to_hex(color))
            if exact:
                name = common.lang['exact'].format(exact)
            else:
                name = common.lang['closest'].format(closest)
            self.closest_label.set_text(name)
            self.vbox.add(self.closest_label)

        button1 = Gtk.RadioButton(label='#rgb')
        button1.connect('toggled', self.rgb_toggled)

        button2 = Gtk.RadioButton.new_with_label_from_widget(button1, 'r, g, b')
        button2.set_label('r, g, b')
        button2.connect('toggled', self.rgb_toggled)

        for button in [button1, button2]:
            if button.get_label() == self.copy_as:
                button.set_active(True)

        hbox = Gtk.HBox()
        hbox.set_spacing(5)
        hbox.set_border_width(5)

        hbox.pack_start(button1, True, False, 0)
        hbox.pack_start(button2, True, False, 0)

        self.vbox.add(hbox)

        hbox = Gtk.HBox()
        hbox.set_spacing(5)
        hbox.set_border_width(5)

        button = Gtk.Button.new_with_label(common.lang['copy'])
        button.connect_after('clicked', self.to_clipboard)
        hbox.pack_start(button, True, False, 0)

        button = Gtk.Button()
        button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_picker.svg')
        button.set_image(img)
        button.connect_after('clicked', self.pick_new_color)
        hbox.pack_start(button, True, False, 0)

        button = Gtk.Button.new_with_label(common.lang['close'])
        button.connect_after('clicked', self.close_window)
        hbox.pack_start(button, True, False, 0)

        self.vbox.add(hbox)

        self.add(self.vbox)
        self.show_all()

    def on_color_chosen(self, user_data, button):
        self.label.set_text(rgba_to_hex(button.get_rgba()))
        exact, closest = common.color_names.get_colour_name(self.label.get_text())
        if exact:
            name = common.lang['exact'].format(exact)
        else:
            name = common.lang['closest'].format(closest)
        self.closest_label.set_text(name)

    def rgb_toggled(self, button):
        state = 'on' if button.get_active() else 'off'
        if state == 'on':
            common.settings.copy_as = button.get_label()
            common.settings.save()

    def close_window(self, widget):
        self.close()

    def to_clipboard(self, widget):
        common.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        if common.settings.copy_as == 'r, g, b':
            t = hex_to_rgb(self.label.get_text())
            content = '{}, {}, {}'.format(t[0], t[1], t[2])
        else:
            content = self.label.get_text()

        common.clipboard.set_text(content, -1)
        common.clipboard_text = self.label.get_text()

    def pick_new_color(self, button):
        color = pick_color()
        if not color:
            color = (255, 255, 255)

        rgba = rgb_to_rgba(color)
        rgba_color = Gdk.RGBA()
        rgba_color.red = rgba[0]
        rgba_color.green = rgba[1]
        rgba_color.blue = rgba[2]
        rgba_color.alpha = 1.0
        self.color_button.set_rgba(rgba_color)

        self.label.set_text(rgb_to_hex(color))

        if common.settings.color_dictionary:
            exact, closest = common.color_names.get_colour_name(rgb_to_hex(color))
            if exact:
                name = common.lang['exact'].format(exact)
            else:
                name = common.lang['closest'].format(closest)
            self.closest_label.set_text(name)
            self.vbox.add(self.closest_label)


class CustomDisplayDialog(Gtk.Window):
    def __init__(self):
        super().__init__()

        self.properties = common.settings.custom_display

        self.set_title("Azote custom display")
        self.set_role("toolbox")
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_decorated(False)
        # self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.MOUSE)
        self.set_keep_above(True)

        self.name_label = Gtk.Label()
        self.name_label.set_width_chars(12)
        self.name_label.set_text(common.lang['name'])

        self.name_entry = Gtk.Entry()
        if self.properties and self.properties[0]:
            self.name_entry.set_text(self.properties[0])
        self.name_entry.connect('changed', self.validate_entries)

        self.width_label = Gtk.Label()
        self.width_label.set_width_chars(12)
        self.width_label.set_text(common.lang['width'])

        self.button_ok = Gtk.Button.new_with_label(common.lang['ok'])
        self.button_ok.set_sensitive(False)

        self.width_entry = NumberEntry()
        if self.properties:
            self.width_entry.set_text(self.properties[1])
        self.width_entry.connect('changed', self.validate_entries)

        self.height_label = Gtk.Label()
        self.height_label.set_width_chars(12)
        self.height_label.set_text(common.lang['height'])

        self.height_entry = NumberEntry()
        if self.properties:
            self.height_entry.set_text(self.properties[2])
        self.height_entry.connect('changed', self.validate_entries)

        self.button_cancel = Gtk.Button.new_with_label(common.lang['cancel'])
        self.button_cancel.connect("clicked", self.dialog_cancel, self)

        self.button_clear = Gtk.Button.new_with_label(common.lang['delete'])
        self.button_clear.connect("clicked", self.dialog_clear, self)

        self.vbox = Gtk.VBox()
        self.vbox.set_spacing(5)
        self.vbox.set_border_width(5)

        self.hbox0 = Gtk.HBox()
        self.hbox0.pack_start(self.name_label, True, True, 0)
        self.hbox0.add(self.name_entry)
        self.vbox.add(self.hbox0)

        self.hbox1 = Gtk.HBox()
        self.hbox1.pack_start(self.width_label, True, True, 0)
        self.hbox1.add(self.width_entry)
        self.vbox.add(self.hbox1)

        self.hbox2 = Gtk.HBox()
        self.hbox2.pack_start(self.height_label, True, True, 0)
        self.hbox2.add(self.height_entry)
        self.vbox.add(self.hbox2)

        self.hbox3 = Gtk.HBox()
        self.hbox3.pack_start(self.button_ok, True, True, 0)
        self.hbox3.pack_start(self.button_cancel, True, True, 5)
        self.hbox3.pack_start(self.button_clear, True, True, 0)
        self.vbox.pack_start(self.hbox3, True, True, 0)

        self.add(self.vbox)
        self.button_ok.connect("clicked", self.dialog_ok)
        self.show_all()

    def validate_entries(self, widget):
        self.button_ok.set_sensitive(self.width_entry.get_text() and self.height_entry.get_text())

    def dialog_ok(self, widget, callback_data=None):
        self.properties = [self.name_entry.get_text(), self.width_entry.get_text(), self.height_entry.get_text()]
        if not self.properties[0]:
            self.properties[0] = 'Custom'
        common.settings.custom_display = self.properties
        common.settings.save()
        self.close()

    def dialog_cancel(self, widget, callback_data=None):
        self.close()

    def dialog_clear(self, widget, callback_data=None):
        common.settings.custom_display = None
        common.settings.save()
        self.close()


class NumberEntry(Gtk.Entry):
    """
    https://stackoverflow.com/a/2727085/4040598
    """

    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed)

    def on_changed(self, *args):
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))


def dialog_cancel(widget, window, callback_data=None):
    window.close()


def on_thumb_double_click(button):
    """
    As the function above, but mode 'fill' will always be used
    """
    if common.sway or common.env['wayland']:
        apply_to_all_swaybg(button, 'fill')
    else:
        apply_to_all_feh(button, 'fill')


def apply_to_all_swaybg(item, mode):
    # Firstly we need to set the selected image thumbnail to all previews currently visible
    for box in common.display_boxes_list:
        box.img.set_from_file(common.selected_wallpaper.thumb_file)
        box.wallpaper_path = common.selected_wallpaper.source_path
        box.thumbnail_path = common.selected_wallpaper.thumb_file

    common.apply_button.set_sensitive(True)


def apply_to_all_feh(item, mode):
    # Firstly we need to set the selected image thumbnail to all previews currently visible
    for box in common.display_boxes_list:
        box.img.set_from_file(common.selected_wallpaper.thumb_file)
        box.wallpaper_path = common.selected_wallpaper.source_path
        box.thumbnail_path = common.selected_wallpaper.thumb_file

    common.apply_button.set_sensitive(True)


def print_help():
    print('\nAzote wallpaper manager version {}\n'.format(__version__))
    print('[-h] | [--help]\t\t\t print Help')
    print('[-l] | [--lang] <ln_LN> \t force a Locale (de_DE, en_US, fr_FR, pl_PL)')
    print('[-c] | [--clear]\t\t Clear unused thumbnails')
    print('[-a] | [--clear-all]\t\t clear All thumbnails\n')
    print('[-v] | [--version]\t\t display Version information\n')


def track_changes():
    if common.preview and common.settings.src_path:
        files_dict = dict([(f, None) for f in os.listdir(common.settings.src_path)])
        if not files_dict == common.preview.files_dict:
            common.preview.refresh()
    return common.settings.track_files


class Indicator(object):
    def __init__(self):
        self.ind = AppIndicator3.Indicator.new('azote_status_icon', '',
                                               AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_icon_full('/usr/share/azote/indicator_active.png', 'Tracking off')
        self.ind.set_attention_icon_full('/usr/share/azote/indicator_attention.png', 'Tracking on')

        if common.settings.track_files:
            self.ind.set_status(AppIndicator3.IndicatorStatus.ATTENTION)
            if common.sway or common.env['wayland']:
                self.ind.set_icon_full('/usr/share/azote/indicator_attention.png', 'Tracking on')
        else:
            self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            if common.sway or common.env['wayland']:
                self.ind.set_icon_full('/usr/share/azote/indicator_active.png', 'Tracking off')

        self.ind.set_menu(self.menu())

    def menu(self):
        menu = Gtk.Menu()

        item = Gtk.MenuItem.new_with_label(common.lang['clear_unused_thumbnails'])
        item.connect('activate', self.clear_unused)
        menu.append(item)

        item = Gtk.MenuItem.new_with_label(common.lang['about_azote'])
        item.connect('activate', on_about_button)
        menu.append(item)

        item = Gtk.SeparatorMenuItem()
        menu.append(item)

        item = Gtk.MenuItem.new_with_label(common.lang['exit'])
        item.connect('activate', destroy)
        menu.append(item)

        menu.show_all()
        return menu

    def clear_unused(self, item):
        clear_thumbnails()
        common.preview.refresh()

    def switch_indication(self, item):
        if item.get_active():
            self.ind.set_status(AppIndicator3.IndicatorStatus.ATTENTION)
            if common.sway or common.env['wayland']:
                self.ind.set_icon_full('/usr/share/azote/indicator_attention.png', 'Tracking on')
        else:
            if common.sway or common.env['wayland']:
                self.ind.set_icon_full('/usr/share/azote/indicator_active.png', 'Tracking off')
            self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)


def main():
    lang_from_args = None
    clear_thumbs, clear_all = False, False
    common.color_names = WikiColours()
    for i in range(1, len(sys.argv)):
        if sys.argv[i].upper() == '-H' or sys.argv[i].upper() == '--HELP':
            print_help()
            exit(0)

        if sys.argv[i].upper() == '-L' or sys.argv[i].upper() == '--LANG':
            try:
                lang_from_args = sys.argv[i + 1]
            except:
                pass

        if sys.argv[i].upper() == '-C' or sys.argv[i].upper() == '--CLEAR':
            clear_thumbs = True

        if sys.argv[i].upper() == '-A' or sys.argv[i].upper() == '--CLEAR-ALL':
            clear_thumbs, clear_all = True, True

        if sys.argv[i].upper() == '-V' or sys.argv[i].upper() == '--VERSION':
            print("Azote version {}".format(__version__))
            exit(0)

    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    css = b"""
            button#thumb-btn {
                font-weight: normal;
                font-size: 11px;
            }
            button#folder-btn {
                font-size: 12px;
            }
            button#thumb-btn-selected {
                font-weight: bold;
                font-size: 12px;
                border-top: 1px solid #ccc;
                border-left: 1px solid #ccc;
                border-bottom: 1px solid #333;
                border-right: 1px solid #333;
            }
            button#color-btn {
                font-weight: normal;
            }
            button#color-btn-selected {
                font-weight: bold;
                border-top: 1px solid #ccc;
                border-left: 1px solid #ccc;
                border-bottom: 1px solid #333;
                border-right: 1px solid #333;
            }

            button#display-btn {
                font-weight: normal;
                font-size: 12px;
            }
            button#display-btn-selected {
                font-weight: bold;
                font-size: 12px;
            }
            label#image-label {
                font-size: 12px;
            }
            statusbar#status-bar {
                font-size: 12px;
            }
            label#selected-label {
                border-top: 1px solid #ccc;
                border-left: 1px solid #ccc;
                border-bottom: 1px solid #333;
                border-right: 1px solid #333;
                font-size: 12px;
            }
            label#dotfiles {
                font-size: 13px;
                margin-top: 0px;
                margin-bottom: 0px;
                margin-right: 10px;
            }
            label#dotfiles-header {
                font-size: 14px;
                font-weight: bold;
            }
            label#closest {
                font-size: 12px;
            }
            button#dotfiles-button {
                padding: 1px;
                margin: 0px;
                font-size: 12px;
            }
            textview#preview {
                font-size: 13px;
            }
            """
    provider.load_from_data(css)

    set_env(__version__, lang_from_args=lang_from_args)  # detect displays, check installed modules, set paths and stuff
    if clear_thumbs:
        clear_thumbnails(clear_all)
        exit()

    common.cols = len(common.displays) if len(common.displays) > common.settings.columns else common.settings.columns

    if common.settings.track_files:
        GLib.timeout_add_seconds(common.settings.tracking_interval_seconds, track_changes)
    if common.env['app_indicator']:
        common.indicator = Indicator()

    # We want Azote to take all the possible screen height. Since Gdk.Screen.height is deprecated, we need to measure
    # the current screen height in another way. `w` is a temporary window.
    # If on sway, we've already detected the screen height in tools/check_displays() and stored it in common.screen_h
    if not common.screen_h:  # neither sway, nor Hyprland
        w = TransparentWindow()
        if common.sway or common.env['wm'] == "i3":
            w.fullscreen()  # .maximize() doesn't work as expected on sway
        else:
            w.maximize()
        w.present()

        GLib.timeout_add(common.settings.screen_measurement_delay, check_height_and_start, w)
    else:
        if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
            app = GUI(common.screen_h)  # Hyprland
        else:
            app = GUI(int(common.screen_h * 0.95))  # sway

    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
