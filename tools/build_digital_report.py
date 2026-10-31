"""Six clearly labeled demo pages appended to the existing real-data report."""


def append(api):
    pages=api['PAGES'];new=api['new_page'];text=api['text'];button=api['button'];visual=api['visual'];chart=api['chart'];slicer=api['slicer'];c=api['c'];m=api['m'];lit=api['lit'];navy=api['NAVY']
    navigation=[('digital_overview','Digital Overview'),('campaigns','Campaigns'),('engagement','Engagement'),('primary_banking','Primary Banking'),('services','Services'),('satisfaction','Satisfaction')]
    def frame(name,title,filters):
        new(name,title)
        text(name,'demo_banner','SYNTHETIC DEMO DATA — simulated behavior linked to the original customer master; not real bank performance',24,12,1392,28,11,'#9F5561')
        text(name,'heading',title,24,45,1190,40,20,navy)
        for i,(target,label) in enumerate(navigation):button(name,'demo_nav_'+target,label,target,24+i*177,91,165)
        button(name,'real_portfolio','Real Portfolio','overview',1090,91,152)
        button(name,'reset','Reset','reset_all',1254,91,162,'Bookmark')
        width=(1392-16*(len(filters)-1))/len(filters)
        for i,(table,col) in enumerate(filters):
            v=slicer(name,table,col,24+i*(width+16),139,width)
            v['visual']['syncGroup']['groupName']='demo_'+table.replace(' ','_')+'_'+col.replace(' ','_')
        text(name,'context','Demo period Oct 2024–Sep 2026. Snapshot cards describe Sep 30, 2026; time charts follow demo dates.',24,220,1392,30,11)
        text(name,'footer','SYNTHETIC DEMO DATA • Scores are transparent proxies • Correlation is not causal impact • Customer IDs remain restricted',24,1200,1392,26,10,'#9F5561')
    def cards(page,names):
        width=(1392-16*(len(names)-1))/len(names)
        for i,name in enumerate(names):
            v=visual(page,'demo_kpi_'+str(i),'card',24+i*(width+16),258,width,100,name,{'Values':[m('Demo '+name)]})
            v['visual']['visualContainerObjects']['title'][0]['properties']['fontSize']=lit(10)
            v['visual']['objects']={'labels':[{'properties':{'fontSize':lit(18),'labelDisplayUnits':lit(0),'labelPrecision':lit(1 if any(s in name for s in ['Rate','Average','NPS','%','Score']) else 0)}}], 'categoryLabels':[{'properties':{'show':lit(False)}}]}
    def bar(page,name,table,col,measure,x,y,w=688,h=245):
        result=chart(page,name,table,col,'Demo '+measure,x,y,w,h,title=measure+' by '+col,kind='lineChart' if table=='Demo Date' else 'clusteredBarChart')
        if table=='Demo Date' or col in ['Primary Bank Segment','Engagement Segment','Engagement Score Band','Primary Score Band']:
            result['visual']['query']['sortDefinition']={'sort':[{'field':api['field'](table,col),'direction':'Ascending'}],'isDefaultSort':False}
        return result
    def funnel(page,kind,x,y,w=688,h=245):
        return visual(page,kind.lower()+'_funnel','funnel',x,y,w,h,kind+' funnel — '+('contacts' if kind=='Campaign' else 'customer-service relationships'),{'Category':[c('Demo Funnel Stage',kind+' Stage')],'Y':[m('Demo '+kind+' Funnel Value')]})
    def matrix(page,name,table,col,measures,y=925,h=250):
        visual(page,name,'pivotTable',24,y,1392,h,'Snapshot profiles — SYNTHETIC DEMO DATA',{'Rows':[c(table,col)],'Values':[m('Demo '+v) for v in measures]})
    cohort=[('Demo Customer 360','Country'),('Demo Customer 360','Customer Value Segment'),('Demo Customer 360','Primary Bank Segment')]
    frame('digital_overview','Digital Business Overview',cohort)
    cards('digital_overview',['Salary Domiciliation Rate','Average Products per Customer','Monthly Active Customers','Conversion Rate','Service Adoption Rate','Likely Primary Bank %','Average NPS Score'])
    bar('digital_overview','primary_mix','Demo Customer 360','Primary Bank Segment','Customers',24,380)
    bar('digital_overview','engagement_mix','Demo Customer 360','Engagement Segment','Customers',728,380)
    bar('digital_overview','product_penetration','Demo Product','Product Type','Product Penetration Rate',24,653)
    funnel('digital_overview','Campaign',728,653)
    bar('digital_overview','payroll_segment','Demo Customer 360','Primary Bank Segment','Salary Domiciliation Rate',24,925,h=245)
    bar('digital_overview','service_adoption','Demo Service','Service Name','Service Activation Rate',728,925,h=245)

    frame('campaigns','Campaign Performance',[('Demo Date','Month'),('Demo Campaign','Channel'),('Demo Customer 360','Primary Customer Segment')])
    cards('campaigns',['Campaigns Sent','Open Rate','CTR','Conversion Rate','Cost per Conversion'])
    funnel('campaigns','Campaign',24,380)
    bar('campaigns','channel','Demo Campaign','Channel','Conversion Rate',728,380)
    bar('campaigns','campaign','Demo Campaign','Campaign Name','Conversion Rate',24,653)
    bar('campaigns','month','Demo Date','Month','Campaign Conversions',728,653)
    matrix('campaigns','segments','Demo Customer 360','Primary Bank Segment',['Campaigns Sent','Campaign Opens','Campaign Clicks','Campaign Conversions','Conversion Rate','Campaign Cost','Cost per Conversion'])
    # Additional cost/conversion exploration fits below the initial dashboard viewport.
    pages['campaigns']['page']['height']=1570
    visual('campaigns','cost_conversions','scatterChart',24,1260,1392,280,'Campaign cost versus conversions — association, not incremental ROI',{'Category':[c('Demo Campaign','Campaign Id')],'X':[m('Demo Campaign Cost')],'Y':[m('Demo Campaign Conversions')],'Size':[m('Demo Campaigns Sent')]})

    frame('engagement','Digital Engagement',[('Demo Date','Month'),('Demo Customer 360','Country'),('Demo Customer 360','Customer Value Segment')])
    cards('engagement',['Monthly Active Customers','Weekly Active Customers','Active Customers 30D','Mobile App Adoption Rate','Average Sessions per Customer','High Value Low Engagement Customers'])
    bar('engagement','monthly_active','Demo Date','Month','Monthly Active Customers',24,380)
    bar('engagement','sessions','Demo Date','Month','Digital Sessions',728,380)
    bar('engagement','channel','Demo Digital Events','Channel','Digital Events',24,653)
    bar('engagement','event','Demo Digital Events','Event Type','Digital Events',728,653)
    bar('engagement','distribution','Demo Customer 360','Engagement Score Band','Customers',24,925,h=245)
    bar('engagement','value','Demo Customer 360','Customer Value Segment','Average Engagement Score',728,925,h=245)

    frame('primary_banking','Primary Banking',cohort)
    cards('primary_banking',['Salary Domiciliation Rate','Likely Primary Bank %','Average Products per Customer','Average Engagement Score','Payroll Opportunity Customers','High Engagement Low Product Depth Customers'])
    bar('primary_banking','score_distribution','Demo Customer 360','Primary Score Band','Customers',24,380)
    bar('primary_banking','payroll','Demo Customer 360','Primary Bank Segment','Salary Domiciliation Rate',728,380)
    bar('primary_banking','products','Demo Customer 360','Primary Bank Segment','Average Products per Customer',24,653)
    bar('primary_banking','engagement','Demo Customer 360','Primary Bank Segment','Average Engagement Score',728,653)
    matrix('primary_banking','opportunities','Demo Customer 360','Customer Value Segment',['Customers','Payroll Opportunity Customers','Cross-Sell Opportunity Customers','High Value Low Engagement Customers','Engagement Balance'])

    frame('services','Value-Added Services',[('Demo Service','Service Name'),('Demo Customer 360','Country'),('Demo Customer 360','Engagement Segment')])
    cards('services',['Eligible Service Customers','Offered Service Customers','Activated Service Customers','Service Activation Rate','Active Service Customers'])
    funnel('services','Service',24,380)
    bar('services','service_rate','Demo Service','Service Name','Service Activation Rate',728,380)
    bar('services','value','Demo Customer 360','Customer Value Segment','Service Adoption Rate',24,653)
    bar('services','country','Demo Customer 360','Country','Service Adoption Rate',728,653)
    matrix('services','primary','Demo Customer 360','Primary Bank Segment',['Eligible ServiceRelationships'.replace('ServiceRelationships','Service Relationships'),'Offered Service Relationships','Activated Service Relationships','Active Service Relationships','Average Service Usage'])

    frame('satisfaction','Customer Satisfaction',[('Demo Date','Month'),('Demo Satisfaction','Channel'),('Demo Customer 360','Primary Customer Segment')])
    cards('satisfaction',['NPS','Average Satisfaction','Resolution Rate','Survey Responses','Promoter %','Detractor %'])
    bar('satisfaction','groups','Demo Satisfaction','Nps Group','Survey Responses',24,380)
    bar('satisfaction','channel','Demo Satisfaction','Channel','NPS',728,380)
    bar('satisfaction','month','Demo Date','Month','NPS',24,653)
    bar('satisfaction','feedback','Demo Satisfaction','Feedback Category','Survey Responses',728,653)
    matrix('satisfaction','engagement','Demo Customer 360','Engagement Segment',['Survey Responses','NPS','Average Satisfaction','Resolution Rate'])

    # Bridge measures respect the original Customer-ID drill-through without joining the two stars.
    text('customer_detail','synthetic_banner','SYNTHETIC DEMO DATA — behavioral Customer 360; select one customer through drill-through',24,930,1392,35,12,'#9F5561')
    visual('customer_detail','synthetic_profile','tableEx',24,979,1392,220,'Synthetic relationship profile — blank until one customer is selected',{'Values':[m('Demo '+v) for v in ['Detail Product Depth','Detail Payroll Amount','Detail Engagement','Detail Primary Score','Detail Active Services','Detail Campaign Conversions','Detail Latest NPS Score','Detail Opportunity Flags']]})
    button('overview','demo_entry','Synthetic Digital Demo','digital_overview',24,1150,250)
