import numpy as np
import numba as nb
from scipy.special import lambertw

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.node_processing import Node,ARRAY,SIGNAL

# Constants
# DT = 2500 #Основное временное разрешение в нс
# WT = 0.86   #Прозрачность входного окна
# LT = 0.93    #Прозрачность линзы
# A = 1      #Индекс начала отрезка
# B = 100     #Индекс конца отрезка
# PIX_FOV = (2.88/160)**2  #Поле зрения пикселя в стеррадианах
# S = np.pi*25/4 #Площадь входного окна в см^2
# N_CH = 256  #Число каналов в расчет lightcurvesum_global_cor
# #N=240400;
# T = 0.001  #Time sample в секундах
# NTS = T/DT*10**9
# CR_TO_INT = 1/(WT*LT*PIX_FOV*S*T) # Коэффициент перевода Count Rate --> Intensity
#

# Function lambertw is not supported by numba_scipy.
# Used solution https://habr.com/ru/articles/665634/
@nb.njit()
def lambert_w0(x):
    left = -1
    right = x if x <= np.e else np.log(x)
    prec = 10**-8 # precision
    # binary search
    while right - left > prec:
        mid = (right + left) / 2
        if mid * np.exp(mid) > x:
            right = mid
        else:
            left = mid
    return right

@nb.njit()
def flatfield(pdm_2d_rot_global:np.ndarray, eff,tau, dt, cr_to_int, nts):
    res = np.empty(pdm_2d_rot_global.shape)
    for i in range(pdm_2d_rot_global.shape[0]):
        for j in range(pdm_2d_rot_global.shape[1]):
            for k in range(pdm_2d_rot_global.shape[2]):

                if eff[j,k]>0:
                    b = tau[j, k] * eff[j, k] / dt
                    larg = -b * pdm_2d_rot_global[i,j,k]/nts/eff[j,k]
                    res[i,j,k] = -cr_to_int*nts*lambert_w0(larg).real/b
                else:
                    res[i,j,k] = 0.0
    return res

class LazyFFPhysicalSignal(LazyArrayOperation):
    def __init__(self, source, eff, tau, dt, cr_to_int, nts):
        self.source = source
        self.tau = tau.request_all_data().astype(float)
        self.eff = eff.request_all_data().astype(float)
        self.dt = dt
        self.cr_to_int = cr_to_int
        self.nts = nts
        #self.divider = divider.request_all_data().astype(float)
        assert self.tau.shape == self.eff.shape == source.shape()[1:]

    def shape(self):
        return self.source.shape()

    def request_single(self,i:int):
        return self.request_slice(slice(i,i+1))[0]

    def request_slice(self,s:slice):
        src_slice = self.source.request_data(s).astype(float)
        return flatfield(src_slice,self.eff,self.tau, self.dt, self.cr_to_int, self.nts)

class PhysicalFlatFieldingNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "tau":ARRAY,
        "eff":ARRAY
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    CONSTANTS = {
        "dt": 2500, #Основное временное разрешение в нс
        "wt": 0.86,  # Прозрачность входного окна
        "lt": 0.93, #Прозрачность линзы
        "pix_fov": (2.88 / 160) ** 2,  # Поле зрения пикселя в стеррадианах
        "s": np.pi * 25 / 4,  # Площадь входного окна в см^2
        "t": 0.001,  # Time sample в секундах
    }
    REPR_LABEL = "Pile up flat fielding"
    LOCATION = "/Flat fielding/Pile up flat fielding"

    def calculate(self,globalspace:dict) ->dict:
        signal = self.require("signal")
        tau = self.require("tau")
        eff = self.require("eff")
        spatial = signal.space

        dt = self.constants["dt"]
        t = self.constants["t"]
        pix_fov = self.constants["pix_fov"]
        s = self.constants["s"]
        wt = self.constants["wt"]
        lt = self.constants["lt"]

        nts = t/dt*10**9
        cr_to_int = 1 / (wt * lt * pix_fov * s * t)  # Коэффициент перевода Count Rate --> Intensity

        new_spatial = LazyFFPhysicalSignal(spatial,eff,tau,dt,cr_to_int,nts)
        new_signal = signal.clone()
        new_signal.space = new_spatial
        return dict(signal=new_signal)