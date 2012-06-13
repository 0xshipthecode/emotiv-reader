#---------------------------------------------------------------------------
#
#   Albow - Root widget
#
#---------------------------------------------------------------------------

import sys
import pygame
from pygame.locals import *
from pygame.time import get_ticks
from pygame.event import Event
import widget
from widget import Widget

mod_cmd = KMOD_LCTRL | KMOD_RCTRL | KMOD_LMETA | KMOD_RMETA
double_click_time = 300 # milliseconds

modifiers = dict(
	shift = False,
	ctrl = False,
	alt = False,
	meta = False,
)

modkeys = {
	K_LSHIFT: 'shift',  K_RSHIFT: 'shift',
	K_LCTRL:  'ctrl',   K_RCTRL:  'ctrl',
	K_LALT:   'alt',    K_RALT:   'alt',
	K_LMETA:  'meta',   K_RMETA:  'meta',
}

MUSIC_END_EVENT = USEREVENT + 1

last_mouse_event = Event(0, pos = (0, 0), local = (0, 0))
last_mouse_event_handler = None
root_widget = None     # Root of the containment hierarchy
top_widget = None      # Initial dispatch target
clicked_widget = None  # Target of mouse_drag and mouse_up events

#---------------------------------------------------------------------------

class Cancel(Exception):
	pass

#---------------------------------------------------------------------------

def set_modifier(key, value):
	attr = modkeys.get(key)
	if attr:
		modifiers[attr] = value

def add_modifiers(event):
	d = event.dict
	d.update(modifiers)
	d['cmd'] = event.ctrl or event.meta

def get_root():
	return root_widget

def get_top_widget():
	return top_widget

def get_focus():
	return top_widget.get_focus()

#---------------------------------------------------------------------------

class RootWidget(Widget):
	#  surface   Pygame display surface
	#  is_gl     True if OpenGL surface

	redraw_every_frame = False
	do_draw = False
	_is_gl_container = True

	def __init__(self, surface):
		global root_widget
		Widget.__init__(self, surface.get_rect())
		self.surface = surface
		root_widget = self
		widget.root_widget = self
		self.is_gl = surface.get_flags() & OPENGL <> 0
	
	def set_timer(self, ms):
		pygame.time.set_timer(USEREVENT, ms)

	def run(self):
		self.run_modal(None)

	def run_modal(self, modal_widget):
		global last_mouse_event, last_mouse_event_handler
		global top_widget, clicked_widget
		is_modal = modal_widget is not None
		modal_widget = modal_widget or self
		try:
			old_top_widget = top_widget
			top_widget = modal_widget
			was_modal = modal_widget.is_modal
			modal_widget.is_modal = True
			modal_widget.modal_result = None
			if not modal_widget.focus_switch:
				modal_widget.tab_to_first()
			mouse_widget = None
			if clicked_widget:
				clicked_widget = modal_widget
			num_clicks = 0
			last_click_time = 0
			self.do_draw = True
			while modal_widget.modal_result is None:
				try:
					if self.do_draw:
						if self.is_gl:
							self.gl_clear()
							self.gl_draw_all(self, (0, 0))
						else:
							self.draw_all(self.surface)
						self.do_draw = False
						pygame.display.flip()
					events = [pygame.event.wait()]
					events.extend(pygame.event.get())
					for event in events:
						type = event.type
						if type == QUIT:
							self.quit()
						elif type == MOUSEBUTTONDOWN:
							self.do_draw = True
							t = get_ticks()
							if t - last_click_time <= double_click_time:
								num_clicks += 1
							else:
								num_clicks = 1
							last_click_time = t
							event.dict['num_clicks'] = num_clicks
							add_modifiers(event)
							mouse_widget = self.find_widget(event.pos)
							if not mouse_widget.is_inside(modal_widget):
								mouse_widget = modal_widget
							clicked_widget = mouse_widget
							last_mouse_event_handler = mouse_widget
							last_mouse_event = event
							mouse_widget.notify_attention_loss()
							mouse_widget.handle_mouse('mouse_down', event)
						elif type == MOUSEMOTION:
							add_modifiers(event)
							modal_widget.dispatch_key('mouse_delta', event)
							mouse_widget = self.find_widget(event.pos)
							last_mouse_event = event
							if clicked_widget:
								last_mouse_event_handler = mouse_widget
								clicked_widget.handle_mouse('mouse_drag', event)
							else:
								if not mouse_widget.is_inside(modal_widget):
									mouse_widget = modal_widget
								last_mouse_event_handler = mouse_widget
								mouse_widget.handle_mouse('mouse_move', event)
						elif type == MOUSEBUTTONUP:
							add_modifiers(event)
							self.do_draw = True
							mouse_widget = self.find_widget(event.pos)
							if clicked_widget:
								last_mouse_event_handler = clicked_widget
								last_mouse_event = event
								clicked_widget = None
								last_mouse_event_handler.handle_mouse('mouse_up', event)
						elif type == KEYDOWN:
							key = event.key
							set_modifier(key, True)
							self.do_draw = True
							self.send_key(modal_widget, 'key_down', event)
							if last_mouse_event_handler:
								event.dict['pos'] = last_mouse_event.pos
								event.dict['local'] = last_mouse_event.local
								last_mouse_event_handler.setup_cursor(event)
						elif type == KEYUP:
							key = event.key
							set_modifier(key, False)
							self.do_draw = True
							self.send_key(modal_widget, 'key_up', event)
							if last_mouse_event_handler:
								event.dict['pos'] = last_mouse_event.pos
								event.dict['local'] = last_mouse_event.local
								last_mouse_event_handler.setup_cursor(event)
						elif type == MUSIC_END_EVENT:
							self.music_end()
						elif type == USEREVENT:
							make_scheduled_calls()
							if not is_modal:
								self.do_draw = self.redraw_every_frame
								if last_mouse_event_handler:
									event.dict['pos'] = last_mouse_event.pos
									event.dict['local'] = last_mouse_event.local
									add_modifiers(event)
									last_mouse_event_handler.setup_cursor(event)
								self.begin_frame()
				except Cancel:
					pass
		finally:
			modal_widget.is_modal = was_modal
			top_widget = old_top_widget
		clicked_widget = None
	
	def send_key(self, widget, name, event):
		add_modifiers(event)
		widget.dispatch_key(name, event)
	
	def begin_frame(self):
		pass

	def get_root(self):
		return self

	def has_focus(self):
		return True

	def quit(self):
		if self.confirm_quit():
			sys.exit(0)

	def confirm_quit(self):
		return True

	def get_mouse_for(self, widget):
		last = last_mouse_event
		event = Event(0, last.dict)
		event.dict['local'] = widget.global_to_local(event.pos)
		add_modifiers(event)
		return event

	def gl_clear(self):
		from OpenGL import GL
		bg = self.bg_color
		if bg:
			r = bg[0] / 255.0
			g = bg[1] / 255.0
			b = bg[2] / 255.0
			GL.glClearColor(r, g, b, 0.0)
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT
			| GL.GL_ACCUM_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)
	
	def music_end(self):
		import music
		music.music_end()

#---------------------------------------------------------------------------

from time import time
from bisect import insort

scheduled_calls = []

def make_scheduled_calls():
	sched = scheduled_calls
	t = time()
	while sched and sched[0][0] <= t:
		sched[0][1]()
		sched.pop(0)

def schedule(delay, func):
	"""Arrange for the given function to be called after the specified
	delay in seconds. Scheduled functions are called synchronously from
	the event loop, and only when the frame timer is running."""
	t = time() + delay
	insort(scheduled_calls, (t, func))
