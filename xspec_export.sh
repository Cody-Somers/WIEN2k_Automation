#!/bin/bash
set -e

CASE_NAME="test"

START_ATOM=1
STOP_ATOM=32

EXPORT_DIR="xspec_export"
ABS_FILE_TEMPLATE="CoCrFeMnNi_O!atom!_ABS_GS"
EMIS_FILE_TEMPLATE="CoCrFeMnNi_O!atom!_EMIS_GS"
ORBITAL="1S"

# create export directory if not already existing
mkdir -p $EXPORT_DIR

# Find and separate all of the binding energies for the system
BINDING_FILE="binding_energies"
FERMI_FILE="fermi_energy"
: > "${EXPORT_DIR}/${BINDING_FILE}.txt"
awk "/:$ORBITAL/ {print}" "$CASE_NAME".scfc | tr "-" "\n" | tr "Ry" "\n" | awk "NR%2==0" | awk "NR%2!=0" >> "${EXPORT_DIR}/${BINDING_FILE}.txt"

: > "${EXPORT_DIR}/${FERMI_FILE}.txt"
awk '/:FER/ {print}' "$CASE_NAME".scf2 | tr "=" "\n" | awk "NR%2==0" >> "${EXPORT_DIR}/${FERMI_FILE}.txt"

for ATOM in $(seq $START_ATOM $STOP_ATOM)
        do
        #export EMIS spectrum
        cat > "${CASE_NAME}.inxs" <<- EOM
Title:
${ATOM}         (atom)
1               (n core)
0               (l core)
0,0.5,0.5	(split, Int1, Int2)
-30,0.02,10	 (EMIN,DE,EMAX in eV)
EMIS            (type of spectrum)
0.50            (S)
0.5             (gamma0)
1.00            (W only for EMIS)
AUTO            (AUTO or MANually select Energy ranges for broadening)
        -19.8600000000000
        -19.9200000000000
        -20.0000000000000
EOM
        x xspec
        cp "${CASE_NAME}.xspec" "${EXPORT_DIR}/${EMIS_FILE_TEMPLATE/!atom!/$ATOM}.xspec"
        cp "${CASE_NAME}.txspec" "${EXPORT_DIR}/${EMIS_FILE_TEMPLATE/!atom!/$ATOM}.txspec"

        #export ABS spectrum
        cat > "${CASE_NAME}.inxs" <<- EOM
Title:
${ATOM}         (atom)
1              (n core)
0               (l core)
0,0.5,0.5	(split, Int1, Int2)
-10,0.02,30	 (EMIN,DE,EMAX in eV)
ABS             (type of spectrum)
0.50            (S)
0.5             (gamma0)
1.00            (W only for EMIS)
AUTO            (AUTO or MANually select Energy ranges for broadening)
        -19.8600000000000
        -19.9200000000000
        -20.0000000000000
EOM
   	x xspec
        cp "${CASE_NAME}.xspec" "${EXPORT_DIR}/${ABS_FILE_TEMPLATE/!atom!/$ATOM}.xspec"
        cp "${CASE_NAME}.txspec" "${EXPORT_DIR}/${ABS_FILE_TEMPLATE/!atom!/$ATOM}.txspec"
done

exit 0

