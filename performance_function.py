import numpy as np
import sklearn


def perf(ytrue,yscore, t = 0.5):
    y_pred_bin = 1*(yscore > t)

    print("n:", len(ytrue))
    print("true: prop:", np.mean(ytrue), "n1:", np.sum(ytrue))
    print("pred: prop:", np.mean(y_pred_bin), "n1:", np.sum(y_pred_bin))
    cm = sklearn.metrics.confusion_matrix(ytrue, y_pred_bin)
    prec = sklearn.metrics.precision_score(ytrue, y_pred_bin)
    auc = sklearn.metrics.roc_auc_score(ytrue, yscore)
    print("cm:\n",cm)
    print("prec:",prec)
    print("auc:", auc)
