import os
import sys
import i3ipc
import common
import gi
from PIL import Image

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from tools import set_env, log, hash_name, create_thumbnails, file_allowed, update_status_bar, flip_selected_wallpaper


class Preview(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

        self.set_border_width(10)
        self.set_size_request(0, 500)
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

        self.add_with_viewport(self.grid)

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

        if len(filename) > 30:
            filename = '…{}'.format(filename[-28::])
        self.set_label(filename)
        self.selected = False

        self.connect('clicked', self.select)

    def select(self, button):
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
    def __init__(self, display_name):
        super().__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.wallpaper_path = None  # stores the value which will be assigned to corresponding display

        self.img = Gtk.Image()
        self.img.set_from_file("images/empty.png")

        self.select_button = Gtk.Button()
        self.select_button.set_label(display_name)                 # label on top: name (with x height)
        self.select_button.set_image(self.img)                     # preview of selected wallpaper
        self.select_button.set_image_position(3)                   # label on top, image below
        self.select_button.set_property("name", "display-btn")     # to assign css style

        self.pack_start(self.select_button, False, False, 10)

        self.select_button.connect_after('clicked', self.on_select_button)

        # Combo box to choose a mode to use for the image
        mode_selector = Gtk.ListStore(str)
        modes = ["stretch", "fit", "fill", "center", "tile"]
        for mode in modes:
            mode_selector.append([mode])

        # Let's display the mode combo and the color button side-by-side in a vertical box
        options_box = Gtk.Box()
        options_box.set_spacing(15)
        options_box.set_border_width(0)
        options_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.pack_start(options_box, True, False, 0)

        mode_combo = Gtk.ComboBox.new_with_model(mode_selector)
        mode_combo.set_active(2)
        mode_combo.connect("changed", self.on_country_combo_changed)
        renderer_text = Gtk.CellRendererText()
        mode_combo.pack_start(renderer_text, True)
        mode_combo.add_attribute(renderer_text, "text", 0)
        options_box.add(mode_combo)

        # Color button
        color_button = Gtk.ColorButton()
        color = Gdk.RGBA()
        color.red = 0.0
        color.green = 0.0
        color.blue = 0.0
        color.alpha = 1.0
        color_button.set_rgba(color)
        color_button.connect("color-set", self.on_color_chosen, color_button)
        options_box.add(color_button)

        self.flip_button = Gtk.Button("Flip image")
        self.flip_button.set_sensitive(False)
        self.flip_button.connect('clicked', self.on_flip_button)
        options_box.add(self.flip_button)

    def on_select_button(self, button):
        if common.selected_wallpaper:
            self.img.set_from_file(common.selected_wallpaper.thumb_file)
            self.wallpaper_path = common.selected_wallpaper.source_path
            button.set_property("name", "display-btn-selected")
            self.flip_button.set_sensitive(True)

    def on_country_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            country = model[tree_iter][0]
            print("Selected: country=%s" % country)

    def on_color_chosen(self, user_data, button):
        print("You chose the color: " + button.get_rgba().to_string())

    def on_flip_button(self, button):
        # convert images and get (thumbnail path, flipped image path)
        images = flip_selected_wallpaper()
        self.img.set_from_file(images[0])
        self.wallpaper_path = images[1]
        self.flip_button.set_sensitive(False)


class GUI:
    def __init__(self, displays):

        window = Gtk.Window()

        window.set_title("Azote")
        window.set_wmclass("azote", "azote")

        window.connect_after('destroy', self.destroy)

        main_box = Gtk.Box()
        main_box.set_spacing(5)
        main_box.set_border_width(10)
        main_box.set_orientation(Gtk.Orientation.VERTICAL)
        window.add(main_box)

        # This contains a Gtk.ScrolledWindow with Gtk.Grid() inside, filled with ThumbButton(Gtk.Button) instances
        common.preview = Preview()
        window.connect('configure-event', on_configure_event)

        main_box.pack_start(common.preview, False, False, 0)

        # Label to display details of currently selected picture
        common.selected_picture_label = Gtk.Label()
        common.selected_picture_label.set_text('Select a picture')

        main_box.pack_start(common.selected_picture_label, False, False, 0)

        # Button to set the wallpapers folder
        folder_button = Gtk.Button(common.settings.src_path)
        main_box.pack_start(folder_button, False, False, 0)

        folder_button.connect_after('clicked', self.on_folder_clicked)

        # We need a horizontal container to display outputs in columns
        displays_box = Gtk.Box()
        displays_box.set_spacing(15)
        displays_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        window.add(main_box)

        common.display_boxes_list = []
        for display in displays:
            # Label format: name (width x height)
            display_box = DisplayBox(
                "{} ({} x {})".format(display.get('name'), display.get('width'), display.get('height')))
            common.display_boxes_list.append(display_box)
            displays_box.pack_start(display_box, True, False, 0)

        main_box.pack_start(displays_box, False, False, 0)

        # Bottom buttons will also need a horizontal container
        bottom_box = Gtk.Box()
        bottom_box.set_spacing(15)
        bottom_box.set_border_width(10)
        bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        all_screens_button = Gtk.Button("Divide selected between screens")
        bottom_box.pack_start(all_screens_button, True, True, 0)

        apply_button = Gtk.Button("Apply")
        apply_button.connect('clicked', self.on_apply_button)
        bottom_box.pack_start(apply_button, True, True, 0)

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
        dialog = Gtk.FileChooserDialog("Open folder", button.get_toplevel(), Gtk.FileChooserAction.SELECT_FOLDER);
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

    def on_apply_button(self, button):
        for box in common.display_boxes_list:
            print(box.wallpaper_path)


def check_displays():
    displays = []
    try:
        i3 = i3ipc.Connection()
        common.outputs = i3.get_outputs()
        for output in common.outputs:
            if output.active:  # dunno WTF xroot-0 is: i3 returns such an output with "active":false
                display = {'name': output.name,
                           'x': output.rect.x,
                           'y': output.rect.y,
                           'width': output.rect.width,
                           'height': output.rect.height}
                displays.append(display)
                log("Output: {}".format(display), common.INFO)

        # for testing
        display = {'name': 'HDMI-A-2',
                   'x': 0,
                   'y': 0,
                   'width': 1920,
                   'height': 1080}
        displays.append(display)
        log("Output: {}".format(display), common.INFO)

        """display = {'name': 'HDMI-A-3',
                   'x': 0,
                   'y': 0,
                   'width': 1920,
                   'height': 1080}
        displays.append(display)
        log("Output: {}".format(display), common.INFO)

        display = {'name': 'HDMI-A-4',
                   'x': 1366,
                   'y': 728,
                   'width': 1920,
                   'height': 1080}
        displays.append(display)
        log("Output: {}".format(display), common.INFO)"""

        return displays
    except Exception as e:
        log(e, common.ERROR)
        return None


def on_configure_event(window, e):
    cols = e.width // 256
    if cols != common.cols:
        common.preview.hide()
        if cols != common.cols:
            common.cols = cols
            common.preview.refresh(False)

        common.preview.show()
        print("Refresh!")


def main():
    screen = Gdk.Screen.get_default()
    print(Gdk.Screen.get_display(screen))
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

    set_env()  # set paths and stuff
    displays = check_displays()
    common.cols = len(displays) if len(displays) > 3 else 3
    app = GUI(displays)
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
