"""Validation permutation importance and explicit local probability perturbations."""
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def explain(champion,frame,folder,cfg):
    sample=frame.sample(min(700,len(frame)),random_state=cfg['random_seed'])
    # Raw named columns avoid opaque one-hot names in business explanations.
    def ap(estimator,x,y):
        from sklearn.metrics import average_precision_score
        return average_precision_score(y,estimator.predict_proba(x)[:,1])
    result=permutation_importance(champion,sample[champion.features],sample.target,scoring=ap,n_repeats=3,random_state=cfg['random_seed'])
    importance=pd.DataFrame({'feature':champion.features,'pr_auc_decrease':result.importances_mean,'std':result.importances_std}).sort_values('pr_auc_decrease',ascending=False)
    importance.to_csv(folder/'feature_importance.csv',index=False)
    pre=champion.pipeline.named_steps['preprocess'];model=champion.pipeline.named_steps['model'];names=pre.get_feature_names_out()
    if hasattr(model,'coef_'):pd.DataFrame({'feature':names,'coefficient':model.coef_[0]}).to_csv(folder/'coefficients.csv',index=False)
    if hasattr(model,'feature_importances_'):pd.DataFrame({'feature':names,'importance':model.feature_importances_}).to_csv(folder/'tree_importance.csv',index=False)
    probs=champion.predict_proba(sample)[:,1]; row=sample.iloc[[int(np.argmax(probs))]].copy();base=float(champion.predict_proba(row)[0,1]);local=[]
    for col in importance.head(10).feature:
        changed=row.copy();changed[col]=frame[col].median() if pd.api.types.is_numeric_dtype(frame[col]) else frame[col].mode().iloc[0]
        local.append({'customer_key':int(row.customer_key.iloc[0]),'feature':col,'actual_value':str(row[col].iloc[0]),'reference_value':str(changed[col].iloc[0]),'probability':base,'probability_difference_to_reference':base-float(champion.predict_proba(changed)[0,1]),'method':'one-feature perturbation; association, not SHAP or causal contribution'})
    pd.DataFrame(local).to_csv(folder/'local_explanation.csv',index=False)
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained');top=importance.head(12).iloc[::-1];ax.barh(top.feature,top.pr_auc_decrease);ax.set(title='SYNTHETIC DEMO MODEL — validation permutation importance',xlabel='PR-AUC decrease');fig.savefig(folder/'feature_importance.png',dpi=130);plt.close(fig)
    return importance.head(8).feature.tolist()
