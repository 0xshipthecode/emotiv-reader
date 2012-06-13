
import pygame
import os
import random
import numpy as np

from emotiv_device import EmotivDevice
from signal_buffer import SignalBuffer
from signal_writer import SignalWriter
#from signal_filter import RealTimeFilter


# definitions and initializations
os.environ['SDL_VIDEO_CENTERED'] = '1'

mainloop, color, fontsize, delta, fps =  True, (32,32,32), 35, 1, 20

sensor_id_to_ndx = { 'F3' : 0, 'FC5' : 1, 'AF3' : 2, 'F7' : 3, 'T7' : 4,
                     'P7' : 5, 'O1' : 6, 'O2' : 7, 'P8' : 8, 'T8' : 9,
                     'F8' : 10, 'AF4' : 11, 'FC6' : 12, 'F4' : 13 }

counter_to_sensor_id = [ 'F3', 'FC5', 'AF3', 'F7', 'T7', 'P7', 'O1',
                         'O2', 'P8', 'T8', 'F8', 'AF4', 'FC6', 'F4' ]


if __name__ == '__main__':

    # signal writer for storing samples
    sw = SignalWriter()
    sw.open('signal.csv')
    print("Signal writer is ready: %s" % sw.ready())

    # initialize the devices & buffer
    dev = EmotivDevice('SN20120229000254')
    dev.subscribe(sw.write_packet)
    dev.start_reader()

    # signal buffer for reading samples from the EEG
    eeg = SignalBuffer(750, 14)

    # PyGame subsystem init
    pygame.init()
    Clock = pygame.time.Clock()

    try:
        screen = pygame.display.set_mode((800, 600))

        myFont = pygame.font.SysFont("Ubuntu", 20, True)

        chan_names = []
        for s in range(len(counter_to_sensor_id)):
            chan_names.append(myFont.render(counter_to_sensor_id[s], 1, (0, 0, 0)))

        while mainloop:

            # pull existing packets from the EEG
            pulled = eeg.pull_packets(dev)

            # wait for remaining time to next frame show
            tickFPS = Clock.tick(fps)

            # update window title
            pygame.display.set_caption("Press Esc to quit. FPS: %.2f PACKETS: %d" % 
                                       (Clock.get_fps(), pulled))

            # erase screen to black
            screen.fill((255,255,255))

            # plot the signals
            gr_height = 600 // 14
            gr_width = 750

            # get a handle to the buffer
            buf = eeg.buffer()

            for s in range(14):
                chan_name = counter_to_sensor_id[s]

                zero_ax_y = gr_height * s + gr_height // 2

                # draw the zero axis
                pygame.draw.line(screen, (0, 0, 255), (50, zero_ax_y), (800, zero_ax_y))

                # draw the signal onto the screen
                sig = buf[:,s]
                zero_lev = np.mean(sig)
                sig_amp = max(np.max(sig) - zero_lev, zero_lev - np.min(sig))
                if sig_amp == 0:
                    sig_amp = 1.0
                draw_pts_y = zero_ax_y - (sig - zero_lev) / sig_amp * gr_height / 2.0
                draw_pts_x = np.linspace(0, 750, len(sig)) + 50
                pygame.draw.lines(screen, (255,0,0), False, zip(draw_pts_x, draw_pts_y))

                # draw a bar indicating contact quality
#                screen.blit(chan_names[s], (10, zero_ax_y - 10.0))
                cq = dev.cq[chan_name]
                line_len = int(min(cq, 1.0) * 40.0)
                pygame.draw.line(screen, (0, 255, 0), (10, zero_ax_y + 12), (10 + line_len, zero_ax_y + 12), 4)
                pygame.draw.line(screen, (0, 0, 0), (10 + line_len, zero_ax_y + 12), (50, zero_ax_y + 12), 4)
            
                # adjust the signal font color to reflect signal quality
                if cq < 0.3:
                    quality_color = (255, 0, 0)
                elif cq < 0.6:
                    quality_color = (180, 200, 0)
                elif cq < 0.9:
                    quality_color = (255, 255, 0)
                else:
                    quality_color = (50, 255, 50)

                screen.blit(myFont.render(counter_to_sensor_id[s], 1, quality_color), (10, zero_ax_y - 10))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    mainloop = False # Be IDLE friendly!
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mainloop = False # Be IDLE friendly!

            pygame.display.update()

    except Exception as e:
        print e
 
    finally:
        print("Exiting.")
        pygame.quit()  # Keep this IDLE friendly 
        dev.stop_reader()
        sw.close()
