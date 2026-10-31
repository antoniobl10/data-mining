"""Three ML pages using existing report-authoring primitives."""


def append(api):
    new=api['new_page'];text=api['text'];button=api['button'];visual=api['visual'];chart=api['chart'];slicer=api['slicer'];c=api['c'];m=api['m'];lit=api['lit']
    scores='ML Customer Scores';perf='ML Model Performance';navigation=[('predictive_analytics','Predictive Analytics'),('next_best_action','Next Best Action'),('model_performance','Model Performance')]
    def frame(page,title,performance=False):
        new(page,title)
        text(page,'ml_banner','SYNTHETIC DEMO MODEL — trained on simulated behavior; not representative of real banking performance',24,12,1392,30,12,'#9F5561')
        text(page,'heading',title,24,51,1392,35,22,api['NAVY'])
        for i,(target,label) in enumerate(navigation):button(page,'nav_'+target,label,target,24+i*250,96,235)
        button(page,'portfolio','Portfolio','overview',790,96,180);button(page,'digital','Digital Demo','digital_overview',986,96,200)
        button(page,'reset','Reset','reset_all',1202,96,214,'Bookmark')
        filters=[(perf,'Use Case')] if performance else [(scores,'Country'),(scores,'Customer Value Segment'),(scores,'Next Best Action')]
        width=(1392-16*(len(filters)-1))/len(filters)
        for i,(table,col) in enumerate(filters):
            v=slicer(page,table,col,24+i*(width+16),158,width);v['visual']['syncGroup']['groupName']='ml_'+page+'_'+col.replace(' ','_')
        text(page,'context','Offline Model Evaluation — held-out temporal test; customer filters do not filter these metrics.' if performance else 'Scores as of Oct 1, 2026. Campaign context: Email / Cross-Sell. Priority is an index, not EUR or uplift.',24,247,1392,30,11)
        text(page,'footer','SYNTHETIC DEMO MODEL • Propensity is not causal uplift • Inactivity is not verified attrition • Analyst review required',24,1200,1392,26,10,'#9F5561')
    def cards(page,names):
        width=(1392-16*(len(names)-1))/len(names)
        for i,label in enumerate(names):
            v=visual(page,'ml_kpi_'+str(i),'card',24+i*(width+16),290,width,100,label,{'Values':[m('ML '+label)]})
            v['visual']['visualContainerObjects']['title'][0]['properties']['fontSize']=lit(10)
            v['visual']['objects']={'labels':[{'properties':{'fontSize':lit(18),'labelDisplayUnits':lit(0)}}],'categoryLabels':[{'properties':{'show':lit(False)}}]}
    def bar(page,name,col,measure,x,y,w=688,h=240,table=scores):
        v=chart(page,name,table,col,'ML '+measure,x,y,w,h,title=measure+' by '+col)
        v['visual']['query']['queryState'].pop('Tooltips',None)
        v['visual']['objects']['valueAxis'][0]['properties']['labelPrecision']=lit(3 if table==perf else 1)
        return v
    frame('predictive_analytics','Predictive Analytics')
    cards('predictive_analytics',['High Churn Risk Customers','High Campaign Propensity Customers','High Payroll Propensity Customers','High Service Propensity Customers','Customers with Recommended Action'])
    bar('predictive_analytics','risk_distribution','Churn Risk Band','Scored Customers',24,414)
    bar('predictive_analytics','propensity_distribution','Campaign Propensity Band','Scored Customers',728,414)
    bar('predictive_analytics','top_actions','Next Best Action','Scored Customers',24,678)
    bar('predictive_analytics','payroll_segment','Customer Value Segment','Average Payroll Propensity',728,678)
    for name,xmeasure,ymeasure,x in [('value_risk','Average Value Index','Average Churn Risk',24),('engagement_propensity','Average Engagement','Average Campaign Propensity',728)]:
        visual('predictive_analytics',name,'scatterChart',x,942,688,230,'Value vs inactivity risk' if x==24 else 'Engagement vs campaign propensity',{'Category':[c(scores,'Customer Key')],'X':[m('ML '+xmeasure)],'Y':[m('ML '+ymeasure)],'Size':[m('ML Scored Customers')]})
    frame('next_best_action','Next Best Action')
    cards('next_best_action',['Scored Customers','Customers with Recommended Action','Average Action Score','Average Priority Index'])
    bar('next_best_action','action_customers','Next Best Action','Scored Customers',24,414)
    bar('next_best_action','priority_index','Next Best Action','Total Priority Index',728,414)
    bar('next_best_action','average_probability','Next Best Action','Average Campaign Propensity',24,678)
    bar('next_best_action','country','Country','Total Priority Index',728,678)
    queue=visual('next_best_action','customer_actions','tableEx',24,942,1392,230,'Authorized analyst queue — priority index and reasons; no monetary value estimate',{'Values':[c(scores,col) for col in ['Customer Key','Customer Value Segment','Next Best Action','Priority Score','Reason Code','Next Best Action Reason']]})
    queue['visual']['query']['sortDefinition']={'sort':[{'field':api['field'](scores,'Priority Score'),'direction':'Descending'}],'isDefaultSort':False}
    api['PAGES']['next_best_action']['page']['height']=1530
    next(v for v in api['PAGES']['next_best_action']['visuals'] if v['name']=='footer')['position']['y']=1490
    visual('next_best_action','actions_by_segment','pivotTable',24,1200,1392,260,'Recommended action by customer value segment',{'Rows':[c(scores,'Customer Value Segment')],'Columns':[c(scores,'Next Best Action')],'Values':[m('ML Scored Customers'),m('ML Average Priority Index')]})
    frame('model_performance','Model Performance',True)
    cards('model_performance',['Offline ROC AUC','Offline PR AUC','Offline Lift at 10','Offline Precision','Offline Recall','Offline Brier Score'])
    bar('model_performance','roc','Use Case','Offline ROC AUC',24,414,table=perf)
    bar('model_performance','pr','Use Case','Offline PR AUC',728,414,table=perf)
    bar('model_performance','lift','Use Case','Offline Lift at 10',24,678,table=perf)
    bar('model_performance','calibration','Use Case','Offline Brier Score',728,678,table=perf)
    visual('model_performance','offline_results','tableEx',24,942,1392,230,'Offline Model Evaluation — champion, calibration and test window',{'Values':[c(perf,col) for col in ['Use Case','Model Name','Calibration','Test Start','Test End']]+[m('ML Offline '+label) for label in ['PR AUC','Lift at 10','Brier Score']]})
    button('overview','ml_entry','Synthetic ML Demo','predictive_analytics',300,1150,250)
    for page in ['predictive_analytics','next_best_action','model_performance']:
        for v in api['PAGES'][page]['visuals']:
            v['visual']['visualContainerObjects']['general'][0]['properties']['altText']=lit('SYNTHETIC DEMO MODEL. '+v['name'])
