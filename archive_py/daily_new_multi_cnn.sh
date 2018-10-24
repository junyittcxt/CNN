# asset=2
# b=3
# maxjob=2
# for asset in {0..20}
# do
# jobsrunning = 0
# while jobsrunning < maxjobs {
#   do python3 sleep.py -t $q &
#   jobsrunning += 1
# }
# wait


# done
# job ( ){
#  python3 sleep.py -t $q1
# }


for asset in {0..17}
do
echo $asset
python3 run_cnn_daily.py -a $asset -d 1
done &

for asset in {18..36}
do
echo $asset
python3 run_cnn_daily.py -a $asset -d 1
done 

echo All done
