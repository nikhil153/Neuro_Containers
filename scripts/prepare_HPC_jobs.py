import pandas as pd
import argparse
import sys
import os
from shutil import copyfile
import time

# Global variables
# This is tied to minc-toolkit version that's baked into the container
# This should be updated based on changes in singularity container, i.e. minc-toolkit or proproc pipeline versions
MINC_TOOLKIT_VERSION = '1.9.16'
MINC_ENV = '/opt/minc/{}/minc-toolkit-config.sh'.format(MINC_TOOLKIT_VERSION) 
MINC_PIPELINE = '/home/nistmni/nist_mni_pipelines/iplLongitudinalPipeline.py'
S_CONTAINER = '/data/ipl/scratch03/nikhil/containers/minc-tools-docker-v2.simg' 
CONTAINER_DATA_DIR = '/home/nistmni/data'

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

        print('created {} subject specific lists at: {}'.format(len(gb.groups), subject_list_dir))
    except:
        print('Error creating files. Check permissions.')

    return sub_list

def create_pipeline_scripts(subject_list_dir,sub_list,model_dir,model_name,beast_dir):
    subject_pipeline_list = []
    subject_list_dir_basename = os.path.basename(subject_list_dir)
    for subx in sub_list:
        subx_script = os.path.join(subject_list_dir, subx, 'run_preproc.sh')
        subject_pipeline_list.append(subx_script)
        subx_list_file = '{}/{}/{}/subject.list'.format(CONTAINER_DATA_DIR,subject_list_dir_basename,subx)
        subx_out_dir = '{}/{}/{}/proc_output'.format(CONTAINER_DATA_DIR,subject_list_dir_basename,subx)
        env_cmd ='#!/bin/bash\nsource {}\n'.format(MINC_ENV)
        pipeline_cmd = 'python -m scoop {} -l {} -o {} -L -D --model-dir={} --model-name={} --beast-dir={}\n'.format(MINC_PIPELINE,subx_list_file,subx_out_dir,model_dir,model_name,beast_dir)
        with open(subx_script, "w") as myfile:
            myfile.write(env_cmd)
            myfile.write(pipeline_cmd)
        os.chmod(subx_script, 0o755)
    print('created {} pipeline run scripts at {}'.format(len(sub_list),subject_list_dir))
    return subject_pipeline_list

def create_Qjob_scripts(q_script_header,subject_list_dir,sub_list,mount_dir):
    subject_Qjob_list = []
    subject_list_dir_basename = os.path.basename(subject_list_dir)
    for subx in sub_list:
        subx_script = os.path.join(subject_list_dir, subx, q_script_header)
        subject_Qjob_list.append(subx_script)
        copyfile(q_script_header, subx_script)
        subx_cmd = 'singularity exec --pwd /home/nistmni -B {}:{} {} {}/{}/{}/run_preproc.sh\n'.format(mount_dir,CONTAINER_DATA_DIR,S_CONTAINER,CONTAINER_DATA_DIR,subject_list_dir_basename,subx) 

    with open(subx_script, "a") as myfile:
        myfile.write(subx_cmd)
 
    os.chmod(subx_script, 0o755)
    print('created {} job scripts at {}'.format(len(sub_list),subject_list_dir))
    return subject_Qjob_list

def create_qsub_list(subject_Qjob_list,qsub_list_file):
    """ Single list of HPC jobs on BIC cluster
    """
    qsub_cmd_list = []
    for job in subject_Qjob_list: 
        qsub_cmd = 'qsub -j y -cwd -V -l h_vmem=10G -o out.log {}\n'.format(job)
        qsub_cmd_list.append(qsub_cmd)

    with open(qsub_list_file, "w") as myfile:
        myfile.writelines(qsub_cmd_list) 


def main():
    # argparse
    parser = argparse.ArgumentParser(description = 'Code for creating subject-specifc MR scan (timepoints) jobs for HPC')
    parser.add_argument('--master_list', required=True, help='List of all subjects. \
    Note that the path needs to be either relative from the mounted directory or absolute within the container.')
    parser.add_argument('--mount_dir', required=True, help='Path to the host data dir to be mounted on the container')
    parser.add_argument('--model_dir', required=True, help='Directory for anatomical models, e.g. icbm152. \
    Note that the path needs to be either relative from the mounted directory or absolute within the container.')
    parser.add_argument('--model_name', required=True, help='Name of the model, e.g. mni_icbm152_t1_tal_nlin_sym_09c')
    parser.add_argument('--beast_dir', required=True, help='Directory for BEAST templates. \
    Note that the path needs to be either relative from the mounted directory or absolute within the container.')

    args = parser.parse_args()

    # req params    
    master_list_file = args.master_list
    mount_dir = args.mount_dir
    model_dir = args.model_dir #'/opt/minc/share/icbm152_model_09c'
    model_name = args.model_name #'mni_icbm152_t1_tal_nlin_sym_09c'
    beast_dir = args.beast_dir #'/opt/minc/share/beast-library-1.1'

    print('')
    print('This script prepares MR dataset for container based preprocessing. The script will create:  \n1) subject-specific directories, each comprising all timepoints per subject from the master_list \n2) ipl pipeline script for each of these directories \n3) qsub command for each of this directories.')
    print('')
    print('Using minc-toolkit version {}'.format(MINC_TOOLKIT_VERSION))

    # create subject specific lists from a master list
    print('\nCreating subject specific directories...')
    working_dir = os.path.dirname(master_list_file)
    subject_list_dir = os.path.join(working_dir,'subject_dirs')
    qsub_list_file = os.path.join(working_dir, 'all_qsub_jobs.sh')
    if not os.path.exists(subject_list_dir):
        os.mkdir(subject_list_dir)
    sub_list = create_subject_lists(master_list_file,subject_list_dir)

    # creare subject specific pipleline script
    print('\nCreating subject specific pipeline script...')
    subject_pipeline_list = create_pipeline_scripts(subject_list_dir,sub_list,model_dir,model_name,beast_dir)

    # create subject specific job submission scripts
    print('\nCreating subject specific qsub command...')
    subject_Qjob_list = create_Qjob_scripts('qsub_script_header', subject_list_dir, sub_list, mount_dir)
    create_qsub_list(subject_Qjob_list,qsub_list_file)
    print('\nTo submit jobs to the BIC cluster, run this script: {}'.format(qsub_list_file))

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
