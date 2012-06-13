

from albow.widget import Widget, overridable_property
from albow.theme import ThemeProperty



class SignalRendererWidget(Widget):
	#  image   Image to display
	
	highlighted = False
	
	def __init__(self, signal_list, buf, rect, **kwds):
		Widget.__init__(self, rect, **kwds)
                self.sig_list = signal_list
                self.buf = buf

	def draw(self, surf):
		frame = surf.get_rect()
                print frame
