"""Probability, capacity, calibration and retrospective targeting diagnostics."""
import math
import numpy as np
import pandas as pd
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_score, recall_score,
                            f1_score, log_loss, brier_score_loss, roc_curve, precision_recall_curve, confusion_matrix)
from sklearn.calibration import calibration_curve


def ranking(y, p, fraction):
    y=np.asarray(y); p=np.asarray(p); n=max(1,math.ceil(len(y)*fraction))
    top=np.argsort(-p,kind='stable')[:n]; base=float(y.mean())
    return {'fraction':fraction,'targeted':n,'conversion_rate':float(y[top].mean()),
            'lift':float(y[top].mean()/base) if base else None,'gain':float(y[top].sum()/y.sum()) if y.sum() else None,
            'recall':float(y[top].sum()/y.sum()) if y.sum() else None}


def metrics(y,p,threshold=.5):
    y=np.asarray(y); p=np.asarray(p); pred=p>=threshold; binary=len(np.unique(y))==2
    return {'roc_auc':float(roc_auc_score(y,p)) if binary else None,'pr_auc':float(average_precision_score(y,p)) if y.sum() else None,
            'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),
            'f1':float(f1_score(y,pred,zero_division=0)),'log_loss':float(log_loss(y,p,labels=[0,1])),
            'brier_score':float(brier_score_loss(y,p)),'lift_at_10':ranking(y,p,.10)['lift'],
            'recall_at_top_5':ranking(y,p,.05)['recall'],'recall_at_top_10':ranking(y,p,.10)['recall']}


def diagnostic_tables(y,p,cfg):
    y=np.asarray(y);p=np.asarray(p);order=np.argsort(-p,kind='stable')
    deciles=[]
    for i,ix in enumerate(np.array_split(order,10)):
        if len(ix):deciles.append({'decile':i+1,'customers':len(ix),'positives':int(y[ix].sum()),'conversion_rate':float(y[ix].mean()),'mean_probability':float(p[ix].mean()),'lift':float(y[ix].mean()/y.mean()) if y.mean() else None})
    thresholds=[{'threshold':t,'customers_targeted':int((p>=t).sum()),'expected_conversions':float(p[p>=t].sum()),**metrics(y,p,t)} for t in cfg['threshold_grid']]
    return pd.DataFrame(deciles),pd.DataFrame(thresholds),pd.DataFrame([ranking(y,p,f) for f in cfg['ranking_fractions']])


def plots(y,p,threshold,folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained'); fig.suptitle('SYNTHETIC DEMO MODEL — offline test evaluation')
    if len(np.unique(y))==2:
        x,z,_=roc_curve(y,p);axes[0,0].plot(x,z);axes[0,0].plot([0,1],[0,1],'--');axes[0,0].set(title='ROC',xlabel='False positive rate',ylabel='Recall')
    pr,re,_=precision_recall_curve(y,p);axes[0,1].plot(re,pr);axes[0,1].axhline(np.mean(y),ls='--');axes[0,1].set(title='Precision–recall',xlabel='Recall',ylabel='Precision')
    actual,predicted=calibration_curve(y,p,n_bins=8,strategy='quantile');axes[0,2].plot(predicted,actual,'o-');axes[0,2].plot([0,1],[0,1],'--');axes[0,2].set(title='Calibration',xlabel='Mean predicted probability',ylabel='Observed rate')
    axes[1,0].imshow(confusion_matrix(y,np.asarray(p)>=threshold,labels=[0,1]));axes[1,0].set(title=f'Confusion matrix at {threshold:.3f}',xlabel='Predicted',ylabel='Actual')
    cm=confusion_matrix(y,np.asarray(p)>=threshold,labels=[0,1])
    for i in range(2):
        for j in range(2):axes[1,0].text(j,i,str(cm[i,j]),ha='center',color='red')
    order=np.argsort(-np.asarray(p),kind='stable'); gain=np.cumsum(np.asarray(y)[order])/max(1,np.sum(y));axes[1,1].plot(np.arange(1,len(y)+1)/len(y),gain);axes[1,1].plot([0,1],[0,1],'--');axes[1,1].set(title='Cumulative gains',xlabel='Audience fraction',ylabel='Positive capture fraction')
    axes[1,2].hist(p,bins=20);axes[1,2].set(title='Score distribution',xlabel='Probability',ylabel='Observations')
    fig.savefig(folder/'evaluation.png',dpi=140);plt.close(fig)


def simulation(frame,p,cfg):
    """Historical selection efficiency; expected random outcomes, observed selected outcomes."""
    cost=cfg['business_rules']['contact_cost'];n=min(len(frame),int(cfg['business_rules']['simulation_budget']/cost)); y=frame.target.to_numpy()
    random_conversions=n*float(y.mean()); rows=[]
    for name,order in [('Random Audience',None),('Rule-Based Audience',np.argsort(-frame.engagement_score.to_numpy(),kind='stable')),('ML Propensity Audience',np.argsort(-np.asarray(p),kind='stable'))]:
        conversions=random_conversions if order is None else int(y[order[:n]].sum())
        rows.append({'audience':name,'customers_contacted':n,'historical_conversion_estimate':conversions,'conversion_rate':conversions/max(1,n),'cost':n*cost,
                     'cost_per_conversion':n*cost/conversions if conversions else None,'difference_vs_random_estimate':conversions-random_conversions,
                     'interpretation':'SYNTHETIC DEMO MODEL — retrospective targeting efficiency; no causal uplift; standardized contact cost'})
    return pd.DataFrame(rows)
