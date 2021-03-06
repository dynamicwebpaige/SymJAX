import os
import pickle,gzip
import urllib.request
import numpy as np
import time
import tarfile
from tqdm import tqdm
from scipy.io.wavfile import read as wav_read

class urban:
    """urban sound classification

    Reference at https://zenodo.org/record/3233082 

    Description

    SONYC Urban Sound Tagging (SONYC-UST) is a dataset for the development and
    evaluation of machine listening systems for realistic urban noise
    monitoring. The audio was recorded from the SONYC acoustic sensor network.
    Volunteers on the Zooniverse citizen science platform tagged the presence
    of 23 classes that were chosen in consultation with the New York City
    Department of Environmental Protection. These 23 fine-grained classes can be
    grouped into 8 coarse-grained classes. The recordings are split into three
    subsets: training, validation, and test. These sets are disjoint with
    respect to the sensor from which each recording came. For increased
    reliability, three volunteers annotated each recording, and members of the
    SONYC team subsequently created a set of ground-truth tags for the
    validation set using a two-stage annotation procedure in which two
    annotators independently tagged and then collectively resolved any
    disagreements. For more details on the motivation and creation of this
    dataset see the DCASE 2019 Urban Sound Tagging Task website.

    Audio data
    
    The provided audio has been acquired using the SONYC acoustic sensor network 
    for urban noise pollution monitoring. Over 50 different sensors have been
    deployed in New York City, and these sensors have collectively gathered the
    equivalent of 37 years of audio data, of which we provide a small subset.
    The data was sampled by selecting the nearest neighbors on VGGish features
    of recordings known to have classes of interest. All recordings are 10
    seconds and were recorded with identical microphones at identical gain
    settings. To maintain privacy, the recordings in this release have been
    distributed in time and location, and the time and location of the
    recordings are not included in the metadata.

    """
    def download(path):
    
        # Check if directory exists
        if not os.path.isdir(path+'ust'):
            print('Creating mnist Directory')
            os.mkdir(path+'ust')
    
        url = 'https://zenodo.org/record/3233082/files/audio-dev.tar.gz?download=1'
        # Check if file exists
        if not os.path.exists(path+'ust/audio-dev.tar.gz'):
            td  = time.time()
            urllib.request.urlretrieve(url, path+'ust/audio-dev.tar.gz')
    
        url = 'https://zenodo.org/record/3233082/files/annotations-dev.csv?download=1'
        # Check if file exists
        if not os.path.exists(path+'ust/annotations-dev.csv'):
            td  = time.time()
            urllib.request.urlretrieve(url, path+'ust/annotations-dev.csv')
    
    
    
    
    def load(path=None, classes=range(10)):
    
        if path is None:
            path = os.environ['DATASET_PATH']
        download(path)
    
        t0 = time.time()
    
        # Loading the file
        files = tarfile.open(path+'ust/audio-dev.tar.gz', 'r:gz')
        annotations = np.loadtxt(path+'ust/annotations-dev.csv', delimiter=',',
                                 skiprows=1, dtype='str')
    
        # get name
        filenames = list(annotations[:, 2])
        for i in range(len(filenames)):
            filenames[i] = annotations[i, 0] + '/' + str(filenames[i])
    
        # get fine labels and limts for coarse classes
        fine_labels = annotations[:, 4: 33].astype('float32').astype('int32')
        class_limits = [0, 4, 9, 10, 14, 19, 23, 28, 29]
        n_classes = len(class_limits) - 1
        n_samples = len(annotations)
        llabels = np.zeros((n_samples, n_classes), dtype='int')
        for k in range(n_classes):
            block = fine_labels[:, class_limits[k]: class_limits[k+1]]
            block = block.astype('float32').astype('int32')
            llabels[:, k] = block.max(1)
    
        POT = []
        wavs = np.zeros((2794, 441000))
        labels = np.zeros((2794, n_classes)).astype('int')
        filenames = files.getnames()
        cpt = 0
        for name in tqdm(filenames, ascii=True):
            if '.wav' not in name:
                continue
            wav = wav_read(files.extractfile(name))[1].astype('float32')
            wavs[cpt, :len(wav)] = wav
            labels[cpt] = llabels[filenames.index(name)]
            cpt += 1
        return wavs, labels
