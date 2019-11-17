#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
Wallpaper manager for Sway, i3 and some other WMs, as a frontend to swaybg and feh

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/azote
License: GPL3

depends=('python' 'python-setuptools' 'python-gobject' 'python-pillow' 'gtk3' 'feh' 'xorg-xrandr' 'python-pyaml')
optdepends=('python-send2trash: trash support'
            'grim: screen color picker on Sway'
            'slurp: screen color picker on Sway'
            'imagemagick: screen color picker on both Sway and X11'
            'maim: screen color picker on X11')
"""
import os
import sys
import subprocess
import stat
import common
import gi
import pkg_resources
from PIL import Image

# send2trash module may or may not be available
try:
    from send2trash import send2trash

    common.env['send2trash'] = True
except Exception as e:
    common.env['send2trash'] = False
    print('send2trash module not found', e)

from colorthief import ColorThief

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository.GdkPixbuf import InterpType
from tools import set_env, hash_name, create_thumbnails, file_allowed, update_status_bar, flip_selected_wallpaper, \
    copy_backgrounds, create_pixbuf, split_selected_wallpaper, scale_and_crop, clear_thumbnails
from color_tools import rgba_to_hex, hex_to_rgb, rgb_to_hex, rgb_to_rgba
from plugins import Alacritty, Xresources
from color_tools import WikiColours


def get_files():
    try:
        file_names = [f for f in os.listdir(common.settings.src_path)
                      if os.path.isfile(os.path.join(common.settings.src_path, f))]
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

        common.buttons_list = []
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(25)
        self.grid.set_row_spacing(15)

        create_thumbnails(common.settings.src_path)

        col, row = 0, 0
        src_pictures = get_files()

        for file in src_pictures:
            if file_allowed(file):
                btn = ThumbButton(common.settings.src_path, file)
                btn.column = col
                common.buttons_list.append(btn)
                self.grid.attach(btn, col, row, 1, 1)
                if col < common.cols - 1:
                    col += 1
                else:
                    col = 0
                    row += 1

        self.add(self.grid)

    def refresh(self, create_thumbs=True):
        if create_thumbs:
            create_thumbnails(common.settings.src_path)

        for button in common.buttons_list:
            self.grid.remove(button)
            button.destroy()

        col, row = 0, 0
        src_pictures = get_files()

        for file in src_pictures:
            if file_allowed(file):
                btn = ThumbButton(common.settings.src_path, file)
                btn.column = col
                common.buttons_list.append(btn)
                self.grid.attach(btn, col, row, 1, 1)
                if col < common.cols - 1:
                    col += 1
                else:
                    col = 0
                    row += 1
                btn.show()

        update_status_bar()


class ThumbButton(Gtk.Button):
    def __init__(self, folder, filename):
        super().__init__()

        self.set_property("name", "thumb-btn")
        self.set_always_show_image(True)

        self.folder = folder
        self.filename = filename
        self.source_path = os.path.join(folder, filename)

        self.img = Gtk.Image()
        self.thumb_file = "{}.png".format(os.path.join(common.thumb_dir, hash_name(self.source_path)))
        self.img.set_from_file(self.thumb_file)

        self.set_image(self.img)
        self.set_image_position(2)  # TOP
        self.set_tooltip_text(
            common.lang['thumbnail_tooltip'])

        # Workaround: column is a helper value to identify thumbnails placed in column 0. 
        # They need different context menu gravity in Sway
        self.column = 0

        if len(filename) > 30:
            filename = '…{}'.format(filename[-28::])
        self.set_label(filename)
        self.selected = False

        # self.connect('clicked', self.on_button_press)
        self.connect('button-press-event', self.on_button_press)

    def on_button_press(self, button, event):
        if common.split_button:
            common.split_button.set_sensitive(True)

        common.apply_to_all_button.set_sensitive(True)

        self.selected = True
        common.selected_wallpaper = self
        deselect_all()
        button.set_property("name", "thumb-btn-selected")

        with Image.open(self.source_path) as img:
            filename = self.filename
            if len(filename) > 30:
                filename = '…{}'.format(filename[-28::])
            common.selected_picture_label.set_text("{} ({} x {})".format(filename, img.size[0], img.size[1]))
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            on_thumb_double_click(button)
        if event.button == 3:
            show_image_menu(button)

    def deselect(self, button):
        self.selected = False
        button.set_property("name", "thumb-btn")


def deselect_all():
    for btn in common.buttons_list:
        btn.deselect(btn)


class DisplayBox(Gtk.Box):
    """
    The box contains elements to preview certain displays and assign wallpapers to them
    """

    def __init__(self, name, width, height):
        super().__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)

        # Values to assigned to corresponding display when apply button pressed
        self.display_name = name
        self.wallpaper_path = None
        self.mode = 'fill' if common.sway else 'scale'
        self.color = None

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

        if common.sway:
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

        self.mode_combo = Gtk.ComboBox.new_with_model(mode_selector)
        self.mode_combo.set_active(2)
        self.mode_combo.connect("changed", self.on_mode_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.mode_combo.pack_start(renderer_text, True)
        self.mode_combo.add_attribute(renderer_text, "text", 0)
        self.mode_combo.set_tooltip_text(common.lang['display_mode'])
        options_box.add(self.mode_combo)

        if common.sway:
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

    def clear_color_selection(self):
        # If not on sway / swaybg, we have no color_button in UI
        if common.sway:
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
        if not common.sway and common.display_boxes_list:
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

    if common.sway:
        # Prepare, save and execute the shell script for swaybg. It'll be placed in ~/.azotebg for further use.
        batch_content = ['#!/usr/bin/env bash', 'pkill swaybg']
        for box in common.display_boxes_list:
            if box.color:
                # if a color chosen, the wallpaper won't appear
                batch_content.append("swaybg -o {} -c{} &".format(box.display_name, box.color))
            elif box.wallpaper_path:
                batch_content.append(
                    "swaybg -o {} -i '{}' -m {} &".format(box.display_name, box.wallpaper_path, box.mode))

        # save to ~/.azotebg
        with open(common.cmd_file, 'w') as f:
            for item in batch_content:
                f.write("%s\n" % item)
        # make the file executable
        st = os.stat(common.cmd_file)
        os.chmod(common.cmd_file, st.st_mode | stat.S_IEXEC)

        subprocess.call(common.cmd_file, shell=True)
    else:
        # Prepare and execute the feh command. It's being saved automagically to ~/.fehbg
        mode = common.display_boxes_list[0].mode  # They are all the same, just check the 1st one
        command = "feh --bg-{}".format(mode)
        for box in common.display_boxes_list:
            command += " '{}'".format(box.wallpaper_path)
        subprocess.call(command, shell=True)


def on_split_button(button):
    if common.selected_wallpaper:
        common.apply_button.set_sensitive(True)
        paths = split_selected_wallpaper(len(common.displays))
        for i in range(len(paths)):
            box = common.display_boxes_list[i]
            box.wallpaper_path = paths[i][0]
            box.img.set_from_file(paths[i][1])

    if common.display_boxes_list:
        for box in common.display_boxes_list:
            box.clear_color_selection()


def open_with(item, opener):
    # if feh selected as the opener, let's start it with options as below
    if opener == 'feh':
        command = 'feh --start-at {} --scale-down --no-fehbg -d --output-dir {}'.format(
            common.selected_wallpaper.source_path, common.selected_wallpaper.folder)
    # elif could specify options for other certain programs here
    else:
        command = '{} {}'.format(opener, common.selected_wallpaper.source_path)
    subprocess.Popen(command, shell=True)


def clear_wallpaper_selection():
    common.selected_wallpaper = None
    common.selected_picture_label.set_text(common.lang['no_picture_selected'])
    if common.split_button:
        common.split_button.set_sensitive(False)
    common.apply_button.set_sensitive(False)


def on_about_button(button):
    dialog = Gtk.AboutDialog()
    dialog.set_program_name('Azote')

    try:
        version = pkg_resources.require(common.app_name)[0].version
        dialog.set_version("v{}".format(version))
    except Exception as e:
        print("Couldn't check version: {}".format(e))
        pass

    logo = GdkPixbuf.Pixbuf.new_from_file_at_size('images/azote.svg', 96, 96)

    dialog.set_keep_above(True)
    dialog.set_logo(logo)
    dialog.set_copyright('(c) 2019 Piotr Miller')
    dialog.set_website('https://github.com/nwg-piotr/azote')
    dialog.set_comments(common.lang['app_desc'])
    dialog.set_license_type(Gtk.License.GPL_3_0)
    dialog.set_authors(['Piotr Miller (nwg)', 'Head-on-a-Stick', 'Libraries and dependencies:',
                        '- colorthief python module (c) 2015 Shipeng Feng',
                        '- python-pillow (c) 1995-2011, Fredrik Lundh, 2010-2019 Alex Clark and Contributors',
                        '- pygobject (c) 2005-2019 The GNOME Project',
                        '- GTK+ (c) 2007-2019 The GTK Team',
                        '- feh (c) 1999,2000 Tom Gilbert, 2010-2018 Daniel Friesel',
                        '- swaybg (c) 2016-2019 Drew DeVault',
                        '- send2trash python module (c) 2017 Virgil Dupras',
                        '- grim, slurp (c) 2018 emersion',
                        '- maim, slop (c) 2014 Dalton Nell and Contributors'])
    dialog.set_translator_credits('xsme (de_DE), HumanG33k (fr_FR)')
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


def show_image_menu(widget):
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
            # Let's cheat here
            subitem = Gtk.MenuItem.new_with_label('4 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 4)
            submenu.append(subitem)

            subitem = Gtk.MenuItem.new_with_label('8 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 9)
            submenu.append(subitem)

            subitem = Gtk.MenuItem.new_with_label('12 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 13)
            submenu.append(subitem)

            subitem = Gtk.MenuItem.new_with_label('16 {}'.format(common.lang['colors']))
            subitem.connect('activate', generate_palette, common.selected_wallpaper.thumb_file,
                            common.selected_wallpaper.filename,
                            common.selected_wallpaper.source_path, 17)
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
            display = common.displays[0]
            width, height = display['width'] * 2, display['height']
            subitem = Gtk.MenuItem.new_with_label(
                '{} x {} ({} {})'.format(width, height, display['name'], common.lang['dual_width']))
            subitem.connect('activate', scale_and_crop, common.selected_wallpaper.source_path, width, height)
            submenu.append(subitem)

            # Scale and crop to double height of the primary display
            display = common.displays[0]
            width, height = display['width'], display['height'] * 2
            subitem = Gtk.MenuItem.new_with_label(
                '{} x {} ({} {})'.format(width, height, display['name'], common.lang['dual_height']))
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

            if widget.column:
                if widget.column == 0:
                    menu.popup_at_widget(widget, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_WEST, None)
                else:
                    menu.popup_at_widget(widget, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_EAST, None)
            else:
                menu.popup_at_widget(widget, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH, None)
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


class GUI:
    def __init__(self):

        window = Gtk.Window()
        screen = window.get_screen()
        h = screen.height()

        window.set_default_size(common.settings.thumb_width * common.settings.columns + 160, h * 0.95)
        common.main_window = window

        window.set_title("Azote wallpaper manager")
        logo = GdkPixbuf.Pixbuf.new_from_file('images/icon.svg')
        window.set_default_icon(logo)
        window.set_role("azote")

        window.connect_after('destroy', destroy)

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
        window.connect('configure-event', on_configure_event)

        main_box.pack_start(common.preview, False, False, 0)

        # We need a horizontal container to display outputs in columns
        displays_box = Gtk.Box()
        displays_box.set_spacing(15)
        displays_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # Buttons below represent displays preview
        common.display_boxes_list = []
        for display in common.displays:
            # Label format: name (width x height)
            display_box = DisplayBox(display.get('name'), display.get('width'), display.get('height'))
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
        if common.sway:
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
        dotfiles_button.set_tooltip_text(common.lang['dotfiles'])
        dotfiles_button.connect('clicked', on_dotfiles_button)
        status_box.add(dotfiles_button)

        common.status_bar = Gtk.Statusbar()
        common.status_bar.set_property("name", "status-bar")
        common.status_bar.set_halign(Gtk.Align.CENTER)
        status_box.pack_start(common.status_bar, True, True, 0)
        update_status_bar()

        main_box.add(status_box)

        window.show_all()

        common.progress_bar.hide()


def on_configure_event(window, e):
    cols = e.width // (common.settings.thumb_width + 40)
    if cols != common.cols:
        common.preview.hide()
        if cols != common.cols:
            common.cols = cols
            common.preview.refresh(create_thumbs=False)
        common.preview.show()


def on_apply_to_all_button(button):
    """
    This will create a single command to set the same wallpaper to all displays, CONNECTED at the time OR NOT.
    Menu for modes needs to differ for swaybg and feh.
    """
    menu = Gtk.Menu()
    if common.sway:
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
    if common.sway:
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
    if common.sway:
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
        if common.xresources:
            menu = Gtk.Menu()
            item = Gtk.MenuItem.new_with_label(common.xresources)
            item.connect('activate', open_dotfile, 'xresources')
            menu.append(item)

        if common.alacritty_config:
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
        self.set_type_hint(Gtk.WindowType.TOPLEVEL)
        # self.set_modal(True)
        self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_keep_above(True)
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

            self.hbox.pack_start(button, False, False, 0)

            if (i + 1) % 4 == 0:
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
        common.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        if common.settings.copy_as == 'r, g, b':
            t = hex_to_rgb(widget.get_label())
            content = '{}, {}, {}'.format(t[0], t[1], t[2])
        else:
            content = widget.get_label()

        common.clipboard.set_text(content, -1)
        common.clipboard_text = widget.get_label()
        # print(common.clipboard_text)

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
        self.set_type_hint(Gtk.WindowType.TOPLEVEL)
        self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.MOUSE)
        self.set_keep_above(True)

        try:
            self.copy_as = common.settings.copy_as
        except AttributeError:
            self.copy_as = '#rgb'

        self.vbox = Gtk.VBox()
        self.vbox.set_spacing(5)
        self.vbox.set_border_width(5)

        self.image = Gtk.Image()
        pixbuf = create_pixbuf((common.settings.color_icon_w, common.settings.color_icon_h), color)
        self.image.set_from_pixbuf(pixbuf)
        self.vbox.add(self.image)

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

        pixbuf = create_pixbuf((common.settings.color_icon_w, common.settings.color_icon_h), color)
        self.image.set_from_pixbuf(pixbuf)

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
        self.set_role("pop-up")
        self.set_type_hint(Gtk.WindowType.TOPLEVEL)
        self.set_modal(True)
        self.set_decorated(False)
        self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
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
    if common.sway:
        apply_to_all_swaybg(button, 'fill')
    else:
        apply_to_all_feh(button, 'fill')


def apply_to_all_swaybg(item, mode):
    # Firstly we need to set the selected image thumbnail to all previews currently visible
    for box in common.display_boxes_list:
        box.img.set_from_file(common.selected_wallpaper.thumb_file)
        box.wallpaper_path = common.selected_wallpaper.source_path

    common.apply_button.set_sensitive(False)

    # Prepare, save and execute the shell script for swaybg. It'll be placed in ~/.azotebg for further use.
    batch_content = ['#!/usr/bin/env bash', 'pkill swaybg',
                     "swaybg -o* -i '{}' -m {} &".format(common.selected_wallpaper.source_path, mode)]

    # save to ~/.azotebg
    with open(common.cmd_file, 'w') as f:
        for item in batch_content:
            f.write("%s\n" % item)
    # make the file executable
    st = os.stat(common.cmd_file)
    os.chmod(common.cmd_file, st.st_mode | stat.S_IEXEC)

    subprocess.call(common.cmd_file, shell=True)


def apply_to_all_feh(item, mode):
    # Firstly we need to set the selected image thumbnail to all previews currently visible
    for box in common.display_boxes_list:
        box.img.set_from_file(common.selected_wallpaper.thumb_file)
        box.wallpaper_path = common.selected_wallpaper.source_path

    common.apply_button.set_sensitive(False)

    # Prepare and execute the feh command. It's being saved automagically to ~/.fehbg
    command = "feh --bg-{}".format(mode)
    command += " '{}'".format(common.selected_wallpaper.source_path)

    subprocess.call(command, shell=True)


def print_help():
    try:
        version = pkg_resources.require(common.app_name)[0].version
    except Exception as e:
        version = 'unknown ({})'.format(e)
    print('\nAzote wallpaper manager version {}\n'.format(version))
    print('[-h] | [--help]\t\t\t Print help')
    print('[-l] | [--lang] <ln_LN> \t Force a locale (de_DE, en_EN, fr_FR, pl_PL)')
    print('[-c] | [--clear]\t\t Clear unused thumbnails')
    print('[-a] | [--clear-all]\t\t Clear all thumbnails\n')


def main():
    lang = None
    clear_thumbs, clear_all = False, False
    common.color_names = WikiColours()
    for i in range(1, len(sys.argv)):
        if sys.argv[i].upper() == '-H' or sys.argv[i].upper() == '--HELP':
            print_help()
            exit(0)

        if sys.argv[i].upper() == '-L' or sys.argv[i].upper() == '--LANG':
            try:
                lang = sys.argv[i + 1]
            except:
                pass

        if sys.argv[i].upper() == '-C' or sys.argv[i].upper() == '--CLEAR':
            clear_thumbs = True

        if sys.argv[i].upper() == '-A' or sys.argv[i].upper() == '--CLEAR-ALL':
            clear_thumbs, clear_all = True, True

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

    set_env(lang)  # detect displays, check installed modules, set paths and stuff
    if clear_thumbs:
        clear_thumbnails(clear_all)
        exit()

    common.cols = len(common.displays) if len(common.displays) > common.settings.columns else common.settings.columns
    app = GUI()
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
