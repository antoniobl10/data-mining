"""Advanced business pages, with synthetic labels and scoped statistical displays."""


def append(api):
    new=api['new_page'];text=api['text'];button=api['button'];visual=api['visual'];chart=api['chart'];slicer=api['slicer'];c=api['c'];m=api['m'];lit=api['lit'];field=api['field']
    navigation=[('journey_analytics','Journeys'),('customer_funnels','Funnels'),('cohorts_retention','Cohorts'),('experimentation','Experiments'),('marketing_attribution','Attribution'),('growth_opportunities','Growth'),('customer_opportunities','Opportunities')]
    def frame(page,title,filters,context):
        new(page,title)
        text(page,'analytics_banner','SYNTHETIC DEMO ANALYTICS — simulated behavior and experiments; value/ROI are proxies, not real bank results',24,12,1392,28,11,'#9F5561')
        text(page,'heading',title,24,51,1392,36,22,api['NAVY'])
        for i,(target,label) in enumerate(navigation):button(page,'nav_'+target,label,target,24+i*201,96,185)
        if not filters:filters=[('AN Opportunities','Country')]
        width=(1392-16*(len(filters)-1))/len(filters)
        for i,(table,col) in enumerate(filters):
            v=slicer(page,table,col,24+i*(width+16),158,width);v['visual']['syncGroup']['groupName']='an_'+page+'_'+col.replace(' ','_')
            if col in ['Funnel Name','Segment Dimension','Cohort Type','Attribution Model','Attribution Window Days']:
                v['visual']['objects']['selection'][0]['properties'].update(singleSelect=lit(True),selectAllCheckboxEnabled=lit(False))
        text(page,'context',context,24,247,1392,30,11)
        text(page,'footer','SYNTHETIC DEMO ANALYTICS • Randomized simulation effects differ from rule-based attribution • No real campaign was sent',24,1200,1392,25,10,'#9F5561')
    def cards(page,names):
        width=(1392-16*(len(names)-1))/len(names)
        for i,label in enumerate(names):
            v=visual(page,'an_kpi_'+str(i),'card',24+i*(width+16),290,width,100,label,{'Values':[m('AN '+label)]});v['visual']['visualContainerObjects']['title'][0]['properties']['fontSize']=lit(10)
            v['visual']['objects']={'labels':[{'properties':{'fontSize':lit(18),'labelDisplayUnits':lit(0)}}],'categoryLabels':[{'properties':{'show':lit(False)}}]}
    def bar(page,name,table,col,measure,x,y,w=688,h=240,kind='clusteredBarChart'):
        v=chart(page,name,table,col,'AN '+measure,x,y,w,h,title=measure+' by '+col,kind=kind);v['visual']['query']['queryState'].pop('Tooltips',None)
        v['visual']['objects']['valueAxis'][0]['properties']['labelPrecision']=lit(2 if any(x in measure for x in ['Lift','Retention','Rate','ROI','Probability']) else 1)
        return v
    def table(page,name,entity,columns,x=24,y=942,w=1392,h=230,title=None,measures=None):return visual(page,name,'tableEx',x,y,w,h,title or name.replace('_',' ').title(),{'Values':[c(entity,col) for col in columns]+[m('AN '+v) for v in measures or []]})
    frame('journey_analytics','Customer Journeys',[('AN Journeys','Journey Path')],'Sessions are reconstructed by customer/channel/device with a 30-minute timeout. Activation events are not verified payroll conversion.')
    cards('journey_analytics',['Journey Sessions','Journey Activations','Journey Activation Rate'])
    bar('journey_analytics','common_paths','AN Journeys','Journey Path','Journey Sessions',24,414,w=1392,h=490)
    table('journey_analytics','path_details','AN Journeys',['Journey Path','Sessions','Customers','Conversions','Average Steps','Average Duration'])
    frame('customer_funnels','Customer Funnels',[('AN Funnels','Funnel Name'),('AN Funnels','Segment Dimension')],'Default: Campaign / All. Choose one funnel and one segmentation dimension. Views without service-specific timestamps are omitted.')
    bar('customer_funnels','dynamic_funnel','AN Funnels','Stage','Funnel Customers',24,290,h=330,kind='funnel')
    bar('customer_funnels','dropoff','AN Funnels','Stage','Funnel Drop Off',728,290,h=330)
    bar('customer_funnels','segment_conversion','AN Funnels','Segment','Funnel Customers',24,646,h=260)
    bar('customer_funnels','channel_rates','AN Campaign Economics','Channel','Attributed Conversions',728,646,h=260)
    # Channel counts need their own observational numerator, not attribution from another table.
    api['PAGES']['customer_funnels']['visuals'].pop()
    table('customer_funnels','channel_conversion','AN Campaign Economics',['Channel'],x=728,y=646,w=688,h=260,title='Observed campaign contacts/conversion by channel; not causal',measures=['Observed Campaign Contacts','Observed Campaign Conversions','Observed Campaign Conversion Rate'])
    table('customer_funnels','stage_table','AN Funnels',['Funnel Name','Stage','Segment Dimension','Segment'],measures=['Funnel Customers','Funnel Rate','Funnel Drop Off'])
    frame('cohorts_retention','Cohorts & Retention',[('AN Cohorts','Cohort Type'),('AN Cohorts','Cohort Name')],'Digital retention requires a meaningful session after cohort entry. Future months are absent. Service cohort digital retention is not service-state retention.')
    heat=visual('cohorts_retention','cohort_heatmap','pivotTable',24,290,1392,340,'Cohort digital retention — cohort month × observed month age',{'Rows':[c('AN Cohorts','Cohort Period')],'Columns':[c('AN Cohorts','Months Since Cohort')],'Values':[m('AN Digital Retention')]})
    heat['visual']['objects']={'values':[{'selector':{'metadata':'_Measures.AN Digital Retention'},'properties':{'backColor':{'solid':{'color':{'expr':field('_Measures','AN Retention Cell Color',True)}}}}}]}
    bar('cohorts_retention','retention_curve','AN Cohorts','Months Since Cohort','Digital Retention',24,654,h=250,kind='lineChart')
    bar('cohorts_retention','engagement_decay','AN Cohorts','Months Since Cohort','Cohort Engagement',728,654,h=250,kind='lineChart')
    table('cohorts_retention','retention_definitions','AN Cohorts',['Cohort Name','Cohort Period','Months Since Cohort'],measures=['Digital Retention','Product Retention','Service Cohort Digital Retention'])
    api['PAGES']['cohorts_retention']['page']['height']=1530
    next(v for v in api['PAGES']['cohorts_retention']['visuals'] if v['name']=='footer')['position']['y']=1490
    bar('cohorts_retention','segment_retention','AN Retention Segments','Customer Value Segment','Segment Digital Retention',24,1200,h=260)
    bar('cohorts_retention','product_retention','AN Cohorts','Cohort Name','Product Retention',728,1200,h=260)
    frame('experimentation','Experimentation',[('AN Experiments','Experiment Id')],'Simulated randomized ITT. Holm-adjusted primary tests; conservative family-wise confidence bounds. A significant p-value alone cannot declare a winner.')
    cards('experimentation',['Active Experiments','Completed Experiments','Winning Experiments','Mean Simulated Lift','Incremental Conversion Estimate'])
    v=visual('experimentation','treatment_control','clusteredColumnChart',24,414,688,245,'Simulated conversion rates by experiment',{'Category':[c('AN Experiments','Experiment Name')],'Y':[m('AN Control Conversion'),m('AN Treatment Conversion')]})
    table('experimentation','lift_confidence','AN Experiments',['Experiment Id'],x=728,y=414,w=688,h=245,title='Lift with simultaneous confidence intervals',measures=['Mean Simulated Lift','Lift CI Lower','Lift CI Upper','Adjusted P Value'])
    table('experimentation','experiment_results','AN Experiments',['Experiment Name','Control N','Treatment N','Planned Per Variant','Experiment Decision','Guardrail Status'],y=683,h=235,title='Decision and planned power — right-click for Experiment Detail')
    table('experimentation','guardrails_timeline','AN Experiments',['Experiment Id','Experiment Start','Experiment End','Unsubscribe Rate Change','Complaint Rate Change','Nps Change','Cost Per Customer'],title='Guardrails and experiment timeline')
    p=new('experiment_detail','Experiment Detail',True,'Drillthrough')
    p['pageBinding']={'name':'experiment_drill','type':'Drillthrough','parameters':[{'name':'experiment_id','boundFilter':'drill_experiment','fieldExpr':field('AN Experiments','Experiment Id')}],'acceptsFilterContext':'Default'}
    p['filterConfig']={'filters':[{'name':'drill_experiment','field':field('AN Experiments','Experiment Id'),'type':'Categorical','howCreated':'Drillthrough'}]}
    text('experiment_detail','banner','SYNTHETIC DEMO ANALYTICS — simulated experiment detail',24,20,1392,35,13,'#9F5561');text('experiment_detail','heading','Experiment Detail',24,70,1392,50,24)
    button('experiment_detail','back','Experiments','experimentation',24,135,220)
    table('experiment_detail','hypothesis','AN Experiments',['Experiment Id','Hypothesis','Control Description','Treatment Description'],y=210,h=240)
    table('experiment_detail','effect','AN Experiments',['Control N','Treatment N','Planned Per Variant','Experiment Decision'],y=475,h=240,measures=['Control Conversion','Treatment Conversion','Mean Simulated Lift','Lift CI Lower','Lift CI Upper','Adjusted P Value'])
    table('experiment_detail','guardrails','AN Experiments',['Guardrail Status','Unsubscribe Rate Change','Complaint Rate Change','Nps Change','Cost Per Customer','Srm P Value'],y=740,h=240)
    text('experiment_detail','limit','All effects and value assumptions are simulated. Minimum sample size, quality, SRM and guardrails override conversion-only ranking.',24,1020,1392,120,14)
    frame('marketing_attribution','Marketing Attribution',[('AN Attribution','Attribution Model'),('AN Attribution','Attribution Window Days')],'Default: Last Touch / 30 days. Credits conserve observed conversions; costs are counted once per model/window. Attribution allocates credit, not causality.')
    cards('marketing_attribution',['Attributed Conversions','Attributed Value','Attributed Cost','Attribution ROI Proxy'])
    bar('marketing_attribution','channel_credit','AN Attribution','Channel','Attributed Conversions',24,414)
    visual('marketing_attribution','first_last','clusteredColumnChart',728,414,688,240,'First versus Last Touch — 30-day rule-based allocation',{'Category':[c('AN Attribution','Channel')],'Y':[m('AN First Touch Conversions'),m('AN Last Touch Conversions')]})
    bar('marketing_attribution','channel_value','AN Attribution','Channel','Attributed Value',24,678)
    bar('marketing_attribution','campaign_roi','AN Attribution','Campaign','Attribution ROI Proxy',728,678)
    table('marketing_attribution','cost_value','AN Attribution',['Channel','Campaign'],measures=['Attributed Conversions','Attributed Value','Attributed Cost','Attribution ROI Proxy'])
    frame('customer_opportunities','Customer Opportunities',[('AN Opportunities','Country'),('AN Opportunities','Customer Value Segment'),('AN Opportunities','Next Best Action'),('AN Opportunities','Contact Allowed')],'Authorized analyst view. Holdout, contact caps, ownership and guardrail stops override scores. Experimental lift is an average simulated effect, not individual uplift.')
    cards('customer_opportunities',['Opportunity Customers','Contactable Customers','Opportunity Priority','Opportunity Experimental Lift'])
    visual('customer_opportunities','priority_matrix','scatterChart',24,414,688,480,'Value index versus model/risk opportunity — not monetary CLV',{'Category':[c('AN Opportunities','Customer Key')],'X':[m('AN Opportunity Value Index')],'Y':[m('AN Opportunity Probability')],'Size':[m('AN Opportunity Customers')],'Series':[c('AN Opportunities','Opportunity Quadrant')]})
    bar('customer_opportunities','actions','AN Opportunities','Next Best Action','Opportunity Customers',728,414)
    bar('customer_opportunities','priority','AN Opportunities','Current Lifecycle Stage','Opportunity Priority',728,678)
    queue=table('customer_opportunities','action_queue','AN Opportunities',['Customer Key','Current Lifecycle Stage','Primary Bank Stage','Next Best Action','Priority Score','Experimental Lift','Contact Allowed','Reason Code','Next Best Action Reason'])
    queue['visual']['query']['sortDefinition']={'sort':[{'field':field('AN Opportunities','Priority Score'),'direction':'Descending'}],'isDefaultSort':False}
    frame('growth_opportunities','Growth & Opportunities',[('AN Experiments','Experiment Id')],'Full snapshot portfolio KPIs and separate simulated experiment effects. The three experiments address different populations and are not one pooled trial.')
    cards('growth_opportunities',['Likely Primary Bank Rate','Salary Domiciliation Rate','Incremental Conversion Estimate','Service Activation Rate','NPS','Campaign ROI Proxy'])
    bar('growth_opportunities','primary_bank','AN Funnels','Stage','Primary Bank Customers',24,414)
    bar('growth_opportunities','experiment_lift','AN Experiments','Experiment Name','Mean Simulated Lift',728,414)
    for i,measure in enumerate(['Primary Journey Narrative','Payroll Experiment Narrative']):
        v=visual('growth_opportunities','narrative_'+str(i),'card',24+i*704,678,688,180,'Supported business narrative',{'Values':[m('AN '+measure)]});v['visual']['objects']={'labels':[{'properties':{'fontSize':lit(13)}}],'categoryLabels':[{'properties':{'show':lit(False)}}]}
    bar('growth_opportunities','lifecycle','AN Opportunities','Current Lifecycle Stage','Opportunity Customers',24,884,h=285)
    table('growth_opportunities','winners','AN Experiments',['Experiment Name','Experiment Decision','Guardrail Status'],x=728,y=884,w=688,h=285,title='Experiment decisions — no conversion-only winner selection')
    button('overview','analytics_entry','Advanced Business Analytics','growth_opportunities',576,1150,300)
    for page in [p for p,_ in navigation]+['experiment_detail']:
        for v in api['PAGES'][page]['visuals']:
            v['visual']['visualContainerObjects']['general'][0]['properties']['altText']=lit('SYNTHETIC DEMO ANALYTICS. '+v['name'])
