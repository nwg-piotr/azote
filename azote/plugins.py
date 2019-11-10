import os
import gi
import common
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from tools import hex_to_rgb, create_pixbuf


class Alacritty(Gtk.Window):
    def __init__(self):
        super().__init__()

        from yaml import load, dump
        try:
            from yaml import CLoader as Loader, CDumper as Dumper
        except ImportError:
            from yaml import Loader, Dumper

        #self.set_default_size(common.settings.thumb_width * 2 + 160, 1000)
        self.set_title('Alacritty color scheme')
        self.set_role("toolbox")
        self.set_resizable(False)
        self.set_type_hint(Gtk.WindowType.TOPLEVEL)
        #self.set_modal(True)
        self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_keep_above(True)

        self.vbox = Gtk.VBox()
        self.vbox.set_spacing(5)
        self.vbox.set_border_width(15)

        f = open(os.path.join(common.config_home, "alacritty/alacritty.yml"), "rb")
        data = load(f, Loader=Loader)
        output = dump(data['colors'], Dumper=Dumper)
        for key in data['colors']:
            print(key)
            label = Gtk.Label()
            label.set_property("name", "dotfiles-header")
            label.set_text(key.upper())
            self.vbox.pack_start(label, False, False, 0)
            for key1 in data['colors'][key]:
                hbox = Gtk.HBox()
                label = Gtk.Label()
                label.set_property("name", "dotfiles")
                label.set_text(key1)
                hbox.pack_start(label, True, False, 0)
                label = Gtk.Label()
                label.set_property("name", "dotfiles")
                hex_color = data['colors'][key][key1].replace('0x', '#')
                label.set_text(hex_color)
                hbox.pack_start(label, True, False, 0)

                pixbuf = create_pixbuf((common.settings.clip_prev_size, common.settings.clip_prev_size // 2), hex_to_rgb(hex_color))
                gtk_image = Gtk.Image.new_from_pixbuf(pixbuf)

                """button = Gtk.Button()
                button.set_property("name", "dotfiles-button")
                button.set_always_show_image(True)
                button.set_image(gtk_image)
                button.set_image_position(1)  # TOP
                button.set_tooltip_text(common.lang['copy'])"""
                #button.connect_after('clicked', self.to_clipboard)
                hbox.pack_start(gtk_image, False, False, 0)

                self.vbox.pack_start(hbox, False, False, 0)
                print(key1, data['colors'][key][key1])

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)

        self.preview = Gtk.TextView()
        self.preview.set_property("name", "preview")
        self.preview.set_editable(False)
        self.textbuffer = self.preview.get_buffer()
        self.textbuffer.set_text(output)

        self.scrolled_window.add(self.preview)

        #self.vbox.pack_start(self.scrolled_window, True, True, 0)



        self.add(self.vbox)

        common.dotfile_window_open = True
        self.show_all()

    def close_window(self, widget):
        common.dotfile_window_open = False
        self.close()
