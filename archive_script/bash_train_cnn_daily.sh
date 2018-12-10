#
# for tt in {0..1}
# do
# echo "================="
# echo "=====THRESHOLD======="
# echo tt
#
#
# for asset in {8..11}
# do
# echo "================="
# echo "================="
# echo $asset
# echo "================="
# echo "================="
# python3 _train_cnn_daily.py -a $asset -d 1 -t $tt
# done &
#
# for asset in {20..23}
# do
# echo "================="
# echo "================="
# echo $asset
# echo "================="
# echo "================="
# python3 _train_cnn_daily.py -a $asset -d 1 -t $tt
# done &
#
# for asset in {33..36}
# do
# echo "================="
# echo "================="
# echo $asset
# echo "================="
# echo "================="
# python3 _train_cnn_daily.py -a $asset -d 1 -t $tt
# done
#
# wait
#
# echo "================="
# echo "=====END THRESHOLD======="
#
# done
#
# echo All done



for tt in {0..1}
do
echo "================="
echo "=====THRESHOLD======="
echo tt


for asset in {0..11}
do
echo "================="
echo "================="
echo $asset
echo "================="
echo "================="
python3 _train_cnn_daily.py -a $asset -d 1 -t $tt
done &

for asset in {12..23}
do
echo "================="
echo "================="
echo $asset
echo "================="
echo "================="
python3 _train_cnn_daily.py -a $asset -d 1 -t $tt
done &

for asset in {24..36}
do
echo "================="
echo "================="
echo $asset
echo "================="
echo "================="
python3 _train_cnn_daily.py -a $asset -d 1 -t $tt
done

wait

echo "================="
echo "=====END THRESHOLD======="

done

echo All done




#
# for asset in {0..36}
# do
# echo $asset
# python3 _cnn_inference.py -a $asset -d 1
# done &

# for asset in {18..36}
# do
# echo $asset
# python3 _cnn_inference.py -a $asset -d 1
# done

# echo All done
