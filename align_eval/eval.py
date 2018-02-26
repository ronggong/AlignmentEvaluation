'''
Created on Oct 10, 2017

@author: joro
'''


import sys
import os
import glob
import numpy as np
projDir = os.path.join(os.path.dirname(__file__), os.path.pardir)

if projDir not in sys.path:
    sys.path.append(projDir)

from align_eval.PercentageCorrectEvaluator import _evalPercentageCorrect
from align_eval.Utilz import load_labeled_intervals, getMeanAndStDevError,\
    writeCsv, load_delimited_variants, remove_dot_tokens
from parse.TextGrid_Parsing import tierAliases
from align_eval.ErrorEvaluator import _evalAlignmentError,\
    calc_percentage_tolerance




def load_detected_intervals(detected_URI):
    detected_starts, detected_ends, labels = load_delimited_variants(detected_URI)
    
    use_end_ts = False #  do not use end_ts even if detected
    if detected_ends is None:
        detected_ends = detected_starts # to keep format
    
    detected_starts, detected_ends, labels = remove_dot_tokens(detected_starts, detected_ends,  labels)
    
    detected_intervals = np.array([detected_starts, detected_ends]).T
    return detected_intervals, use_end_ts

def eval_all_metrics_lab(refs_URI, detected_URI, tolerance ):
    '''
    run all eval metrics on one file
    '''
    ref_intervals, ref_labels = load_labeled_intervals(refs_URI)
    
    detected_intervals, use_end_ts = load_detected_intervals(detected_URI)
    
    # # # # error     
    alignmentErrors = _evalAlignmentError(ref_intervals, detected_intervals, ref_labels, use_end_ts)
    mean, stDev, median = getMeanAndStDevError(alignmentErrors)

    ######### tolerance
    percentage_tolerance = calc_percentage_tolerance(alignmentErrors, tolerance) 
    
    
    ###### percentage correct
    initialTimeOffset_refs = ref_intervals[0][0]
    finalts_refs = ref_intervals[-1][1]
    durationCorrect, totalLength  = _evalPercentageCorrect(ref_intervals, detected_intervals, 
                                                  finalts_refs,  initialTimeOffset_refs, ref_labels )
    percentage_correct = durationCorrect / totalLength
    return median,  percentage_correct, percentage_tolerance


def main_eval_one_file(argv):
    if len(argv) != 4:
        sys.exit('usage: {} <URI reference word boundaries> <URI detected word boundaries> <tolerance> '.format(sys.argv[0]))
    refs_URI = argv[1]
    detected_URI = argv[2]
    tolerance = float(argv[3])
    print 'evaluating on {}'.format(refs_URI) 
    medianError, percentage, percentage_tolerance = eval_all_metrics_lab(refs_URI, detected_URI, tolerance)
    
    #     print "Alignment error mean : ", mean, "Alignment error median : ", median, "Alignment error st. dev: " , stDev
    print "Alignment error median", medianError
    print "percentage {0:0.2f} with tolerance {1}".format(percentage_tolerance, tolerance)
    
    return medianError, percentage, percentage_tolerance

def main_eval_all_files(argv):
    if len(argv) != 4:
        sys.exit('usage: {} <path dir with to reference word boundaries> <path to dir with detected word boundaries> <path_output>'.format(sys.argv[0]))
    refs_dir_URI = argv[1]
    detected_dir_URI = argv[2]
    a = os.path.join(detected_dir_URI, "*.lab")
    lab_files = glob.glob(a)
    
    results = [['Track', 'Average absolute error'    , 'Percentage of correct segments']]
    for lab_file in lab_files:
        base_name = os.path.basename(lab_file)
        
        ref_file = os.path.join(refs_dir_URI, base_name[:-4] + '.wordonset.tsv')
        mean, percentage = main_eval_one_file(["dummy",  ref_file, lab_file])
        results.append([base_name[:-4],'{:.3f}'.format(mean), '{:.3f}'.format(percentage)])
    output_URI = argv[3]
    writeCsv(os.path.join(output_URI, 'results.csv'), results)
    
if __name__ == '__main__':
    main_eval_one_file(sys.argv)
    # main_eval_all_files(sys.argv)