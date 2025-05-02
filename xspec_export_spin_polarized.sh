#!/bin/bash
set -e

CASE_NAME="CoFeMnPlusU"

START_ATOM=1
STOP_ATOM=32

EXPORT_DIR="xspec_export"
ABS_FILE_TEMPLATE="CoFeMnPlusU_O!atom!_ABS_GS"
EMIS_FILE_TEMPLATE="CoFeMnPlusU_O!atom!_EMIS_GS"
ORBITAL="1S"

# create export directory if not already existing
mkdir -p $EXPORT_DIR

# Find and separate all of the binding energies for the system
BINDING_FILE="binding_energies"
FERMI_FILE="fermi_energy"

: > "${EXPORT_DIR}/${BINDING_FILE}up.txt"
awk "/:$ORBITAL/ {print}" "$CASE_NAME".scfcup | tr "-" "\n" | tr "Ry" "\n" | awk "NR%2==0" | awk "NR%2!=0" >> "${EXPORT_DIR}/${BINDING_FILE}up.txt"
: > "${EXPORT_DIR}/${BINDING_FILE}dn.txt"
awk "/:$ORBITAL/ {print}" "$CASE_NAME".scfcdn | tr "-" "\n" | tr "Ry" "\n" | awk "NR%2==0" | awk "NR%2!=0" >> "${EXPORT_DIR}/${BINDING_FILE}dn.txt"

: > "${EXPORT_DIR}/${FERMI_FILE}up.txt"
awk '/:FER/ {print}' "$CASE_NAME".scf2up | tr "=" "\n" | awk "NR%2==0" >> "${EXPORT_DIR}/${FERMI_FILE}up.txt"
: > "${EXPORT_DIR}/${FERMI_FILE}dn.txt"
awk '/:FER/ {print}' "$CASE_NAME".scf2dn | tr "=" "\n" | awk "NR%2==0" >> "${EXPORT_DIR}/${FERMI_FILE}dn.txt"

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
        x xspec -up
        cp "${CASE_NAME}.xspecup" "${EXPORT_DIR}/${EMIS_FILE_TEMPLATE/!atom!/$ATOM}.xspecup"
        cp "${CASE_NAME}.txspecup" "${EXPORT_DIR}/${EMIS_FILE_TEMPLATE/!atom!/$ATOM}.txspecup"

        x xspec -dn
        cp "${CASE_NAME}.xspecdn" "${EXPORT_DIR}/${EMIS_FILE_TEMPLATE/!atom!/$ATOM}.xspecdn"
        cp "${CASE_NAME}.txspecdn" "${EXPORT_DIR}/${EMIS_FILE_TEMPLATE/!atom!/$ATOM}.txspecdn"

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
   	x xspec -up
    cp "${CASE_NAME}.xspecup" "${EXPORT_DIR}/${ABS_FILE_TEMPLATE/!atom!/$ATOM}.xspecup"
    cp "${CASE_NAME}.txspecup" "${EXPORT_DIR}/${ABS_FILE_TEMPLATE/!atom!/$ATOM}.txspecup"

   	x xspec -dn
    cp "${CASE_NAME}.xspecdn" "${EXPORT_DIR}/${ABS_FILE_TEMPLATE/!atom!/$ATOM}.xspecdn"
    cp "${CASE_NAME}.txspecdn" "${EXPORT_DIR}/${ABS_FILE_TEMPLATE/!atom!/$ATOM}.txspecdn"
done

exit 0

