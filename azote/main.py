import os
import sys
import i3ipc
import common
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from tools import set_env, log, hash_name, create_thumbnails, file_allowed

cols = 3


class GUI:
    def __init__(self, displays):
        window = Gtk.Window()
        window.set_title("Hello World")
        window.connect_after('destroy', self.destroy)

        box = Gtk.Box()
        box.set_spacing(5)
        box.set_orientation(Gtk.Orientation.VERTICAL)
        window.add(box)

        preview = Gtk.ScrolledWindow()
        preview.set_border_width(10)
        preview.set_size_request(400, 600)
        preview.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        grid = Gtk.Grid()

        col = 0
        row = 0
        src_pictures = [f for f in os.listdir(common.settings.src_path) if os.path.isfile(os.path.join(common.settings.src_path, f))]
        for file in src_pictures:
            if file_allowed(file):
                btn = self.thumb_btn(common.settings.src_path, file)
                grid.attach(btn, col, row, 1, 1)
                if col < 2:
                    col += 1
                else:
                    col = 0
                    row += 1

        preview.add_with_viewport(grid)

        box.pack_start(preview, False, False, 0)

        label = Gtk.Label()
        label.set_text(displays[0].get('name'))
        box.pack_start(label, False, False, 0)

        self.image = Gtk.Image()
        self.image.set_padding(20, 20)
        box.pack_start(self.image, False, False, 0)

        button = Gtk.Button(os.getenv("HOME"))
        box.pack_start(button, False, False, 0)

        button.connect_after('clicked', self.on_open_clicked)

        window.show_all()

    def destroy(window, self):
        Gtk.main_quit()

    def thumb_btn(self, folder, filename):
        img = Gtk.Image()
        thumb_file = "{}.png".format(os.path.join(common.thumb_dir, hash_name(os.path.join(folder, filename))))
        img.set_from_file(thumb_file)
        btn = Gtk.Button()
        btn.set_image(img)
        btn.set_image_position(2)  # TOP

        if len(filename) > 30:
            filename = '…{}'.format(filename[-28::])
        btn.set_label(filename)

        return btn

    def on_open_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Open Image", button.get_toplevel(), Gtk.FileChooserAction.OPEN);
        dialog.add_button(Gtk.STOCK_CANCEL, 0)
        dialog.add_button(Gtk.STOCK_OK, 1)
        dialog.set_default_response(1)

        filefilter = Gtk.FileFilter()
        filefilter.add_pixbuf_formats()
        dialog.set_filter(filefilter)

        if dialog.run() == 1:
            self.image.set_from_file(dialog.get_filename())

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
        return displays
    except Exception as e:
        log(e, common.ERROR)
        return None


def main():
    set_env()   # set paths and stuff
    create_thumbnails(common.settings.src_path)
    displays = check_displays()
    app = GUI(displays)
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
