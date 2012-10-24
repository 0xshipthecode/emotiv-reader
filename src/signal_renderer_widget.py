
import numpy as np
import bisect

import pygame
import scipy.signal


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
        self.display_type = [0] * 14


    def select_channels(self, which):
        """
        Supply a new array of integers which indicate the signals to show.
        """
        self.selected = which


    def toggle_channel(self, ndx):
        """
        Toggle the display of channel with index ndx (0..13).
        """
        if ndx in self.selected:
#            if self.display_type[ndx] == 1:
#                self.selected.remove(ndx)
#            else:
#                self.display_type[ndx] = 1
            self.selected.remove(ndx)
        else:
            # need to re-sort the list after the append
            bisect.insort(self.selected, ndx)
            self.display_type[ndx] = 0


    def update_magnification(self, update):
        """
        Set the magnification of the displayed signal.
        """
        self.multiplier = max(0.2, self.multiplier + update)

    
    def render_time_series(self, sig, color, frame, surf):
        """
        Render a time series representation (given by pts) into rect.
        """

        # draw the zero level
        zero_ax_y = frame.top + frame.height // 2
        pygame.draw.line(surf, (70, 70, 70),
                         (frame.left, zero_ax_y),
                         (frame.right, zero_ax_y))
        pygame.draw.line(surf, (20, 60, 20, 30), 
                         (frame.left, frame.bottom),
                         (frame.right, frame.bottom))

        # draw the signal onto the screen (remove mean in buffer)
        zero_lev = np.mean(sig)
        sig_amp = max(np.max(sig) - zero_lev, zero_lev - np.min(sig))
        if sig_amp == 0:
            sig_amp = 1.0
#        pixel_per_lsb = self.multiplier * frame.height / sig_amp / 2.0
        pixel_per_lsb = self.multiplier * frame.height / (200.0 / 0.51)
        draw_pts_y = zero_ax_y - (sig - zero_lev) * pixel_per_lsb
        draw_pts_y[draw_pts_y < frame.top] = frame.top
        draw_pts_y[draw_pts_y > frame.bottom] = frame.bottom
        draw_pts_x = np.linspace(0, frame.width, len(sig)) + frame.left

        pygame.draw.lines(surf, color, False, zip(draw_pts_x, draw_pts_y))

        # draw a bar that corresponds to 10uV
        uV10_len = 10.0 / 0.51 * pixel_per_lsb
        if uV10_len > frame.height:
            uV10_len = frame.height * 3 // 4
            uV10_col = (255, 0, 0)
        else:
            uV10_col = (0, 0, 0)
                
        pygame.draw.line(surf, uV10_col, 
                         (frame.right - 10, zero_ax_y - uV10_len // 2),
                         (frame.right - 10, zero_ax_y + uV10_len // 2), 2)


    def render_spectrum(self, sig, color, frame, surf):
        """
        Render a spectral representation of the signal.
        """
        min_freq = 0.7
        max_freq = 45.0

        s2 = sig.copy()

        # special check for all zeros (no data situation)
        if np.all(s2 == 0.0):
            sp = np.zeros(shape = (s2.shape[0] // 2, ))
        else:
            tm = np.arange(len(sig), dtype = np.float64) / 128.0
            angular_freqs = np.linspace(2.0 * np.pi * min_freq,
                                        2.0 * np.pi * max_freq, 100)
#            pg = scipy.signal.lombscargle(tm, s2, angular_freqs)
#            sp = np.sqrt(4 * (pg / tm.shape[0]))
            s2 = s2 - np.mean(s2)
            sp = np.abs(np.fft.rfft(s2))

        # if there are any non-finite values, replace buffer with zeros
        if not np.all(np.isfinite(sp)):
            sp[:] = 0.0

        # autoscale the spectral display
#        sp -= np.amin(sp)
        sig_amp = np.amax(sp)
        if sig_amp == 0:
            sig_amp = 1.0
        pixel_per_lsb = self.multiplier * frame.height / sig_amp / 2.0
        draw_pts_y = frame.bottom - sp * pixel_per_lsb
        draw_pts_x = np.linspace(0, frame.width, len(sp)) + frame.left

        # draw line at bottom of frame
        pygame.draw.line(surf, (20, 60, 20, 30), (frame.left, frame.bottom), 
                         (frame.right, frame.bottom))

        # draw the spectrum in dB
        pygame.draw.lines(surf, color, False, zip(draw_pts_x, draw_pts_y))

        # draw spectral bands
        for f in [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]:
            x = (f - min_freq) / max_freq * frame.width + frame.left
            pygame.draw.line(surf, (0, 0, 0), (x, frame.top), (x, frame.bottom))

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
        surf.blit(self.font.render(chan_name, 1, (0,0,0)), (frame.right - 150, zero_ax_y - 10))
        surf.blit(self.cq_font.render('%d (%s)' % (cq, cr_str), 1, quality_color),
                  (frame.right - 150, zero_ax_y  + 10))


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
            if self.display_type[s] == 0:
                self.render_time_series(buf[:,s], color, rect, surf)
            else:
                self.render_spectrum(buf[:,s], color, rect, surf)

            # draw the signal name
            self.render_name_and_contact_quality(chan_name, rect, surf)
            
