for asset in {0..28}
do
echo "================="
echo "================="
echo $asset
echo "================="
echo "================="
python3 _train_cnn_minute_price.py -a $asset -d 0
done &

for asset in {29..58}
do
echo "================="
echo "================="
echo $asset
echo "================="
echo "================="
python3 _train_cnn_minute_price.py -a $asset -d 0
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
