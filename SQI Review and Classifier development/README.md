# SQI Review and Classifier development

## How to use Annotation Tool:

### External Python Libraries required :

* numpy
* pandas
* PyQt5
* pyqtgraph

### Running

NOTE: PPG signal segments must be formatted in a Pickle file in which each column vector is a sample to be annotated and is of equal length.
To run type "python3 Annotation_GUI.py" input the sampling rate and sample length.

## How to conduct SQI Review and Classifier Development

### External Python Libraries required :

* jupyter
* natsort
* scipy
* PyQT
* pyqtgraph
* sklearn
* tqdm


### Running

* Open Jupyter notebook by typing "jupyter notebook" within a terminal located within this directory
* To run PPG signal segment pre-processing and SQI extraction open "Importing processing and SQI extraction.ipynb"
* To run a SQI review open "SQI Review.ipynb"
* To run an invesitigation into optimal linear classifiers using Skewness and MSQ scores and to extract custom thresholds open "
Classifier Development.ipynb"

NOTE: the contents of these files allow for the validation of the findings from the report attached using the data and annotations collected.
To validate the findings of this report by reconducting annotation using the Annotation tool or to extract custom thresholds for a specific
dataset, modifications must be made in the files mentioned above to allow for the new files to be imported and incorperated
