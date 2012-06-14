
import numpy as np
import bisect

import pygame

from albow.widget import Widget, overridable_property
from albow.theme import ThemeProperty



class SignalRendererWidget(Widget):
	
	
    def __init__(self, signal_list, dev, buf, rect, **kwds):
        """
        Initialize the renderer with the signal_name to index mapping
        (always all 14 signals).  The measurement device, the signal
        buffer and the rectangle into which the signals are to be rendered.
        To select shown signals, use select_channels.
        """
        Widget.__init__(self, rect, **kwds)
	self.sig_list = signal_list
	self.dev = dev
	self.buf = buf
	self.font = pygame.font.SysFont("Ubuntu", 20, True)
        self.cq_font = pygame.font.SysFont("Ubuntu", 16, True)
        self.multiplier = 1.0
        self.selected = range(14)


    def select_channels(self, which):
        """
        Supply a new array of integers which indicate the signals to show.
        """
        self.selected = which


    def toggle_channel(self, ndx):
        """
        Toggle the display of channel with index ndx (0..13).
        """
#        print("Toggle chanbel %d" % ndx)
        if ndx in self.selected:
            self.selected.remove(ndx)
        else:
            # need to re-sort the list after the append
            bisect.insort(self.selected, ndx)
#            self.selected.append(ndx)
#            self.selected.sort()


    def update_magnification(self, update):
        self.multiplier = max(0.4, self.multiplier + update)


    def draw(self, surf):
	"""
	Draw the signals.  Here we expect the signal buffer to be updated.
	"""
        frame = surf.get_rect()

        pygame.draw.rect(surf, (255,255,255), frame)

	# plot the signals
        Nsig = len(self.selected)
        if Nsig == 0:
            return

	gr_height = (frame.bottom - frame.top) // Nsig
	gr_width = frame.width

	# get a handle to the buffer
	self.buf.pull_packets(self.dev)
	buf = self.buf.buffer()

	# for each signal repeat
	for s, sndx in zip(self.selected, range(len(self.selected))):

            # retrieve channel name
            chan_name = self.sig_list[s]

	    # compute zero axis position for this signal & draw axis
	    zero_ax_y = frame.top + gr_height * sndx + gr_height // 2
	    pygame.draw.line(surf, (70, 70, 70), (frame.left, zero_ax_y), (frame.right, zero_ax_y))

	    # draw the signal onto the screen (remove mean in buffer)
            if True:
                sig = buf[:,s]
                zero_lev = np.mean(sig)
                sig_pp = max(np.max(sig) - zero_lev, zero_lev - np.min(sig))
                if sig_pp == 0:
                    sig_pp = 1.0
                pixel_per_bit = self.multiplier * gr_height / sig_pp
                draw_pts_y = zero_ax_y - (sig - zero_lev) * pixel_per_bit
            else:
                fft = np.abs(np.fft.rfft(sig))
#                draw_pts_y = zero_ax_y - 

            draw_pts_x = np.linspace(0, gr_width, len(sig)) + frame.left

            color = (255, 0, 0) if sndx % 2 == 0 else (0, 0, 255)
            pygame.draw.lines(surf, color, False, zip(draw_pts_x, draw_pts_y))

            # draw a bar that corresponds to one mV
            uV100_len = 10.0 / 0.51 * pixel_per_bit
            if uV100_len > gr_height:
                uV100_len = gr_height * 3 // 4
                uV100_col = (255, 0, 0)
            else:
                uV100_col = (0, 0, 0)
                
            pygame.draw.line(surf, uV100_col, 
                             (frame.right - 10, zero_ax_y - uV100_len // 2),
                             (frame.right - 10, zero_ax_y + uV100_len // 2), 2)

	    # draw a bar indicating contact quality
	    cq = self.dev.cq[chan_name]
            cr, cr_str = self.dev.contact_resistance(chan_name)
            
#	    line_len = int(min(cq, 1.0) * 40.0)
#	    pygame.draw.line(surf, (0, 255, 0), (frame.left + 10, zero_ax_y + 12), (frame.left + 10 + line_len, zero_ax_y + 12), 4)
#	    pygame.draw.line(surf, (0, 0, 0), (frame.left + 10 + line_len, zero_ax_y + 12), (frame.left + 50, zero_ax_y + 12), 4)
            
            
	    # adjust the signal font color to reflect signal quality
#	    if cq < 0.3:
#                quality_color = (255, 0, 0)
#	    elif cq < 0.6:
#                quality_color = (180, 200, 0)
#	    elif cq < 0.9:
#                quality_color = (255, 255, 0)
#	    else:

            if cr is None or cr > 1000:
                quality_color = (255, 0, 0)
            elif cr > 50:
                quality_color = (200, 100, 20)
            elif cr > 20:
                quality_color = (200, 100, 20)
            else:
                quality_color = (20, 150, 20)

	    surf.blit(self.font.render(self.sig_list[s], 1, (0,0,0)), (frame.left + 10, zero_ax_y - 10))
            surf.blit(self.cq_font.render('%d (%s)' % (cq, cr_str), 1, quality_color), (frame.left + 10, zero_ax_y  + 10))
