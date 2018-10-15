import pandas as pd
import argparse
import sys
import os
from shutil import copyfile
import time

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
    # This is tied to minc-toolkit version that's baked into the container
    MINC_ENV = '/opt/minc/1.9.16/minc-toolkit-config.sh' 
    subject_pipeline_list = []
    subject_list_dir_basename = os.path.basename(subject_list_dir)
    for subx in sub_list:
        subx_script = os.path.join(subject_list_dir, subx, 'run_preproc.sh')
        subject_pipeline_list.append(subx_script)
        subx_list_file = 'data/{}/{}/subject.list'.format(subject_list_dir_basename,subx)
        subx_out_dir = 'data/{}/{}/proc_output'.format(subject_list_dir_basename,subx)
        env_cmd ='#!/bin/bash\nsource {}\n'.format(MINC_ENV)
	pipeline_cmd = 'python -m scoop nist_mni_pipelines/iplLongitudinalPipeline.py -l {} -o {} -L -D \
        --model-dir={} --model-name={} --beast-dir={}\n'.format(subx_list_file,subx_out_dir,model_dir,model_name,beast_dir)
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
        subx_cmd = 'singularity exec --pwd /home/nistmni -B /data/ipl/scratch03/nikhil/containers/test_data:/home/nistmni/data \
        /data/ipl/scratch03/nikhil/containers/minc-tools-docker-v2.simg data/{}/{}/run_preproc.sh\n'.format(subject_list_dir_basename, subx) 
        with open(subx_script, "a") as myfile:
            myfile.write(subx_cmd)
	os.chmod(subx_script, 0o755)
    print('created {} job scripts at {}'.format(len(sub_list),subject_list_dir))
    return subject_Qjob_list

def submit_HCP_jobs(job_list):
    """ submits HPC jobs on BIC cluster
    """
    print('Submitting jobs to the queue...')
    msg = ''

    try:    
        for j in job_list:
            qsub_cmd = 'qsub -j y -cwd -V -l h_vmem=10G -o out.log {}/qsub_script_header'.format(j)
            q_status = subprocess.check_output(qsub_cmd, shell=True)
            time.sleep(1) 

        msg = 'success'
    except:
        msg = 'job submission failed'
    
    return q 


# argparse
parser = argparse.ArgumentParser(description = 'Code for creating subject-specifc MR scan (timepoints) jobs for HPC')
parser.add_argument('--master_list', required=True, help='List of all subjects. \
Note that the path needs to be either relative from the mounted directory or absolute within the container.')
parser.add_argument('--model_dir', required=True, help='Directory for anatomical models, e.g. icbm152. \
Note that the path needs to be either relative from the mounted directory or absolute within the container.')
parser.add_argument('--model_name', required=True, help='Name of the model, e.g. mni_icbm152_t1_tal_nlin_sym_09c')
parser.add_argument('--beast_dir', required=True, help='Directory for BEAST templates. \
Note that the path needs to be either relative from the mounted directory or absolute within the container.')
parser.add_argument('--submit_jobs', required=True, help='If true, submit jobs to the HPC. If false, only creates the job list.')

args = parser.parse_args()

# req params    
master_list_file = args.master_list
model_dir = args.model_dir #'/opt/minc/share/icbm152_model_09c'
model_name = args.model_name #'mni_icbm152_t1_tal_nlin_sym_09c'
beast_dir = args.beast_dir #'/opt/minc/share/beast-library-1.1'
submit_jobs = args.submit_jobs

# create subject specific lists from a master list
working_dir = os.path.dirname(master_list_file)
subject_list_dir = os.path.join(working_dir,'subject_dirs')
if not os.path.exists(subject_list_dir):
    os.mkdir(subject_list_dir)
sub_list = create_subject_lists(master_list_file,subject_list_dir)

# creare subject specific pipleline script
subject_pipeline_list = create_pipeline_scripts(subject_list_dir,sub_list,model_dir,model_name,beast_dir)

# create subject specific job submission scripts
subject_Qjob_list = create_Qjob_scripts('qsub_script_header', subject_list_dir, sub_list)
print(subject_Qjob_list)

if submit_jobs:
    q = submit_HCP_jobs(subject_Qjob_list)
    print(q)
