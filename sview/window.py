import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.animation as anim

import datetime

mpl.rcParams['axes.facecolor'] = '#eee8d5'
mpl.rcParams['axes.grid'] = 'True'
mpl.rcParams['figure.facecolor'] = '#fdf6e3'
mpl.rcParams['font.family'] = 'sans-serif'

from .stream import Stream

class _MyAnim(anim.FuncAnimation):
    def __init__(self, fig, updater, interval, arg):
        self.run = 0
        self.updater = updater
        self.arg = arg
        super(_MyAnim, self).__init__(fig, lambda x: updater.update(arg), interval=interval, repeat=True)

    def _step(self, *args):
        if self.updater.is_update_needed(self.arg):
            super(_MyAnim, self)._step(*args)


class Window:
    def draw_event(self, event):
        print("draw_event")

    def __init__(self, title = 'Figure 1', updater = None):
        self.figure = plt.figure()
        self.streams = []
        self.dirty = True
        self.dirty_layout = True

        #self.figure.canvas.mpl_connect('draw_event',     self.draw_event)
        self.figure.canvas.mpl_connect('axes_enter_event',     self.mouse_enter)
        self.figure.canvas.mpl_connect('axes_leave_event',     self.mouse_leave)
        self.figure.canvas.mpl_connect('motion_notify_event',  self.mouse_move)
        self.figure.canvas.mpl_connect('scroll_event',         self.mouse_wheel)

        #self.figure.canvas.mpl_connect('button_press_event',   self.button_press)
        self.figure.canvas.mpl_connect('button_release_event', self.button_release)

        self.figure.canvas.mpl_connect('key_press_event',      self.key_press)
        self.figure.canvas.mpl_connect('key_release_event',    self.key_release)

        self.right_button_pressed = False
        self.figure.canvas.set_window_title(title)

        if updater:
            self.a = _MyAnim(self.figure, updater, interval=300, arg=self)
        #if anim_func:
        #    self.a = anim.FuncAnimation(self.figure, _ClosureWithArg(anim_func, self), frames=1, interval=200, repeat=True)


    def create_stream(self, updater = None, time_window = None):

        s = Stream(self, time_window)
        self.streams.append(s)
        self.dirty = True
        self.dirty_layout = True

        if updater:
            s.a = _MyAnim(self.figure, updater, interval=200, arg=s)
            #s.a = anim.FuncAnimation(self.figure, _ClosureWithArg(anim_func, s), frames=1, interval=200, repeat=True) #, blit=True)

        return s

    def destroy_stream(self, s):
        self.dirty = True
        self.dirty_layout = True
        self.streams.remove(s)
        s.destroy()

    def invalidate(self):
        self.dirty = True

    def calc_layout(self, streams, x, y, w, h):
        if len(streams) > 3:
            half = len(streams) // 2
            if h >= w*0.9:
                self.calc_layout(streams[0:half], x, y+h/2, w, h/2)
                self.calc_layout(streams[half:], x, y, w, h/2)
            else:
                self.calc_layout(streams[0:half], x, y, w/2, h)
                self.calc_layout(streams[half:], x+w/2, y, w/2, h)
        else:
            if len(streams) == 1:
                streams[0].set_position(x, y, w, h)
            elif len(streams) == 2:
                streams[0].set_position(x, y, w/2, h)
                streams[1].set_position(x+w/2, y, w/2, h)
            elif len(streams) == 3:
                streams[0].set_position(x, y, w/3, h)
                streams[1].set_position(x+w/3, y, w/3, h)
                streams[2].set_position(x+w*2/3, y, w/3, h)

    def prepare_artists(self):

        if self.dirty_layout:

            self.calc_layout(self.streams, 0.0, 0.0, 1.0, 1.0)
            self.dirty_layout = False

        #print("win.invalidate, ", self.dirty)
        if self.dirty:

            for s in self.streams:
                s.prepare_artists()

            self.dirty = False


    def mouse_move(self, event):
        if event.inaxes and event.inaxes.stream:
            event.inaxes.stream.mouse_move(event)



    def mouse_enter(self, event):
        if not event.inaxes:
            return

        event.inaxes.patch.set_facecolor("#EEE9CE")
        if event.inaxes.stream:
            event.inaxes.stream.mouse_enter(event)
        event.canvas.draw()

    def mouse_leave(self, event):
        if not event.inaxes:
            self.right_button_pressed = False
            return

        event.inaxes.patch.set_facecolor("#EEE8D5")
        if event.inaxes.stream:
            event.inaxes.stream.mouse_leave(event)
        event.canvas.draw()

    def mouse_wheel(self, event):
        if event.inaxes:

            if self.right_button_pressed:
                axis = event.inaxes.yaxis
                pos  = event.ydata
            else:
                axis = event.inaxes.xaxis
                pos  = event.xdata

            vmin, vmax = axis.get_view_interval()
            interval = abs(vmax - vmin)
            k = 0.2
            if event.button == 'down':
                delta = interval * k
            else:
                delta = interval * k / (1.0 + k) * -1.0

            #print("delta", delta, "vmin", vmin, "vmax", vmax)

            l1 = abs(pos - vmin) / interval
            vmin = vmin + l1 * delta
            vmax = vmax - (1.0 - l1) * delta

            if self.right_button_pressed:
                event.inaxes.set_ylim(ymin=vmin, ymax=vmax)
            else:
                event.inaxes.set_xlim(xmin=vmin, xmax=vmax)

            if event.inaxes.stream:
                event.inaxes.stream.on_zoomed()

            event.canvas.draw()

            #print(event.inaxes.xaxis.get_view_interval(), event.ydata, event.button, event.key)
        pass

    def button_release(self, event):
        #print('button release', event.button, event.xdata)
        if event.button == 2:
            if event.inaxes and event.inaxes.links:
                event.inaxes.links.open(event)


    def key_release(self, event):
        if not event.key:
            self.right_button_pressed = False

    def key_press(self, event):

        if event.key == 'shift':
            self.right_button_pressed = True

        if event.inaxes and event.inaxes.stream:
            if event.key == 'h':
                event.inaxes.stream.scale_to_default()
            elif event.key == ' ':
                event.inaxes.links.open(event)


def event_loop():
    plt.show()


