
import pygame

from albow.shell import Shell
from albow.screen import Screen
from albow.controls import Label, Button, Image, AttrRef, RadioButton, ValueDisplay
from albow.text_screen import TextScreen
from albow.fields import TextField, FloatField
from albow.layout import Row, Column, Grid
from albow.resource import get_font, get_image
from albow.dialogs import alert, ask
from albow.file_dialogs import request_old_filename, request_new_filename, look_for_file_or_directory

frame_time = 50 # ms

class DemoControlsScreen(Screen):

	def __init__(self, shell):
		Screen.__init__(self, shell)
		model = DemoControlsModel()
		width_field = FloatField(ref = AttrRef(model, 'width'))
		height_field = FloatField(ref = AttrRef(model, 'height'))
		area_display = ValueDisplay(ref = AttrRef(model, 'area'), format = "%.2f")
		shape = AttrRef(model, 'shape')
		shape_choices = Row([
			RadioButton(setting = 'rectangle', ref = shape), Label("Rectangle"),
			RadioButton(setting = 'triangle', ref = shape), Label("Triangle"),
			RadioButton(setting = 'ellipse', ref = shape), Label("Ellipse"),
		])
		grid = Grid([
			[Label("Width"), width_field],
			[Label("Height"), height_field],
			[Label("Shape"), shape_choices],
			[Label("Area"), area_display],
		])
		back = Button("Menu", action = shell.show_menu)
		contents = Column([grid, back])
		self.add_centered(contents)
		width_field.focus()
	
#--------------------------------------------------------------------------------

class DemoControlsModel(object):

	width = 0.0
	height = 0.0
	shape = 'rectangle'

	def get_area(self):
		a = self.width * self.height
		shape = self.shape
		if shape == 'rectangle':
			return a
		elif shape == 'triangle':
			return 0.5 * a
		elif shape == 'ellipse':
			return 0.25 * pi * a
	
	area = property(get_area)


class DemoDialogScreen(Screen):

	def __init__(self, shell):
		Screen.__init__(self, shell)
		menu = Column([
			Button("Ask a Question", self.test_ask),
			Button("Request Old Filename", self.test_old),
			Button("Request New Filename", self.test_new),
			Button("Look for File or Directory", self.test_lookfor),
		], align = 'l')
		contents = Column([
			Label("File Dialogs", font = get_font(18, "VeraBd.ttf")),
			menu,
			Button("Menu", action = shell.show_menu),
		], align = 'l', spacing = 30)
		self.add_centered(contents)
	
	def test_ask(self):
		response = ask("Do you like mustard and avocado ice cream?",
			["Yes", "No", "Undecided"])
		alert("You chose %r." % response)
	
	def test_old(self):
		path = request_old_filename()
		if path:
			alert("You chose %r." % path)
		else:
			alert("Cancelled.")

	def test_new(self):
		path = request_new_filename(prompt = "Save booty as:",
			filename = "treasure", suffix = ".dat")
		if path:
			alert("You chose %r." % path)
		else:
			alert("Cancelled.")

	def test_lookfor(self):
		path = look_for_file_or_directory(prompt = "Please find 'Vera.ttf'",
			target = "Vera.ttf")
		if path:
			alert("You chose %r." % path)
		else:
			alert("Cancelled.")


class DemoShell(Shell):

	def __init__(self, display):
		Shell.__init__(self, display)
		self.create_demo_screens()
		self.menu_screen = MenuScreen(self) # Do this last
		self.set_timer(frame_time)
		self.show_menu()
	
	def create_demo_screens(self):
		self.text_screen = TextScreen(self, "demo_text.txt")
		self.controls_screen = DemoControlsScreen(self)
		self.dialog_screen = DemoDialogScreen(self)
		self.anim_screen = DemoAnimScreen(self)
	
	def show_menu(self):
		self.show_screen(self.menu_screen)
	
	def begin_frame(self):
		self.anim_screen.begin_frame()


class DemoAnimScreen(Screen):

	def __init__(self, shell):
		Screen.__init__(self, shell)
		self.rect = shell.rect.inflate(-100, -100)
		w, h = self.size
		self.points = [[100, 50], [w - 50, 100], [50, h - 50]]
		from random import randint
		def randv():
			return randint(-5, 5)
		self.velocities = [[randv(), randv()] for i in range(len(self.points))]
		btn = Button("Menu", action = self.go_back)
		btn.rect.center = (w/2, h - 20)
		self.add(btn)
	
	def draw(self, surface):
		from pygame.draw import polygon
		polygon(surface, (128, 200, 255), self.points)
		polygon(surface, (255, 128, 0), self.points, 5)
	
	def begin_frame(self):
		r = self.rect
		w, h = r.size
		for p, v in zip(self.points, self.velocities):
			p[0] += v[0]
			p[1] += v[1]
			if not 0 <= p[0] <= w:
				v[0] = -v[0]
			if not 0 <= p[1] <= h:
				v[1] = -v[1]
		self.invalidate()

	def go_back(self):
		self.parent.show_menu()


class MenuScreen(Screen):

	def __init__(self, shell):
		Screen.__init__(self, shell)
		self.shell = shell
		f1 = get_font(24, "VeraBd.ttf")
		title = Label("Albow Demo", font = f1)
		def screen_button(text, screen):
			return Button(text, action = lambda: shell.show_screen(screen))
		menu = Column([
			screen_button("Text Screen", shell.text_screen),
			screen_button("Controls", shell.controls_screen),
			screen_button("Modal Dialogs", shell.dialog_screen),
			Button("Quit", shell.quit),
		], align = 'l')
		contents = Column([
			title,
			menu,
		], align = 'l', spacing = 20)
		self.add_centered(contents)
	
	def show_text_screen(self):
		self.shell.show_screen(self.text_screen)
	
	def show_fields_screen(self):
		self.shell.show_screen(self.fields_screen)
		self.fields_screen.fld1.focus()
	
	def show_anim_screen(self):
		self.shell.show_screen(self.anim_screen)
	
	def quit(self):
		sys.exit(0)


def main():
    pygame.init()
    display = pygame.display.set_mode((800,600), 0)
    shell = DemoShell(display)
    shell.run()
    pygame.quit()


main()
