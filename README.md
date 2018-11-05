# Neuro_Containers
## Description
- Containers for preprocessing pipelines 

## Containers
- Docker: general purpose containerized snapshots of 1) Minc-tools 2) preproc pipeline (e.g. ipl_longitudinal) 3) other packages (e.g. pyminc) 
- Singularity: Converted from Docker image to run on HPC cluster at BIC (not uploaded on here) 

## Workflow 
- see preproc_pipeline* images for implementation details

## Directories
 - docker: Dockerfiles 
 - scripts: code for preparing HPC job submission with new workflow

## Usage requirements
 - host directory comprising all images 
 - list of all subjects-scans in following format (subject.list): 
 
 ```
subject04,1,input/subject04_1_t1w.mnc.gz,,,Male,50
subject04,2,input/subject04_2_t1w.mnc.gz,,,Male,51
subject04,3,input/subject04_3_t1w.mnc.gz,,,Male,52
subject05,1,input/subject05_1_t1w.mnc.gz,,,Male,56
subject05,2,input/subject05_2_t1w.mnc.gz,,,Male,57
 ```
 
 ## Useful paths
 - container home: /home/nistmni
 - container data-mount: /home/nistmni/data
 
 ## Usage 
 - run the "scripts/prepare_HPC_jobs.py". See sample command below: 
 ```
 python prepare_HPC_jobs.py --master_list /data/ipl/scratch03/nikhil/containers/3subjects/subject.list \
 --mount_dir /data/ipl/scratch03/nikhil/containers/3subjects \
 --model_dir /opt/minc/share/icbm152_model_09c \
 --model_name mni_icbm152_t1_tal_nlin_sym_09c \
 --beast_dir /opt/minc/share/beast-library-1.1
 ```
 
-  Note that the model_dir and beast_dir can be external to container and can mounted from host. However make sure you provide absolute path with reference to the container. For example: 
```
--model_dir home/nistmni/data/my_model_dir
--model_name my_model
--beast_dir home/nistmni/data/my_beast_dir
```

- prepare_HPC_jobs.py script creates a single list qsub jobs at the mount-point:
```
/data/ipl/scratch03/nikhil/containers/3subjects/all_qsub_jobs.sh:

qsub -j y -cwd -V -l h_vmem=10G -o out.log /data/ipl/scratch03/nikhil/containers/3subjects/subject_dirs/subject05/qsub_script_header
qsub -j y -cwd -V -l h_vmem=10G -o out.log /data/ipl/scratch03/nikhil/containers/3subjects/subject_dirs/subject04/qsub_script_header
qsub -j y -cwd -V -l h_vmem=10G -o out.log /data/ipl/scratch03/nikhil/containers/3subjects/subject_dirs/subject06/qsub_script_header
```
These jobs can be submitted to the queue with:
```
bash /data/ipl/scratch03/nikhil/containers/3subjects/all_qsub_jobs.sh
```
 
