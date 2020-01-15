ROOT='/Users/ohamelijnck/Scripts/cluster'

LIBS=()
SLURM_FILES=()
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
      --experiments_folder)
         EXPERIMENTS_FOLDER=$2
         shift;
      ;;
      --slurm_file)
         SLURM_FILE=$2
         SLURM_FILES+=("$SLURM_FILE")
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

TO_TAR="-C $EXPERIMENTS_FOLDER/$BASENAME/ models data meta  -C ../../ ${SLURM_FILES[@]}"

if [ "$LIB_FLAG" -eq "1" ]; then
   len=${#LIBS[@]}
   for (( i=0; i<$len; i++ )); do
      LIB="${LIBS[$i]}" ; 
      LIB_BASENAME=$(basename $LIB)
      echo "MOVING LIBRARY $LIB_BASENAME"
      #To uncompress without leading directories cd to $LIB then add all contents
      dir=`dirname "$LIB"`
      lib=`basename "$LIB"`
      TO_TAR="$TO_TAR -C $dir $lib"
   done
fi

echo $TO_TAR

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

#-l make bash act like login shell
#-s read from standard input

len=${#SLURM_FILES[@]}
for (( i=0; i<$len; i++ )); do
   SLURM_FILE="${SLURM_FILES[$i]}" ; 
   echo "sbatch $BASENAME/$SLURM_FILE"

results=$(ssh  -i "$SSH_KEY" "$USER@$IP" -o StrictHostKeyChecking=no 'bash -ls' << HERE
   sbatch $BASENAME/$SLURM_FILE
HERE
)
done

JOB_ID=$(echo $results | awk '{print $NF}')

echo $JOB_ID > 'cluster/job_id'

