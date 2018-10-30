# for asset in {0..24}
# do
# echo $asset
# python3 _cnn_inference.py -a $asset -d 0
# done &
#
# for asset in {25..50}
# do
# echo $asset
# python3 _cnn_inference.py -a $asset -d 0
# done
#
# echo All done

#
for asset in {0..28}
do
echo $asset
python3 _cnn_inference.py -a $asset -d 0
done &

for asset in {29..58}
do
echo $asset
python3 _cnn_inference.py -a $asset -d 0
done

# echo All done
