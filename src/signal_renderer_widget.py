
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

    
    def render_time_series(self, sig, color, frame, surf):
        """
        Render a time series representation (given by pts) into rect.
        """

        # draw the zero level
        zero_ax_y = frame.top + frame.height // 2
#        pygame.draw.line(surf, (70, 70, 70), (frame.left, zero_ax_y), (frame.right, zero_ax_y))
        pygame.draw.line(surf, (20, 60, 20, 30), 
                         (frame.left, frame.bottom),
                         (frame.right, frame.bottom))

        # draw the signal onto the screen (remove mean in buffer)
        zero_lev = np.mean(sig)
        sig_amp = max(np.max(sig) - zero_lev, zero_lev - np.min(sig))
        if sig_amp == 0:
            sig_amp = 1.0
        pixel_per_lsb = self.multiplier * frame.height / sig_amp / 2.0
#        pixel_per_lsb = self.multiplier * frame.height / (50 / 0.51) / 2.0
        draw_pts_y = zero_ax_y - (sig - zero_lev) * pixel_per_lsb
        draw_pts_x = np.linspace(0, frame.width, len(sig)) + frame.left

        pygame.draw.lines(surf, color, False, zip(draw_pts_x, draw_pts_y))

        # draw a bar that corresponds to 10uV
        uV100_len = 10.0 / 0.51 * pixel_per_lsb
        if uV100_len > frame.height:
            uV100_len = frame.height * 3 // 4
            uV100_col = (255, 0, 0)
        else:
            uV100_col = (0, 0, 0)
                
        pygame.draw.line(surf, uV100_col, 
                         (frame.right - 10, zero_ax_y - uV100_len // 2),
                         (frame.right - 10, zero_ax_y + uV100_len // 2), 2)


    def render_spectrum(self, sig, color, frame, surf):
        """
        Render a spectral representation of the signal.
        """

        # special check for all zeros (no data situation)
        sig -= np.mean(sig)
        if np.all(np.abs(sig) < 1.0):
            sp = np.zeros(shape=(len(sig)/2,))
        else:
            sp = 20 * np.log(np.abs(np.fft.rfft(sig)))

        # autoscale the FFT display
        sp -= np.amin(sp)
        sig_amp = np.amax(sp)
        if sig_amp == 0:
            sig_amp = 1.0
        pixel_per_lsb = self.multiplier * frame.height / sig_amp / 2.0
        draw_pts_y = frame.bottom - sp * pixel_per_lsb
        draw_pts_x = np.linspace(0, frame.width, len(sp)) + frame.left

        print draw_pts_y
        print draw_pts_x

        # draw line at bottom of frame
        pygame.draw.line(surf, (20, 60, 20, 30), (frame.left, frame.bottom), 
                         (frame.right, frame.bottom))

        # draw the spectrum in dB
        pygame.draw.lines(surf, color, False, zip(draw_pts_x, draw_pts_y))

        # fixme: draw 20dB? yardstick


    def render_name_and_contact_quality(self, chan_name, frame, surf):

        # draw a bar indicating contact quality
        cq = self.dev.cq[chan_name]
        cr, cr_str = self.dev.contact_resistance(chan_name)

        # map signal resistance to color
        if cr is None or cr > 1000:
            quality_color = (255, 0, 0)
        elif cr > 50:
            quality_color = (200, 100, 20)
        elif cr > 20:
            quality_color = (200, 100, 20)
        else:
            quality_color = (20, 150, 20)

        zero_ax_y = frame.top + frame.height // 2
        surf.blit(self.font.render(chan_name, 1, (0,0,0)), (frame.left + 10, zero_ax_y - 10))
        surf.blit(self.cq_font.render('%d (%s)' % (cq, cr_str), 1, quality_color), (frame.left + 10, zero_ax_y  + 10))


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

	    # compute target rectangle
            rect = pygame.Rect(frame.left, frame.top + gr_height * sndx, frame.width, gr_height)

            # render a time series representation
            color = (255, 0, 0) if sndx % 2 == 0 else (0, 0, 255)
#            self.render_time_series(buf[:,s], color, rect, surf)
            self.render_time_series(buf[:,s], color, rect, surf)

            # draw the signal name
            self.render_name_and_contact_quality(chan_name, rect, surf)
            
