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


#APPEND DATETIME TO RESULTS FOLDER
dt=$(date '+%d_%m_%Y_%H_%M_%S');


#ENSURE RESULTS FOLDER EXISTS

ssh  -i "$SSH_KEY" "$USER@$IP" -o StrictHostKeyChecking=no 'bash -s' << HERE
   cd $BASENAME
   tar -czf $BASENAME.tar results cluster/logs models/restore
HERE

mkdir -p cluster/"$dt"_results

echo "scp  -i $SSH_KEY $USER@$IP:$BASENAME/$BASENAME.tar cluster/'$dt'_results/$BASENAME'_results.tar"

scp  -i "$SSH_KEY" "$USER@$IP:$BASENAME/$BASENAME.tar" cluster/"$dt"_results/"$BASENAME"_results.tar
tar -xzf cluster/"$dt"_results/"$BASENAME"_results.tar --directory cluster/"$dt"_results/
rm -rf cluster/"$dt"_results/"$BASENAME"_results.tar

echo $PWD
echo "HERE"

rsync -r cluster/"$dt"_results/results/ experiment_data/"$BASENAME"/results/
rsync -r cluster/"$dt"_results/models/restore/ experiment_data/"$BASENAME"/models/restore/

