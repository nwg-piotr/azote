#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
Wallpaper manager for Sway, i3 and some other WMs, as a frontend to swaybg and feh

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/azote
License: GPL3

Dependencies:
python, python-setuptools, python-gobject, python-cairo, i3ipc-python, python-pillow, wmctrl, feh, xorg-xrandr
"""
import os
import sys
import subprocess
import stat
import common
import gi
import pkg_resources
from PIL import Image

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from tools import set_env, hash_name, create_thumbnails, file_allowed, update_status_bar, flip_selected_wallpaper, \
    copy_backgrounds, rgba_to_hex, split_selected_wallpaper


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

        col = 0
        row = 0
        src_pictures = [f for f in os.listdir(common.settings.src_path) if
                        os.path.isfile(os.path.join(common.settings.src_path, f))]

        for file in src_pictures:
            if file_allowed(file):
                btn = ThumbButton(common.settings.src_path, file)
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

        col = 0
        row = 0
        src_pictures = [f for f in os.listdir(common.settings.src_path) if
                        os.path.isfile(os.path.join(common.settings.src_path, f))]

        for file in src_pictures:
            if file_allowed(file):
                btn = ThumbButton(common.settings.src_path, file)
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

        self.filename = filename
        self.source_path = os.path.join(folder, filename)

        img = Gtk.Image()
        self.thumb_file = "{}.png".format(os.path.join(common.thumb_dir, hash_name(self.source_path)))
        img.set_from_file(self.thumb_file)

        self.set_image(img)
        self.set_image_position(2)  # TOP
        self.set_tooltip_text(common.lang['select_this_picture'])

        if len(filename) > 30:
            filename = '…{}'.format(filename[-28::])
        self.set_label(filename)
        self.selected = False

        self.connect('clicked', self.select)

    def select(self, button):
        if common.split_button:
            common.split_button.set_sensitive(True)
        self.selected = True
        common.selected_wallpaper = self
        deselect_all()
        button.set_property("name", "thumb-btn-selected")

        with Image.open(self.source_path) as img:
            common.selected_picture_label.set_text("{}    ({} x {})".format(self.filename, img.size[0], img.size[1]))

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

        self.img = Gtk.Image()
        self.img.set_from_file("images/empty.png")

        self.select_button = Gtk.Button()
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
            modes = ["stretch", "fit", "fill", "center", "tile"]  # modes available in swaybg
        else:
            modes = ["tile", "center", "scale", "seamless"]  # modes available in feh

        for mode in modes:
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

        self.flip_button = Gtk.Button.new_with_label(common.lang['flip_image'])
        self.flip_button.set_sensitive(False)
        self.flip_button.connect('clicked', self.on_flip_button)
        self.flip_button.set_tooltip_text(common.lang['flip_wallpaper_horizontally'])
        if common.sway:
            options_box.add(self.flip_button)
        else:
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


class GUI:
    def __init__(self):

        window = Gtk.Window()

        window.set_title("Azote")
        logo = GdkPixbuf.Pixbuf.new_from_file('images/azote.svg')
        window.set_default_icon(logo)
        window.set_role("azote")

        window.connect_after('destroy', self.destroy)

        main_box = Gtk.Box()
        main_box.set_spacing(5)
        main_box.set_border_width(10)
        main_box.set_orientation(Gtk.Orientation.VERTICAL)

        # This contains a Gtk.ScrolledWindow with Gtk.Grid() inside, filled with ThumbButton(Gtk.Button) instances
        common.preview = Preview()
        window.connect('configure-event', on_configure_event)

        main_box.pack_start(common.preview, False, False, 0)

        # Label to display details of currently selected picture
        common.selected_picture_label = Gtk.Label()
        common.selected_picture_label.set_text(common.lang['select_a_picture'])

        main_box.pack_start(common.selected_picture_label, False, False, 0)

        # Let's pack 2 folder buttons horizontally
        folder_buttons_box = Gtk.Box()
        folder_buttons_box.set_spacing(5)
        folder_buttons_box.set_border_width(10)
        folder_buttons_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # Button to refresh currently selected folder thumbnails
        refresh_button = Gtk.Button()
        img = Gtk.Image()
        img.set_from_file('images/icon_refresh.svg')
        refresh_button.set_image(img)
        refresh_button.set_tooltip_text(common.lang['refresh_folder_preview'])
        folder_buttons_box.add(refresh_button)

        refresh_button.connect_after('clicked', self.on_refresh_clicked)

        # Button to set the wallpapers folder
        folder_button = Gtk.Button.new_with_label(common.settings.src_path)
        img = Gtk.Image()
        img.set_from_file('images/icon_open.svg')
        folder_button.set_image(img)
        folder_button.set_tooltip_text(common.lang['open_another_folder'])
        folder_buttons_box.pack_start(folder_button, True, True, 0)

        folder_button.connect_after('clicked', self.on_folder_clicked)

        main_box.pack_start(folder_buttons_box, False, True, 0)

        # We need a horizontal container to display outputs in columns
        displays_box = Gtk.Box()
        displays_box.set_spacing(15)
        displays_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        window.add(main_box)

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
        bottom_box.set_border_width(10)
        bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # Button to call About dialog
        about_button = Gtk.Button()
        img = Gtk.Image()
        img.set_from_file('images/icon_about.svg')
        about_button.set_image(img)
        about_button.set_tooltip_text(common.lang['about_azote'])
        about_button.connect('clicked', self.on_about_button)
        bottom_box.add(about_button)

        # Button to split wallpaper between displays
        if len(common.displays) > 1:
            common.split_button = Gtk.Button.new_with_label(common.lang['split_selection'])
            bottom_box.pack_start(common.split_button, True, True, 0)
            common.split_button.set_sensitive(False)
            common.split_button.set_tooltip_text(common.lang['split_selection_between_displays'])
            common.split_button.connect('clicked', self.on_split_button)

        # Button to apply settings
        common.apply_button = Gtk.Button.new_with_label(common.lang['apply'])
        common.apply_button.connect('clicked', self.on_apply_button)
        common.apply_button.set_sensitive(False)
        common.apply_button.set_tooltip_text(common.lang['apply_settings'])
        bottom_box.pack_start(common.apply_button, True, True, 0)

        main_box.add(bottom_box)

        hseparator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.add(hseparator)

        common.status_bar = Gtk.Statusbar()
        common.status_bar.set_property("name", "status-bar")
        common.status_bar.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(common.status_bar, True, False, 0)
        update_status_bar()

        window.show_all()

    def destroy(window, self):
        Gtk.main_quit()

    def on_folder_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Open folder", button.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button(Gtk.STOCK_CANCEL, 0)
        dialog.add_button(Gtk.STOCK_OK, 1)
        dialog.set_default_response(1)
        dialog.set_default_size(500, 600)

        response = dialog.run()
        if response == 1:
            common.settings.src_path = dialog.get_filename()
            common.settings.save()
            common.preview.refresh()
            button.set_label(common.settings.src_path)

        dialog.destroy()

    def on_refresh_clicked(self, button):
        common.preview.refresh()

    def on_apply_button(self, button):
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
                        "swaybg -o {} -i {} -m {} &".format(box.display_name, box.wallpaper_path, box.mode))

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
                command += " {}".format(box.wallpaper_path)
            print(command)
            subprocess.call(command, shell=True)

    def on_split_button(self, button):
        if common.selected_wallpaper:
            common.apply_button.set_sensitive(True)
            # self.unset_boxes()
            paths = split_selected_wallpaper(len(common.displays))
            for i in range(len(paths)):
                box = common.display_boxes_list[i]
                box.wallpaper_path = paths[i][0]
                box.img.set_from_file(paths[i][1])

        if common.display_boxes_list:
            for box in common.display_boxes_list:
                box.clear_color_selection()

    def on_about_button(self, button):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name('Azote')

        try:
            version = pkg_resources.require(common.app_name)[0].version
            dialog.set_version("v{}".format(version))
        except Exception as e:
            print("Couldn't check version: {}".format(e))
            pass

        logo = GdkPixbuf.Pixbuf.new_from_file_at_size('images/azote.svg', 96, 96)

        dialog.set_logo(logo)
        dialog.set_copyright('(c) 2019 Piotr Miller')
        dialog.set_website('https://github.com/nwg-piotr/azote')
        dialog.set_comments(common.lang['app_desc'])
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.set_authors(['Piotr Miller (nwg)'])
        dialog.set_artists(['edskeye'])

        dialog.show()

        dialog.run()
        dialog.destroy()
        return False


def on_configure_event(window, e):
    cols = e.width // 256
    if cols != common.cols:
        common.preview.hide()
        if cols != common.cols:
            common.cols = cols
            common.preview.refresh(False)

        common.preview.show()


def main():
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    css = b"""
            button#thumb-btn {
                background-color: #fefefe;
                font-weight: normal;
                font-size: 11px;
            }
            button#thumb-btn-selected {
                background-color: #66ccff;
                font-weight: bold;
                font-size: 12px;
            }
            button#display-btn {
                font-weight: normal;
                font-size: 12px;
            }
            button#display-btn-selected {
                font-weight: bold;
                font-size: 12px;
            }
            statusbar#status-bar {
                font-size: 12px;
            }
            """
    provider.load_from_data(css)

    lang = None
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == 'lang':
            try:
                lang = sys.argv[i + 1]
            except:
                pass

    set_env(lang)  # detect displays, check installed modules, set paths and stuff
    common.cols = len(common.displays) if len(common.displays) > 3 else 3
    app = GUI()
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
