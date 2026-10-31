"""Feature drift and score drift are diagnostics, not evidence of concept drift."""
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def psi(reference,current):
    a=pd.Series(reference).dropna().to_numpy();b=pd.Series(current).dropna().to_numpy()
    if not len(a) or not len(b):return None
    inner=np.unique(np.quantile(a,np.linspace(0,1,11)))[1:-1]
    bins=np.r_[-np.inf,inner,np.inf];pa=np.histogram(a,bins)[0]/len(a);pb=np.histogram(b,bins)[0]/len(b)
    pa=np.clip(pa,1e-5,1);pb=np.clip(pb,1e-5,1)
    return float(np.sum((pb-pa)*np.log(pb/pa)))


def drift(reference,current,features):
    rows=[]
    for col in features:
        a=reference[col];b=current[col];numeric=pd.api.types.is_numeric_dtype(a)
        rows.append({'feature':col,'reference_missing_rate':float(a.isna().mean()),'current_missing_rate':float(b.isna().mean()),
                     'psi':psi(a,b) if numeric else None,'ks_statistic':float(ks_2samp(a.dropna(),b.dropna()).statistic) if numeric and a.notna().any() and b.notna().any() else None,
                     'interpretation':'Descriptive data drift; repeated customers violate iid KS inference; concept drift needs matured future labels.'})
    return pd.DataFrame(rows)
