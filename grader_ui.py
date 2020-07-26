from tkinter import *
from PIL import ImageTk, Image
from pathlib import Path
import math
import json
CANVAS_SIZE_RATIO = (0.7, .7)
CANVAS_PADDING = (20, 20)
POPUP_SPACE_RATIO = 0.8
POPUP_PADDING = 5
IMAGE_ROOT = "/mnt/Ubuntu_ext/Uni/MasterThesis/Scads_images/Fotos_ScaDS/"
CLASS_REPRESENTATION = "/mnt/Ubuntu_ext/Uni/MasterThesis/Dataset_Grader/class_rep.json"
GRADE_FILE = "/mnt/Ubuntu_ext/Uni/MasterThesis/Dataset_Grader/grades.json"

class ImageGrader:
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.root.title("Image Grader")
        self.root.geometry(f"{int(self.root.winfo_screenwidth())}x{self.root.winfo_screenheight()}")
        self.root.update()

        self.grade_dict = {}
        g_file = Path(GRADE_FILE)
        if g_file.is_file():
            with g_file.open("r") as json_file:
                self.grade_dict = json.load(json_file)
        print(self.grade_dict)
        self.image_canvas = Canvas(self.root, width=int(self.root.winfo_width() *CANVAS_SIZE_RATIO[0]), height=int(self.root.winfo_height()*CANVAS_SIZE_RATIO[1]), bg="grey")
        self.image_canvas.grid(row=3, column=3, rowspan=30)
        self.image_canvas.update()
        self.max_img_size = self.image_canvas.winfo_width()-CANVAS_PADDING[0], self.image_canvas.winfo_height()-CANVAS_PADDING[1]

        self.images = get_image_paths()
        self.image_idx = 0

        self.current_image = self.get_scaled_image(self.images[self.image_idx])
        self.canvas_img = self.image_canvas.create_image(int(self.image_canvas.winfo_width()/2),int(self.image_canvas.winfo_height()/2), image=self.current_image)

        self.image_name = StringVar(self.root, "")
        self.set_image_name_label()
        self.image_name_label = Label(self.root, textvariable=self.image_name)
        self.image_name_label.grid(row=1, column=3)

        self.prev_button = Button(self.root, text="Previous_Image", command=self.prev_image)
        self.prev_button.grid(row=1, pady=20)
        self.next_button = Button(self.root, text="Next_Image", command=self.next_image)
        self.next_button.grid(row=1, column=2)

        self.grade_value = IntVar()
        grade_good = Radiobutton(self.root, text="Clearly Visible/Very Good", padx=2, variable=self.grade_value, value=1)
        grade_mediocre = Radiobutton(self.root, text="Palely Occluded/ Good", variable=self.grade_value, value=2)
        grade_ok = Radiobutton(self.root, text="Heavily Occluded/ OK / Drawings", variable=self.grade_value,
                                     value=3)
        grade_bad = Radiobutton(self.root, text="No Overlap/ Bad", variable=self.grade_value,
                                     value=4)
        grade_good.grid(row=3, sticky="W")
        grade_mediocre.grid(row=4, sticky="W")
        grade_ok.grid(row=5, sticky="W")
        grade_bad.grid(row=6, sticky="W")
        if str(self.images[self.image_idx]) in self.grade_dict.keys():
            self.grade_value.set(self.grade_dict[str(self.images[self.image_idx])][1])
        self.image_class = StringVar(self.root, "")
        self.set_image_class_label()
        self.image_class_label = Label(self.root, textvariable=self.image_class)
        self.image_class_label.grid(row=33, column=3)
        self.image_class_label.bind("<Button-1>", self.open_class_selector)
        self.close_button = Button(self.root, text="Save & Close", command=self.save_and_exit)
        self.close_button.grid(row=33)
        self.popup = None
        with Path(CLASS_REPRESENTATION).open("r") as rep_file:
            rep_dict = json.load(rep_file)
        self.thumbnails, self.column_count = self.create_thumbnail_dict(rep_dict)
        self.selector_dict = {}

    def save_and_exit(self):
        with Path(GRADE_FILE).open("w") as json_file:
            json.dump(self.grade_dict, json_file)
        self.root.destroy()

    def get_scaled_image(self, image):
        image = Image.open(image)
        ratio = max(image.width/self.max_img_size[0], image.height/self.max_img_size[1])
        image = image.resize((int(image.width/ratio), int(image.height/ratio)), Image.ANTIALIAS)
        scaled = ImageTk.PhotoImage(image)
        return scaled

    def next_image(self):
        if self.grade_value.get() != 0:
            self.save_info()
            if self.image_idx < len(self.images)-1:
                self.image_idx += 1
                self.current_image = self.get_scaled_image(self.images[self.image_idx])
            self.image_canvas.itemconfig(self.canvas_img, image=self.current_image)
            self.set_image_name_label()
            self.set_image_class_label()
            if str(self.images[self.image_idx]) in self.grade_dict.keys():
                self.grade_value.set(self.grade_dict[str(self.images[self.image_idx])][1])

    def prev_image(self):
        if self.grade_value.get() != 0:
            self.save_info()
            if self.image_idx > 0:
                self.image_idx -= 1
                self.current_image = self.get_scaled_image(self.images[self.image_idx])
            self.image_canvas.itemconfig(self.canvas_img, image=self.current_image)
            self.set_image_name_label()
            self.set_image_class_label()
            if str(self.images[self.image_idx]) in self.grade_dict.keys():
                self.grade_value.set(self.grade_dict[str(self.images[self.image_idx])][1])

    def set_image_name_label(self):
        self.image_name.set(Path(self.images[self.image_idx]).stem)

    def set_image_class_label(self):
        # load if known
        if str(self.images[self.image_idx]) in self.grade_dict.keys():
            self.image_class.set(self.grade_dict[str(self.images[self.image_idx])][0])
        else:
            self.image_class.set(Path(self.images[self.image_idx]).parts[-2])

    def create_thumbnail_dict(self, rep_dict):
        thumbnail_dict = {}
        available_width = self.root.winfo_screenwidth() * POPUP_SPACE_RATIO
        available_height = self.root.winfo_screenheight() * POPUP_SPACE_RATIO
        aspect_ratio = available_width / available_height
        num_classes = len(rep_dict)
        column_count = math.ceil(math.sqrt(num_classes * aspect_ratio))
        row_count = math.ceil(num_classes / column_count)
        img_size = int(min(available_width / column_count, available_height / row_count)) - (POPUP_PADDING * 2)
        for class_name in rep_dict.keys():
            thumbnail_dict[class_name] = get_thumbnail_image(rep_dict[class_name], img_size)
        return thumbnail_dict, column_count

    def open_class_selector(self, e):
        self.popup = Toplevel()
        self.popup.wm_title("Class Selections")
        i = 0
        for class_name in self.thumbnails.keys():
            lab = Label(self.popup, image=self.thumbnails[class_name])
            self.selector_dict[lab._name] = class_name
            lab.bind("<Button-1>", lambda la: self.set_class_and_close(la))
            row, col = divmod(i, self.column_count)
            i += 1
            lab.grid(row=row, column=col, padx=POPUP_PADDING, pady=POPUP_PADDING)

    def set_class_and_close(self, callback):
        self.image_class.set(self.selector_dict[callback.widget._name])
        self.popup.destroy()

    def save_info(self):
        self.grade_dict[str(self.images[self.image_idx])] = (self.image_class.get(), self.grade_value.get())

def get_image_paths():
    all_files = []
    for child in Path(IMAGE_ROOT).iterdir():
        all_files.extend(child.glob("*.jpg"))
    return all_files


def get_thumbnail_image(image, max_size):
    image = Image.open(image)
    ratio = max(image.width/max_size, image.height/max_size)
    image = image.resize((int(image.width/ratio), int(image.height/ratio)), Image.ANTIALIAS)
    scaled = ImageTk.PhotoImage(image)
    return scaled

r = Tk()
ui = ImageGrader(r)
r.mainloop()

