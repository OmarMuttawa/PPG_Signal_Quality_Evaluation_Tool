from scipy.stats import skew
import numpy as np
from scipy import signal as s
import numpy as np
from numpy import NaN, Inf, arange, isscalar, asarray, array
from scipy import signal
# Functions Required for SQI Extraction
from scipy.stats import kurtosis,entropy
## Perfusion

def perfusion(filtered_signal):
    return abs(np.max(filtered_signal)-np.min(filtered_signal))/abs(np.mean(filtered_signal))*100.0

## Skewness

def skew1(signal):
    return skew(signal)

## Kurtosis
### Imported

## Entropy
### Imported

## Zero crossing rate

def cross_zero(detrended_signal):
    zero_crossings = len(np.where(np.diff(np.sign(detrended_signal)))[0])/len(detrended_signal)
    return zero_crossings

## Signal-to-noise ratio

def noise_ratio(filtered_signal):
    return np.var(filtered_signal)/np.var(abs(filtered_signal))

## Matching of multiple systolic wave detection algorithms

def billauer_peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    """
    maxtab = []
    mintab = []

    if x is None:
        x = np.arange(len(v))

    v = np.asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in np.arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append(mxpos)
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append(mnpos)
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab) , array(mintab)


def scipy_find_peaks(sig,height=None,threshold=None,distance=None):
    return signal.find_peaks(sig,height=height,threshold=threshold,distance=distance)

def get_msq(detrended_signal,d=0.4,h=21):
    peaks_1,_=scipy_find_peaks(detrended_signal,distance=h)
    peaks_2,_=billauer_peakdet(detrended_signal,d)
#     print(peaks_1)
#     print(peaks_2)
    if len(peaks_1)==0:
        return 0.0
    return len(np.intersect1d(peaks_1,peaks_2))/len(peaks_1)

# Relative Power

def relative_power(filtered_signal):
    f,PSD = signal.welch(filtered_signal,125,nperseg=len(filtered_signal))
    indices1 = [i for i in range(len(f)) if f[i]>=1.0 and f[i]<=2.4] # indices of PSD's 1 Hz to 2.25 Hz
    indices2 = [i for i in range(len(f)) if f[i]>=0 and f[i]<=8] #indices of PSDS from 0 Hz to 8 Hz
    return (PSD[indices1].sum()/PSD[indices2].sum())


# Per pulse variants of above SQIs

def mean_skew(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    
    n_segments = len(mins)-1
    skew_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        skew_scores.append(skew1(sig))
    return np.mean(skew_scores)

def mean_kurtosis(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    kurtosis_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        kurtosis_scores.append(kurtosis(sig))
    return np.mean(kurtosis_scores)

def mean_entropy(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    entropy_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        entropy_scores.append(entropy(sig))
    return np.mean(entropy_scores)

def mean_snr(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    snr_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        snr_scores.append(noise_ratio(sig))
    return np.mean(snr_scores)

def mean_relative_power(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    relative_powers=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        relative_powers.append(relative_power(sig))
    return np.mean(relative_powers)

def median_skew(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    skew_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        skew_scores.append(skew1(sig))
    return np.median(skew_scores)

def median_kurtosis(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    kurtosis_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        kurtosis_scores.append(kurtosis(sig))
    return np.median(kurtosis_scores)

def median_entropy(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    entropy_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        entropy_scores.append(entropy(sig))
    return np.median(entropy_scores)

def median_snr(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    snr_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        snr_scores.append(noise_ratio(sig))
    return np.median(snr_scores)

def median_relative_power(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    relative_powers=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        relative_powers.append(relative_power(sig))
    return np.median(relative_powers)

def std_skew(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    skew_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        skew_scores.append(skew1(sig))
    return np.std(skew_scores)

def std_kurtosis(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    kurtosis_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        kurtosis_scores.append(kurtosis(sig))
    return np.std(kurtosis_scores)

def std_entropy(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    entropy_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        entropy_scores.append(entropy(sig))
    return np.std(entropy_scores)

def std_snr(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    snr_scores=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        snr_scores.append(noise_ratio(sig))
    return np.std(snr_scores)

def std_relative_power(filtered_signal):
    _, mins = billauer_peakdet(filtered_signal,0.1)
    n_segments = len(mins)-1
    relative_powers=[]
    for i in range(n_segments):
        sig = filtered_signal[mins[i]:mins[i+1]]
        relative_powers.append(relative_power(sig))
    return np.std(relative_powers)


# Auto Correlation based SQIS

def acf(sig):
    return np.array([1]+[np.corrcoef(sig[:-i], sig[i:])[0,1] for i in range(1,len(sig))])

def first_acf_peak_loc(sig):
    corrs=acf(sig)
    peaks=scipy_find_peaks(corrs)
    if len(peaks[0])!=0:
        return peaks[0][0]
    else:
        return 0
    
def first_acf_peak_val(sig):
    corrs=acf(sig)
    peaks=scipy_find_peaks(corrs)
    if len(peaks[0])!=0:
        return corrs[peaks[0][0]]
    else:
        return 0
    
def second_acf_peak_loc(sig):
    corrs=acf(sig)
    peaks=scipy_find_peaks(corrs)
    if len(peaks[0])>=2:
        return peaks[0][1]
    else:
        return 0
def second_acf_peak_val(sig):
    corrs=acf(sig)
    peaks=scipy_find_peaks(corrs)
    if len(peaks[0])>=2:
        return corrs[peaks[0][1]]
    else:
        return 0

def notch_filt(signal,f0,fs=250.0,Q=60.0):
    # Design notch filter
    b, a = s.iirnotch(f0, Q, fs)
    # Filter signal
    filtered= s.filtfilt(b, a, signal)
    return filtered


def filter_down_scale(sig,b,a,fs):
    filtered = s.filtfilt(b, a,sig)
    if fs == 250:
        return scale_data(s.decimate(filtered,2,ftype="iir"))
    else:
        return scale_data(filtered)

def scale_data(sig):
    s_min = np.min(sig)
    s_max = np.max(sig)
    s_mean= np.mean(sig)
    std = (sig - s_min) / (s_max - s_min)
#     scaled = std * (s_max - s_min) + s_min
    return std

def predict_sample(sample,coefficients,intercepts):
    Class_0_Score=coefficients[0][0]*sample[0]+coefficients[0][1]*sample[1]+intercepts[0]
    Class_1_Score=coefficients[1][0]*sample[0]+coefficients[1][1]*sample[1]+intercepts[1]
    Class_2_Score=coefficients[2][0]*sample[0]+coefficients[2][1]*sample[1]+intercepts[2]
    Scores=[Class_0_Score,Class_1_Score,Class_2_Score]
    predicted_class=Scores.index(np.max(Scores))
    return predicted_class

def predict_set(X,coefficients,intercepts):
    predictions=[]
    for index in X.index:
        predictions.append(predict_sample(X.loc[index].values,coefficients,intercepts))
    return predictions

def filt(sig,b,a):
    # print("sig len: ",len(sig))
    # print("b: ",b)
    # print("a: ",a)
    return s.filtfilt(b,a,sig)

def filt_pipeline(sig,b,a,period=375):
    sig=s.resample(sig,period)
    sig=filt(sig,b,a)
    return scale_data(sig)

def detrend(sig):
    return s.detrend(sig)


def butter_bandpass(fs,lowcut=0.5, highcut=30, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = s.butter(order, [low, high], btype='band')
    return b, a

