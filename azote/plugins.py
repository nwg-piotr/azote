import os
import gi
import common
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from tools import hex_to_rgb, create_pixbuf

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class Alacritty(Gtk.Window):
    def __init__(self):
        super().__init__()

        self.set_title('Alacritty color scheme')
        self.set_role("toolbox")
        self.set_resizable(False)
        self.set_type_hint(Gtk.WindowType.TOPLEVEL)
        self.set_transient_for(common.main_window)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_keep_above(True)

        hbox0 = Gtk.HBox()
        hbox0.set_spacing(5)
        hbox0.set_border_width(15)
        
        f = open(os.path.join(common.config_home, "alacritty/alacritty.yml"), "rb")
        self.data = load(f, Loader=Loader)
        output = dump(self.data['colors'], Dumper=Dumper, default_flow_style=False, sort_keys=False)

        self.frame = Gtk.Frame()
        self.frame.set_label('alacritty.yml')
        self.frame.set_shadow_type(Gtk.ShadowType.IN)

        self.preview = Gtk.Label()
        self.preview.set_property("name", "preview")
        self.preview.set_selectable(True)
        self.preview.set_yalign(0)
        self.preview.set_text(output)

        self.frame.add(self.preview)
        hbox0.pack_start(self.frame, False, False, 0)

        self.vbox = Gtk.VBox()
        self.vbox.set_spacing(5)
        self.vbox.set_border_width(15)

        for key in self.data['colors']:
            label = Gtk.Label()
            label.set_property("name", "dotfiles-header")
            label.set_text(key.upper())
            self.vbox.pack_start(label, True, False, 0)
            for key1 in self.data['colors'][key]:
                hbox = Gtk.HBox()
                label = Gtk.Label()
                label.set_property("name", "dotfiles")
                label.set_text(key1)
                hbox.pack_start(label, True, False, 0)
                label = Gtk.Label()
                label.set_property("name", "dotfiles")
                hex_color = self.data['colors'][key][key1].replace('0x', '#')
                label.set_text(hex_color)
                hbox.pack_start(label, True, False, 0)

                preview_box = ColorPreviewBox(hex_color)
                preview_box.connect('button-press-event', self.on_box_press, label, key, key1)

                hbox.pack_start(preview_box, False, False, 0)

                self.vbox.pack_start(hbox, False, False, 0)

        hbox = Gtk.HBox()
        hbox.set_spacing(5)
        hbox.set_border_width(10)
        refresh_button = Gtk.Button()
        refresh_button.set_always_show_image(True)
        img = Gtk.Image()
        img.set_from_file('images/icon_refresh.svg')
        refresh_button.set_image(img)
        refresh_button.set_tooltip_text(common.lang['reload'])
        #refresh_button.connect_after('clicked', on_refresh_clicked)
        hbox.pack_start(refresh_button, True, False, 0)

        button = Gtk.Button.new_with_label(common.lang['close'])
        button.connect_after('clicked', self.close_window)
        hbox.pack_start(button, False, False, 0)

        self.vbox.add(hbox)

        hbox0.add(self.vbox)
        self.add(hbox0)
        self.show_all()

    def update_preview(self):
        output = dump(self.data['colors'], Dumper=Dumper, default_flow_style=False, sort_keys=False)
        self.preview.set_text(output)
        
    def on_box_press(self, preview_box, event, label, section, key):
        if common.clipboard_text:
            self.data['colors'][section][key] = common.clipboard_text.replace('#', '0x')
            label.set_text(common.clipboard_text)
            preview_box.update()
            self.update_preview()
            
    def close_window(self, button):
        self.close()


class ColorPreviewBox(Gtk.EventBox):
    def __init__(self, hex_color):
        super().__init__()
        pixbuf = create_pixbuf((common.settings.clip_prev_size, common.settings.clip_prev_size // 2),
                               hex_to_rgb(hex_color))
        self.gtk_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.add(self.gtk_image)
        
    def update(self):
        if common.clipboard_text:
            pixbuf = create_pixbuf((common.settings.clip_prev_size, common.settings.clip_prev_size // 2),
                                   hex_to_rgb(common.clipboard_text))
            self.gtk_image.set_from_pixbuf(pixbuf)
