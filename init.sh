#!/bin/sh

WORK_DIR=/home/onyxia/work
CLONE_DIR=${WORK_DIR}/matchSIRET

# Clone course repository
REPO_URL=git@github.com:etalab/matchSIRET.git
git clone --depth 1 $REPO_URL $CLONE_DIR

# Put RFPE data in the working dir
cd ${WORK_DIR}

#mc cp s3/projet-funathon/diffusion/rfpe.zip rfpe.zip # Avec l'user root
#unzip rfpe.zip

# Install additional packages if needed
REQUIREMENTS_FILE=${CLONE_DIR}/requirements.txt
[ -f $REQUIREMENTS_FILE ] && pip install -r $REQUIREMENTS_FILE && rm $REQUIREMENTS_FILE

cd $CLONE_DIR

chown onyxia -R /home/onyxia/ # Sinon onyxia n'a plus les droits
