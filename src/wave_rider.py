
import sys
import os

import pygame
from pygame import Rect

from albow.widget import Widget
from albow.screen import Screen
from albow.layout import Column, Row, Grid
from albow.root import RootWidget
from albow.controls import Button, Label
from albow.menu_bar import MenuBar
from albow.menu import Menu
import albow.dialogs
import albow.file_dialogs


from emotiv_device_monitor import EmotivDeviceMonitor
from emotiv_device import EmotivDevice
from signal_buffer import SignalBuffer
from signal_writer import SignalWriter
from signal_renderer_widget import SignalRendererWidget
from emotiv_data_packet import counter_to_sensor_id


class WaveRiderGUI(RootWidget):
    """
    The GUI elements of the main screen for wave rider.
    """
    
    def __init__(self, surf, **kwds):
        RootWidget.__init__(self, surf, **kwds)
        self.bg_color = (255,255,255)
        self.redraw_every_frame = True
        self.set_timer(50)

        self.recording_in_progress = False

        self.sig_buf = SignalBuffer(768, 14)

        mon.callbacks.append(self.update_device_status)
        mon.callbacks.append(self.start_device_reader)

        self.gyrox_label = Label('', width = 80, height = 30, bg_color = (30, 30, 255))
        self.gyroy_label = Label('', width = 80, height = 30, bg_color = (30, 30, 255))
        self.signal_mag_label = Label('', width = 80, height = 30)

        small_font = pygame.font.SysFont('Ubuntu', 12)

        self.renderer = SignalRendererWidget(counter_to_sensor_id,
                                             dev,
                                             self.sig_buf,
                                             Rect(0, 0, 880, 660))
        self.add(self.renderer)

        c = Column([
                Button("Start REC",
                       action = self.start_recording,
                       enabled = lambda: not self.recording_in_progress,
                       bg_color = (0, 0, 128),
                       height = 30,
                       margin = 3),
                Button("Stop REC",
                       action = self.stop_recording,
                       enabled = lambda: self.recording_in_progress,
                       bg_color = (0, 0, 128),
                       height = 30,
                       margin = 3),
                Widget(height = 70),
                Label('Gyro Data', height = 30),
                self.gyrox_label,
                self.gyroy_label,
                Button("Cursor",
                       action = self.toggle_cursor_rendering,
                       bg_color = (255, 0, 0),
                       height = 30,
                       margin = 3),
#                Widget(height = 30),
                Label('EEG Mag', height = 30),
                Row( [
                        Button("+",
                               action = lambda: self.renderer.update_magnification(+0.2),
                               bg_color = (80, 100, 40),
                               width = 30,
                               margin = 5),
                        Button("-",
                               action = lambda: self.renderer.update_magnification(-0.2),
                               bg_color = (80, 100, 40),
                               margin = 5,
                               width = 30) ]),
                self.signal_mag_label,
                Button("Clear",
                       action = lambda: self.sig_buf.clear(),
                       bg_color = (255, 0, 0),
                       height = 30,
                       margin = 5),
                Label('Channels', width = 100, bg_color = (50, 50, 255)),
                Grid([ [ Button("F3", font = small_font, action = lambda: self.renderer.toggle_channel(0)),
                         Button("FC5", font = small_font, action = lambda: self.renderer.toggle_channel(1)),
                         Button("AF3", font = small_font, action = lambda: self.renderer.toggle_channel(2)),
                         Button("F7", font = small_font, action = lambda: self.renderer.toggle_channel(3)) ],
                       [ Button("T7", font = small_font, action = lambda: self.renderer.toggle_channel(4)),
                         Button("P7", font = small_font, action = lambda: self.renderer.toggle_channel(5)),
                         Button("O1", font = small_font, action = lambda: self.renderer.toggle_channel(6)),
                         Button("O2", font = small_font, action = lambda: self.renderer.toggle_channel(7)) ],
                       [ Button("P8", font = small_font, action = lambda: self.renderer.toggle_channel(8)),
                         Button("T8", font = small_font, action = lambda: self.renderer.toggle_channel(9)),
                         Button("F8", font = small_font, action = lambda: self.renderer.toggle_channel(10)),
                         Button("AF4", font = small_font, action = lambda: self.renderer.toggle_channel(11)) ],
                       [ Button("FC6", font = small_font, action = lambda: self.renderer.toggle_channel(12)),
                         Button("F4", font = small_font, action = lambda: self.renderer.toggle_channel(13)) ] ],
                     row_spacing = 5,
                     column_spacing = 8,
                     width = 100),
#                Widget(height = 55),
                Button("  QUIT  ",
                       action = self.quit,
                       bg_color = (200, 0, 64),
                       margin = 5
                       )],
                   align = 'c',
                   spacing = 20,
                   bg_color = (50, 50, 50),
                   rect = Rect(880, 0, 120, 690),
                   height = 690,
                   expand = True,
                   margin = 5)

        self.stat_label = Label('', 100, margin = 3)
        self.packet_speed_label = Label('', 100, margin = 3)
        self.recording_label = Label('NOT RECORDING', 400, margin = 3)
        self.battery_label = Label('NO DATA', 100, margin = 3)
        r = Row([ self.stat_label, self.packet_speed_label, self.battery_label, self.recording_label, Widget(width = 50, height = 30) ],
                rect = Rect(0, 660, 880, 30),
                width = 880,
                height = 30,
                expand = True,
                margin = 5,
                spacing = 20,
                bg_color = (50, 50, 50))

        self.add(c)
        self.add(r)

        # first update is manual
        self.update_device_status(mon.check_connected())

        # eeg rendering widget
        self.renderer = SignalRendererWidget(counter_to_sensor_id,
                                             dev,
                                             self.sig_buf,
                                             Rect(0, 0, 880, 660))
        self.add(self.renderer)

        self.update_ps_counter = 0
        self.rec = None

        self.render_cursor = False
        self.sq_pos = (400, 300)


    def start_device_reader(self, status):
        if status:
            dev.start_reader()


    def update_device_status(self, status):
        self.stat_label.text = 'ONLINE' if status else 'OFFLINE'
        self.stat_label.bg_color = (50, 255, 50) if status else (255, 30, 30)
        self.stat_label.invalidate()


    def update_packet_speed_label(self):
        if self.update_ps_counter > 10:
            self.packet_speed_label.text = '%.1f S/sec' % dev.packet_speed if dev.packet_speed > 0 else 'NO DATA'
            self.packet_speed_label.bg_color = (50, 255, 50) if dev.packet_speed > 0 else (255, 30, 30)
            self.packet_speed_label.invalidate()
            self.update_ps_counter = 0
        else:
            self.update_ps_counter += 1

    def update_gyro_labels(self):
        if dev.gyro_x is not None:
            self.gyrox_label.text = 'X = %d' % dev.gyro_x
        if dev.gyro_y is not None:
            self.gyroy_label.text = 'Y = %d' % dev.gyro_y
        

    def toggle_cursor_rendering(self):
        if self.render_cursor == False:
            self.sq_pos = (400, 300)
            
        self.render_cursor = not self.render_cursor


    def begin_frame(self):
        self.update_packet_speed_label()
        self.update_gyro_labels()

        self.signal_mag_label.text = 'mag: %gx' % self.renderer.multiplier
        self.signal_mag_label.invalidate()

        if dev.battery is not None:
            self.battery_label.text = 'BATT: %d%%' % (dev.battery * 100) 
        else:
            self.battery_label.text = 'NO DATA'
        self.battery_label.invalidate()

        # no sense in updating if we are not going to use it
        if self.render_cursor and (dev.gyro_x is not None) and (dev.gyro_y is not None):
            new_pos_x = max(20, min(800, self.sq_pos[0] + (105 - dev.gyro_x) * 4)) if abs(dev.gyro_x - 105) > 1 else self.sq_pos[0]
            new_pos_y = max(20, min(600, self.sq_pos[1] + (dev.gyro_y - 105) * 4)) if abs(dev.gyro_y - 105) > 1 else self.sq_pos[1]
            self.sq_pos = new_pos_x, new_pos_y

        RootWidget.begin_frame(self)


    def draw_all(self, surf):

        # draw the root widgets
        Widget.draw_all(self, surf)

        # only render the cursor if required
        if self.render_cursor:
            pos = self.sq_pos
            pygame.draw.rect(display, (0, 0, 0), Rect(pos[0] - 10, pos[1] - 10, 20, 20))



    def start_recording(self):
        if self.rec is not None:
            albow.dialogs.alert('Recording in progress!')
            return

        fname = albow.file_dialogs.request_new_filename("Select output file ...", suffix = "csv", directory = 'data')
        if fname is None:
            return

        # start the recording
        self.rec = SignalWriter()
        self.rec.open(fname)

        if not self.rec.ready():
            albow.dialogs.alert("File cannot be opened, cancelling recording.")
            self.rec = None
            return

        # update the recording label
        self.recording_label.text = 'Recording to [%s]' % os.path.basename(fname)
        self.recording_label.bg_color = (255, 30, 30)
        self.recording_label.invalidate()

        dev.subscribe(self.rec.write_packet)


    def stop_recording(self):
        if self.rec is None:
            albow.dialogs.alert("There is no recording in progress.")
            return

        # stop the recording
        dev.unsubscribe(self.rec.write_packet)

        self.rec.close()
        self.rec = None
        
        # update the recording label
        self.recording_label.text = 'NOT RECORDING'
        self.recording_label.bg_color = (50, 50, 50)
        self.recording_label.invalidate()
  

    def confirm_quit(self):
        """
        Check if we really want to quit.
        """
        if self.rec is not None:
            albow.dialogs.alert("You are recording! Stop the recording before exiting.")
            return

        return albow.dialogs.ask("Are you sure you want to quit?", ["Yes", "No"]) == "Yes"
        

    def exit_cmd(self):
        self.quit()

    def quit(self):

        if not self.confirm_quit():
            return

        # we're quitting
        mon.stop()
        dev.stop_reader()
        pygame.quit()
        sys.exit(0)


if __name__ == '__main__':

    # init the pygae subsystem
    pygame.init()
    display = pygame.display.set_mode((1000,700), 0)

    # init the device & monitor
    mon = EmotivDeviceMonitor()
    dev = EmotivDevice('SN20120229000254')

    # create the main GUI window
    rootwidget = WaveRiderGUI(display)

    # check the device status
    mon.check_connected()
    mon.start()

    # execution does not reach past the run() function
    rootwidget.run()

    
