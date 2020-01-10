
ROOT='/Users/ohamelijnck/Scripts/cluster'

while [[ $# -gt 0 ]]
do
   key="$1"

   case $key in
      --nodes)
         MAX_NODES=$2
         shift;
      ;;
      --time)
         TIME=$2
         shift;
      ;;
      --cpus)
         CPUS=$2
         shift;
      ;;
      --memory)
         MEMORY=$2
         shift;
      ;;
      --lib)
         LIB_FLAG=1
         LIB=$2
         LIBS+=("$LIB")
         shift;
      ;;
      --ip)
         IP=$2
         shift;
      ;;
      --ssh_key)
         SSH_KEY=$2
         shift;
      ;;
      --user)
         USER=$2
         shift;
      ;;
      --basename)
         BASENAME=$2
         shift;
      ;;
      --cluster_folder)
         CLUSTER_FOLDER=$2
         shift;
      ;;
      --slurm_file)
         SLURM_FILE=$2
         shift;
      ;;
      *)
         # unknown option
      ;;
   esac
shift # past argument or value
done

#ensure a results folder exists
mkdir -p results

TO_TAR="models data cluster/run.sh"

if [ "$LIB_FLAG" -eq "1" ]; then
   len=${#LIBS[@]}
   for (( i=0; i<$len; i++ )); do
      LIB="${LIBS[$i]}" ; 
      LIB_BASENAME=$(basename $LIB)
      echo "MOVING LIBRARY $LIB_BASENAME"
      TO_TAR="$TO_TAR $LIB"
   done
fi

#create folder for this specific run
TAR_NAME="cluster/$BASENAME.tar"
tar -czf "$TAR_NAME"  $TO_TAR


echo "$SSH_KEY" "$TAR_NAME" "$USER@$IP:" 
scp  -i "$SSH_KEY" "$TAR_NAME" "$USER@$IP:"


ssh  -i "$SSH_KEY" "$USER@$IP" -o StrictHostKeyChecking=no 'bash -s' << HERE
   mkdir $BASENAME
   tar -xzf $BASENAME.tar --directory $BASENAME --warning=none
   rm -rf $BASENAME.tar
   mkdir $BASENAME/cluster/logs
   mkdir $BASENAME/results
HERE


results=$(ssh  -i "$SSH_KEY" "$USER@$IP" -o StrictHostKeyChecking=no 'bash -s' << HERE
   sbatch $BASENAME/cluster/run.sh
HERE
)

JOB_ID=$(echo $results | awk '{print $NF}')

echo $JOB_ID > 'cluster/job_id'

