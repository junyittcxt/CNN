# asset=2
# lossmethod=1

for asset in {3..15}
do
for lossmethod in {0..1}
do
echo $asset $lossmethod
python3 cnn_preproc.py -f 1 -a $asset
wait
python3 cnn_preproc.py -f 0 -i 2 -a $asset
wait
python3 cnn_preproc.py -f 0 -i 3 -a $asset
wait
python3 cnn_train_basic.py -l $lossmethod -a $asset
wait
python3 cnn_inference_basic.py -l $lossmethod -a $asset -t 0
python3 cnn_inference_basic.py -l $lossmethod -a $asset -t 1
done
done
echo All done
