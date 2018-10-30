
for asset in {0..28}
do
echo $asset
python3 _cnn_inference_price_minute.py -a $asset -d 0
done &

for asset in {29..58}
do
echo $asset
python3 _cnn_inference_price_minute.py -a $asset -d 0
done

# echo All done
