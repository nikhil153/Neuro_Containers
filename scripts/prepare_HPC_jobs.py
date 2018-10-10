import pandas as pd
import argparse
import sys
import os

def create_subject_lists(f):
    subject_list_dir = os.path.join(os.path.dirname(f),'sub_lists')
    if not os.path.exists(subject_list_dir):
        os.mkdir(subject_list_dir)

    master_df = pd.read_csv(f,sep=',',header=None)
    other_cols = []
    for i in range(len(master_df)-1):
        other_cols.append('cols_{}'.format(i+2))

    master_df.columns = ['subject','tp'] + other_cols
    gb = master_df.groupby('subject')    

    file_list_check = False
    try: 
        for x in gb.groups:
            gb.get_group(x).to_csv('{}/{}.list'.format(subject_list_dir,x),header=False,index=False)

        print('subject specific lists created at: {}'.format(subject_list_dir))
        file_list_check = True
    except:
        print('Error creating files. Check permissions.')

    return file_list_check

# argparse
parser = argparse.ArgumentParser(description = 'Code for creating subject-specifc MR scan (timepoints) jobs for HPC')
parser.add_argument('--master_list', required=True, help='List of all subjects')

args = parser.parse_args()

# req params    
master_list_file = args.master_list

# create subject specific lists from a master list
file_list_check = create_subject_lists(master_list_file)
print('subject files created: {}'.format(file_list_check))