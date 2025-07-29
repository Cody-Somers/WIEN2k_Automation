#!/bin/bash
set -e

case_name="800Fm3m"
atom_list=(1 2 3 16 40) # In xspec_config we have odd number positions
orbital_list=("2p" "2p" "2p" "1s" "1s") # In xspec_config we have even number positions
spin_polarized="False"

ABS_FILE_TEMPLATE="CoCrFeMnNi_O!atom!_ABS_GS"
EMIS_FILE_TEMPLATE="CoCrFeMnNi_O!atom!_EMIS_GS"

fermi_file="fermi_energy"

##########
# END of user parameters
edge_arr=("1s" "2s" "2p" "3s" "3p" "3d" "4s" "4p" "4d" "4f")
n_arr=(1 2 2 3 3 3 4 4 4 4)
l_arr=(0 0 1 0 1 2 0 1 2 3)

export_dir="xspec_export"

# create export directory if not already existing
mkdir -p $export_dir

# Find and separate all of the binding energies for the system
#BINDING_FILE="binding_energies"
# 1.ATOM # TODO: Fix the format to get binding energies for different edges. Maybe leave for python h5
# :1S, 2P, 2PP, 3D, 3DD
#: > "${export_dir}/${BINDING_FILE}.txt"
#awk "/:$ORBITAL/ {print}" "$case_name".scfc | tr "-" "\n" | tr "Ry" "\n" | awk "NR%2==0" | awk "NR%2!=0" >> "${export_dir}/${BINDING_FILE}.txt"


if [[ "${spin_polarized}" == "True" ]]; then
  : > "${export_dir}/${fermi_file}up.txt"
  awk '/:FER/ {print}' "$case_name".scf2up | tr "=" "\n" | awk "NR%2==0" >> "${export_dir}/${fermi_file}up.txt"
  : > "${export_dir}/${fermi_file}dn.txt"
  awk '/:FER/ {print}' "$case_name".scf2dn | tr "=" "\n" | awk "NR%2==0" >> "${export_dir}/${fermi_file}dn.txt"
else
  : > "${export_dir}/${fermi_file}.txt"
  awk '/:FER/ {print}' "$case_name".scf2 | tr "=" "\n" | awk "NR%2==0" >> "${export_dir}/${fermi_file}.txt"
fi

for atom_index in "${!atom_list[@]}"; do
  # Get the edge that we care about
  edge_index=999 # value that means it was not assigned properly
  for i in "${!edge_arr[@]}"; do # The ! is to get the key, without that it just returns the value instead
    # echo "For each i value: Index: $i, value: ${edge_arr[i]}"
    if [[ "${edge_arr[i]}" == "${orbital_list[${atom_index}]}" ]]; then
      # echo "Index: $i, value: ${edge_arr[i]}"
      edge_index=$i
      break
    fi
  done
  if [[ "$edge_index" == 999 ]]; then
    echo "Error in edge assignment"
    exit 1
  fi
  echo "Atom: ${atom_list[atom_index]} and Edge: ${orbital_list[${atom_index}]}"

  #export EMIS spectrum
  cat > "${case_name}.inxs" <<- EOM
Title:
${atom_list[atom_index]}         (atom)
${n_arr[edge_index]}               (n core)
${l_arr[edge_index]}               (l core)
0,0.5,0.5	(split, Int1, Int2)
-50,0.02,10	 (EMIN,DE,EMAX in eV)
EMIS            (type of spectrum)
0.50            (S)
0.5             (gamma0)
1.00            (W only for EMIS)
AUTO            (AUTO or MANually select Energy ranges for broadening)
        -19.8600000000000
        -19.9200000000000
        -20.0000000000000
EOM
  if [[ "${spin_polarized}" == "True" ]]; then
    x xspec -up
    cp "${case_name}.xspecup" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecup"
    cp "${case_name}.txspecup" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecup"

    x xspec -dn
    cp "${case_name}.xspecdn" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecdn"
    cp "${case_name}.txspecdn" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecdn"
  else
    x xspec
    cp "${case_name}.xspec" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspec"
    cp "${case_name}.txspec" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspec"
  fi

  #export ABS spectrum
  cat > "${case_name}.inxs" <<- EOM
Title:
${atom_list[atom_index]}         (atom)
${n_arr[edge_index]}              (n core)
${l_arr[edge_index]}               (l core)
0,0.5,0.5	(split, Int1, Int2)
-10,0.02,50	 (EMIN,DE,EMAX in eV)
ABS             (type of spectrum)
0.50            (S)
0.5             (gamma0)
1.00            (W only for EMIS)
AUTO            (AUTO or MANually select Energy ranges for broadening)
        -19.8600000000000
        -19.9200000000000
        -20.0000000000000
EOM
  if [[ "${spin_polarized}" == "True" ]]; then
    x xspec -up
    cp "${case_name}.xspecup" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecup"
    cp "${case_name}.txspecup" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecup"

   	x xspec -dn
    cp "${case_name}.xspecdn" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecdn"
    cp "${case_name}.txspecdn" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecdn"
  else
    x xspec
    cp "${case_name}.xspec" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspec"
    cp "${case_name}.txspec" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspec"
  fi
done

exit 0

