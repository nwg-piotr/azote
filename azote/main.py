import os
import sys
import i3ipc
import common
import gi
from PIL import Image
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from tools import set_env, log, hash_name, create_thumbnails, file_allowed

cols = 3


class Preview(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

        self.set_border_width(10)
        self.set_size_request(400, 600)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)

        common.buttons_list = []
        self.grid = Gtk.Grid()

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
                if col < 2:
                    col += 1
                else:
                    col = 0
                    row += 1

        self.add_with_viewport(self.grid)

    def refresh(self):
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
                if col < 2:
                    col += 1
                else:
                    col = 0
                    row += 1
                btn.show()


class ThumbButton(Gtk.Button):
    def __init__(self, folder, filename):
        super().__init__()

        self.filename = filename
        self.source_path = os.path.join(folder, filename)

        img = Gtk.Image()
        self.thumb_file = "{}.png".format(os.path.join(common.thumb_dir, hash_name(self.source_path)))
        img.set_from_file(self.thumb_file)

        self.set_image(img)
        self.set_image_position(2)  # TOP

        if len(filename) > 30:
            filename = '…{}'.format(filename[-28::])
        self.set_label(filename)
        self.selected = False

        color = Gdk.color_parse('#fefefe')
        rgba = Gdk.RGBA.from_color(color)
        self.override_background_color(0, rgba)

        self.connect('clicked', self.select)

    def select(self, button):
        self.selected = True
        deselect_all()

        color = Gdk.color_parse('#66ccff')
        rgba = Gdk.RGBA.from_color(color)
        button.override_background_color(0, rgba)

        with Image.open(self.source_path) as img:
            common.selected_picture_label.set_text("{}    ({} x {})".format(self.filename, img.size[0], img.size[1]))

    def deselect(self, button):
        self.selected = False

        color = Gdk.color_parse('#fefefe')
        rgba = Gdk.RGBA.from_color(color)
        button.override_background_color(0, rgba)


def deselect_all():
    for btn in common.buttons_list:
        btn.deselect(btn)


class GUI:
    def __init__(self, displays):

        window = Gtk.Window()
        window.set_title("Hello World")
        window.connect_after('destroy', self.destroy)

        box = Gtk.Box()
        box.set_spacing(15)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        window.add(box)

        common.preview = Preview()

        box.pack_start(common.preview, False, False, 0)

        common.selected_picture_label = Gtk.Label()
        common.selected_picture_label.set_text('Select a picture')

        box.pack_start(common.selected_picture_label, False, False, 0)

        folder_button = Gtk.Button(common.settings.src_path)
        box.pack_start(folder_button, False, False, 0)

        folder_button.connect_after('clicked', self.on_folder_clicked)

        output_label = Gtk.Label()
        output_label.set_text(displays[0].get('name'))
        box.pack_start(output_label, False, False, 0)

        window.show_all()

    def destroy(window, self):
        Gtk.main_quit()

    def on_folder_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Open Image", button.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER);
        dialog.add_button(Gtk.STOCK_CANCEL, 0)
        dialog.add_button(Gtk.STOCK_OK, 1)
        dialog.set_default_response(1)
        dialog.set_default_size(300, 300)

        response = dialog.run()
        if response == 1:
            common.settings.src_path = dialog.get_filename()
            common.settings.save()
            common.preview.refresh()
            button.set_label(common.settings.src_path)

        dialog.destroy()


def check_displays():
    displays = []
    try:
        i3 = i3ipc.Connection()
        common.outputs = i3.get_outputs()
        for output in common.outputs:
            display = {'name': output.name,
                       'x': output.rect.x,
                       'y': output.rect.y,
                       'width': output.rect.width,
                       'height': output.rect.height}
            displays.append(display)
            log("Output: {}".format(display), common.INFO)
        return displays
    except Exception as e:
        log(e, common.ERROR)
        return None


def main():
    set_env()   # set paths and stuff
    displays = check_displays()
    app = GUI(displays)
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
