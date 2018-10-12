import pandas as pd
import argparse
import sys
import os
from shutil import copyfile

def create_subject_lists(f,subject_list_dir):
    master_df = pd.read_csv(f,sep=',',header=None)
    other_cols = []
    for i in range(len(master_df.columns)-2):
        other_cols.append('cols_{}'.format(i+2))
    master_df.columns = ['subject','tp'] + other_cols
    gb = master_df.groupby('subject')    

    sub_list = []
    try: 
        for x in gb.groups:
            subx_dir = os.path.join(subject_list_dir,x)
            if not os.path.exists(subx_dir):
                os.mkdir(subx_dir)
            subx_file = os.path.join(subx_dir, 'subject.list')
            sub_list.append(x)
            gb.get_group(x).to_csv(subx_file, header=False, index=False)

        print('subject specific lists created at: {}'.format(subject_list_dir))
    except:
        print('Error creating files. Check permissions.')

    return sub_list

def create_pipeline_scripts(subx_list_dir,sub_list,model_dir,model_name,beast_dir):
    subject_pipeline_list = []
    subject_list_dir_basename = os.path.basename(subject_list_dir)
    for subx in sub_list:
        subx_script = os.path.join(subject_list_dir, subx, 'run_preproc.sh')
        subject_pipeline_list.append(subx_script)
        subx_list = 'data/{}/{}/subject.list'.format(subject_list_dir_basename,subx)
        subx_out_dir = 'data/{}/{}/proc_output'.format(subject_list_dir_basename,subx)
        env_cmd ='#!/bin/bash\nsource /opt/minc/1.9.16/minc-toolkit-config.sh\n'
	pipeline_cmd = 'python -m scoop nist_mni_pipelines/iplLongitudinalPipeline.py -l {} -o {} -L -D --model-dir={} --model-name={} --beast-dir={}\n'.format(subx_list,subx_out_dir,model_dir,model_name,beast_dir)
        with open(subx_script, "w") as myfile:
	    myfile.write(env_cmd)
            myfile.write(pipeline_cmd)
        os.chmod(subx_script, 0o755)
    print('created {} pipeline run scripts at {}'.format(len(sub_list),subject_list_dir))
    return subject_pipeline_list

def create_Qjob_scripts(q_script_header,subject_list_dir,sub_list):
    subject_Qjob_list = []
    subject_list_dir_basename = os.path.basename(subject_list_dir)
    for subx in sub_list:
        subx_script = os.path.join(subject_list_dir, subx, q_script_header)
        subject_Qjob_list.append(subx_script)
        copyfile(q_script_header, subx_script)
        subx_cmd = 'singularity exec --pwd /home/nistmni -B /data/ipl/scratch03/nikhil/containers/test_data:/home/nistmni/data /data/ipl/scratch03/nikhil/containers/minc-tools-docker-v2.simg data/{}/{}/run_preproc.sh\n'.format(subject_list_dir_basename, subx) 
        with open(subx_script, "a") as myfile:
            myfile.write(subx_cmd)
	os.chmod(subx_script, 0o755)
    print('created {} job scripts at {}'.format(len(sub_list),subject_list_dir))
    return subject_Qjob_list

# argparse
parser = argparse.ArgumentParser(description = 'Code for creating subject-specifc MR scan (timepoints) jobs for HPC')
parser.add_argument('--master_list', required=True, help='List of all subjects')

args = parser.parse_args()

# req params    
master_list_file = args.master_list

# create subject specific lists from a master list
working_dir = os.path.dirname(master_list_file)
subject_list_dir = os.path.join(working_dir,'subject_dirs')
if not os.path.exists(subject_list_dir):
    os.mkdir(subject_list_dir)
sub_list = create_subject_lists(master_list_file,subject_list_dir)

# creare subject specific pipleline script
model_dir = '/opt/minc/share/icbm152_model_09c'
model_name = 'mni_icbm152_t1_tal_nlin_sym_09c'
beast_dir = '/opt/minc/share/beast-library-1.1'
subject_pipeline_list = create_pipeline_scripts(subject_list_dir,sub_list,model_dir,model_name,beast_dir)

# create subject specific job submission scripts
subject_Qjob_list = create_Qjob_scripts('qsub_script_header', subject_list_dir, sub_list)

#TODO
# Use Dockerfile entrypoint to source env:
# source /opt/minc/1.9.16/minc-toolkit-config.sh
# Mount single input data dir + template dir (read-only)
# Use customize subject_file names and output dirs for python pipeline command:
