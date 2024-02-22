import matplotlib.pyplot as plt


class LazyPlotter(object):
    def apply(self, figure:plt.Figure, axes:plt.Axes):
        raise NotImplementedError

    def __add__(self, other):
        return SequenceDualPlotter(self,other)

    def make_plot(self, figsize):
        figure:plt.Figure
        axes:plt.Axes
        figure, axes = plt.subplots(figsize=figsize)
        self.apply(figure,axes)
        return figure,axes

class SequenceDualPlotter(LazyPlotter):
    def __init__(self,a:LazyPlotter,b:LazyPlotter):
        self.a = a
        self.b = b

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        self.a.apply(figure,axes)
        self.b.apply(figure,axes)