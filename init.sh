#!/bin/sh

WORK_DIR=/home/jovyan/work
CLONE_DIR=${WORK_DIR}/matchSIRET

# Clone course repository
REPO_URL=https://github.com/etalab/matchSIRET.git
git clone --depth 1 $REPO_URL $CLONE_DIR

# Put RFPE data in the working dir
cd ${WORK_DIR}

mc cp s3/projet-funathon/diffusion/rfpe.zip rfpe.zip # Avec l'user root

unzip rfpe.zip

# Install additional packages if needed
REQUIREMENTS_FILE=${CLONE_DIR}/requirements.txt
[ -f $REQUIREMENTS_FILE ] && pip install -r $REQUIREMENTS_FILE && rm $REQUIREMENTS_FILE

# Remove course Git repository
#rm -r $CLONE_DIR

chown jovyan -R /home/jovyan/ # Sinon jovyan n'a plus les droits
