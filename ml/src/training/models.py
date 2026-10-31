"""Persist preprocessing with model and an optional disjoint-period sigmoid calibrator."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.utils.class_weight import compute_sample_weight


class Champion:
    def __init__(self, pipeline, features, calibrator=None):
        self.pipeline=pipeline;self.features=features;self.calibrator=calibrator

    def fit(self,frame,target):
        """Estimator protocol for diagnostics; production fitting uses controlled train.fit."""
        self.pipeline.fit(frame[self.features],target);self.calibrator=None
        return self

    def predict_proba(self,frame):
        missing=set(self.features)-set(frame)
        if missing:raise ValueError('Missing features: '+', '.join(sorted(missing)))
        raw=self.pipeline.predict_proba(frame[self.features])[:,1]
        if self.calibrator is not None:raw=self.calibrator.predict_proba(logits(raw))[:,1]
        if not np.isfinite(raw).all() or ((raw<0)|(raw>1)).any():raise ValueError('Invalid model probability')
        return np.column_stack([1-raw,raw])


def logits(p):
    p=np.clip(p,1e-6,1-1e-6);return np.log(p/(1-p)).reshape(-1,1)


def feature_names(cfg,task):
    numeric=list(cfg['numeric_features']);categorical=cfg['categorical_features'] if task=='campaign' else []
    excluded=set(cfg['feature_exclusions'])|set(cfg.get(task+'_exclusions',[]))
    if set(numeric+categorical)&set(cfg['feature_exclusions']):raise ValueError('Allowlist contains excluded feature')
    return [v for v in numeric if v not in excluded],categorical


def pipeline(cfg,task,kind,value=None):
    numeric,categorical=feature_names(cfg,task)
    pre=ColumnTransformer([('numeric',Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())]),numeric),
                           ('category',Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),('encoder',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical)],verbose_feature_names_out=False)
    seed=cfg['random_seed']; params=cfg['model_parameters']
    if kind=='logistic':model=LogisticRegression(C=value,max_iter=params[kind]['max_iter'],random_state=seed)
    elif kind=='random_forest':model=RandomForestClassifier(max_leaf_nodes=value,n_estimators=params[kind]['n_estimators'],min_samples_leaf=params[kind]['min_samples_leaf'],n_jobs=2,random_state=seed)
    elif kind=='gradient_boosting':model=HistGradientBoostingClassifier(max_leaf_nodes=value,max_iter=params[kind]['max_iter'],learning_rate=params[kind]['learning_rate'],min_samples_leaf=params[kind]['min_samples_leaf'],early_stopping=False,random_state=seed)
    else:model=DummyClassifier(strategy='prior')
    return Pipeline([('preprocess',pre),('model',model)]),numeric+categorical


def fit(pipe,frame,features,cfg,kind):
    kwargs={}
    if kind!='dummy' and cfg['imbalance_strategy']=='balanced_sample_weights':kwargs['model__sample_weight']=compute_sample_weight('balanced',frame.target)
    if cfg['imbalance_strategy'] not in ['balanced_sample_weights','none']:raise ValueError('Unsupported imbalance strategy')
    return pipe.fit(frame[features],frame.target,**kwargs)
