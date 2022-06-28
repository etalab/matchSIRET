#!/bin/sh

WORK_DIR=/home/jovyan/work
CLONE_DIR=${WORK_DIR}/matchSIRET

# Clone course repository
REPO_URL=https://github.com/etalab/matchSIRET.git
git clone --depth 1 $REPO_URL $CLONE_DIR

# Put RFPE data in the working dir
mc cp s3/projet-funathon/diffusion/rfpe.zip ${WORK_DIR}/rfpe.zip
unzip rfpe.zip

# Install additional packages if needed
REQUIREMENTS_FILE=${FORMATION_DIR}/requirements.txt
[ -f $REQUIREMENTS_FILE ] && pip install -r $REQUIREMENTS_FILE && rm $REQUIREMENTS_FILE

# Remove course Git repository
#rm -r $CLONE_DIR
