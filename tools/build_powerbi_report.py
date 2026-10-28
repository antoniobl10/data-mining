"""Author PBIR native visuals, pages, navigation, bookmarks and a restrained theme."""
from pathlib import Path
import json
import re
from tools.build_powerbi_model import ROOT,PBI,write

BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
REPORT=PBI/'BankingCustomerAnalytics.Report'
DEFINITION=REPORT/'definition'
NAVY='#142D4E'; TEAL='#167D9A'; BG='#F4F7FA'; MUTED='#617187'
MAIN=[('overview','Executive Overview'),('customers','Customer Profile'),('financial','Financial Analysis'),('segments','Segmentation'),('explorer','Customer Explorer')]
PAGES={}


def lit(value):
    text='true' if value is True else 'false' if value is False else str(value)+'D' if isinstance(value,(int,float)) else "'"+value.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':text}}}


def field(table,property,measure=False):
    return {'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':property}}


def projection(table,property,measure=False):
    return {'field':field(table,property,measure),'queryRef':table+'.'+property,'nativeQueryRef':property,'displayName':property}


def m(name):return projection('_Measures',name,True)
def c(table,name):return projection(table,name)


def visual(page,name,type,x,y,w,h,title,roles=None,tooltip=None):
    items=PAGES[page]['visuals']
    container={'title':[{'properties':{'show':lit(True),'text':lit(title),'fontSize':lit(13),'fontColor':{'solid':{'color':lit(NAVY)}},'fontFamily':lit('Segoe UI Semibold'),'titleWrap':lit(True)}}],
    'background':[{'properties':{'show':lit(True),'color':{'solid':{'color':lit('#FFFFFF')}},'transparency':lit(0)}}],
    'general':[{'properties':{'altText':lit(title+'; based on the selected accepted-customer snapshot.')}}],
    'border':[{'properties':{'show':lit(False)}}], 'subTitle':[{'properties':{'show':lit(False)}}]}
    data={'$schema':BASE+'visualContainer/2.4.0/schema.json','name':name,'position':{'x':x,'y':y,'width':w,'height':h,'z':len(items),'tabOrder':len(items)},'visual':{'visualType':type,'visualContainerObjects':container,'drillFilterOtherVisuals':True}}
    if roles: data['visual']['query']={'queryState':{role:{'projections':values} for role,values in roles.items()}}
    if tooltip: container['visualTooltip']=[{'properties':{'show':lit(True),'type':lit('Canvas'),'section':lit(tooltip)}}]
    items.append(data)
    return data


def text(page,name,text,x,y,w,h,size=12,color=MUTED):
    v=visual(page,name,'textbox',x,y,w,h,'')
    v['visual']['visualContainerObjects']['title'][0]['properties']['show']=lit(False)
    v['visual']['visualContainerObjects']['background'][0]['properties']['transparency']=lit(100)
    v['visual']['visualContainerObjects']['padding']=[{'properties':{side:lit(0) for side in ['top','bottom','left','right']}}]
    v['visual']['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':color}}]}]}}]}
    v['annotations']=[{'name':'plainText','value':text}]
    return v


def button(page,name,label,target,x,y,w=150,action='PageNavigation'):
    v=visual(page,name,'actionButton',x,y,w,44,'')
    v['visual']['visualContainerObjects']['title'][0]['properties']['show']=lit(False)
    v['visual']['visualContainerObjects']['visualLink']=[{'properties':{'show':lit(True),'type':lit(action), 'bookmark' if action=='Bookmark' else 'navigationSection' if action=='PageNavigation' else 'tooltip':lit(target)}}]
    selected=page==target
    v['visual']['visualContainerObjects']['background'][0]['properties']['show']=lit(False)
    v['visual']['objects']={
        'text':[{'properties':{'show':lit(True)}},{'selector':{'id':'default'},'properties':{'text':lit(label),'fontSize':lit(11),'horizontalAlignment':lit('center'),'fontColor':{'solid':{'color':lit('#FFFFFF' if selected else NAVY)}}}}],
        'fill':[{'properties':{'show':lit(True)}},{'selector':{'id':'default'},'properties':{'fillColor':{'solid':{'color':lit(TEAL if selected else '#E4EDF3')}}}}],
        'icon':[{'properties':{'show':lit(False)}},{'selector':{'id':'default'},'properties':{'placement':lit('left')}}],
        'shape':[{'properties':{'tileShape':lit('rectangleRounded'),'roundEdge':lit(6)}},{'selector':{'id':'default'},'properties':{'tileShape':lit('rectangleRounded')}}],
        'outline':[{'properties':{'show':lit(False)}}]}
    v['annotations']=[{'name':'buttonLabel','value':label},{'name':'actionTarget','value':target}]
    return v


def new_page(name,title,hidden=False,type=None,width=1440,height=1240):
    page={'$schema':BASE+'page/2.0.0/schema.json','name':name,'displayName':title,'displayOption':'FitToWidth' if not type else 'ActualSize','height':height,'width':width,'objects':{'background':[{'properties':{'color':{'solid':{'color':lit(BG)}},'transparency':lit(0)}}]}}
    if hidden:page['visibility']='HiddenInViewMode'
    if type:page['type']=type
    PAGES[name]={'page':page,'visuals':[]}
    return page


def slicer(page,table,col,x,y,w):
    slug=re.sub('[^a-z0-9]','_',col.lower())
    v=visual(page,'slicer_'+slug,'slicer',x,y,w,76,col,{'Values':[c(table,col)]})
    v['visual']['visualContainerObjects']['title'][0]['properties']['show']=lit(False)
    v['visual']['syncGroup']={'groupName':'sync_'+slug,'fieldChanges':True,'filterChanges':True}
    v['visual']['objects']={'data':[{'properties':{'mode':lit('Dropdown')}}], 'selection':[{'properties':{'singleSelect':lit(False),'selectAllCheckboxEnabled':lit(True)}}]}
    return v


def frame(page,title,question,slicers=None):
    new_page(page,title)
    text(page,'brand','BANKING / CUSTOMER ANALYTICS',24,16,700,25,10,TEAL)
    heading=text(page,'heading',title,24,44,1000,44,20,NAVY)
    if page!='overview':
        heading['visual']['visualType']='card'
        heading['visual']['query']={'queryState':{'Values':{'projections':[m(title+' Title')]}}}
        heading['visual']['objects']={'labels':[{'properties':{'fontSize':lit(18),'color':{'solid':{'color':lit(NAVY)}}}}],'categoryLabels':[{'properties':{'show':lit(False)}}]}
    for i,(target,label) in enumerate(MAIN):button(page,'nav_'+target,{'overview':'Overview','customers':'Customers','financial':'Financial','segments':'Segments','explorer':'Explorer'}[target],target,24+i*160,91)
    button(page,'reset','Reset Filters','reset_all',1250,91,166,'Bookmark')
    selectors=slicers or [('Dim Country','Country'),('Dim Customer','Gender'),('Dim Customer','Customer Value Segment')]
    width=(1392-16*(len(selectors)-1))/len(selectors)
    for i,(table,col) in enumerate(selectors):slicer(page,table,col,24+i*(width+16),139,width)
    text(page,'question',question,24,220,1392,34,11)
    text(page,'footer','Snapshot analytics • EUR is an unverified display assumption • Value score is a proxy • Missing amounts remain unknown',24,1197,1200,25,10)
    button(page,'quality_navigation','Data Quality','quality',1240,1189,176)


def cards(page,names,y=258):
    width=(1392-16*(len(names)-1))/len(names)
    for i,name in enumerate(names):
        v=visual(page,'kpi_'+str(i),'card',24+i*(width+16),y,width,100,name,{'Values':[m(name)]})
        v['visual']['visualContainerObjects']['title'][0]['properties']['fontSize']=lit(10)
        v['visual']['visualContainerObjects']['padding']=[{'properties':{side:lit(2) for side in ['top','bottom','left','right']}}]
        v['visual']['objects']={'labels':[{'properties':{'fontSize':lit(18),'color':{'solid':{'color':lit(NAVY)}}}}], 'categoryLabels':[{'properties':{'show':lit(False)}}]}
        props=v['visual']['objects']['labels'][0]['properties']
        props['labelDisplayUnits']=lit(0 if '%' in name or 'Customers' in name or 'Credit' in name or 'Age' in name or 'Tenure' in name or 'Score' in name else 1000000 if name=='Total Balance' else 1000)
        props['labelPrecision']=lit(1 if '%' in name or name=='Total Balance' else 0)


def chart(page,name,table,col,measure,x,y,w=453,h=265,title=None,tooltip=None,kind='clusteredBarChart'):
    v=visual(page,name,kind,x,y,w,h,title or measure+' by '+col,{'Category':[c(table,col)],'Y':[m(measure)],'Tooltips':[m('Balance Coverage %'),m('Score Coverage %')]},tooltip)
    sortfield=field(table,col) if table in ['Dim Age Group','Dim Credit Band','Dim Tenure Band'] or col=='Customer Value Segment' else field('_Measures',measure,True)
    v['visual']['query']['sortDefinition']={'sort':[{'field':sortfield,'direction':'Ascending' if sortfield.get('Column') else 'Descending'}],'isDefaultSort':True}
    v['visual']['objects']={'dataPoint':[{'properties':{'defaultColor':{'solid':{'color':lit(TEAL)}}}}], 'legend':[{'properties':{'show':lit(False)}}], 'categoryAxis':[{'properties':{'fontSize':lit(10)}}], 'valueAxis':[{'properties':{'fontSize':lit(10),'labelDisplayUnits':lit(1000000 if measure=='Total Balance' else 1000 if 'Balance' in measure or 'Salary' in measure else 0),'labelPrecision':lit(0)}}]}
    return v


def build():
    frame('overview','Executive Overview','How large is the accepted portfolio, where are observed balances held, and how complete is the evidence?')
    cards('overview',['Total Customers','Total Balance','Average Balance','Average Credit Score','Average Estimated Salary','Premium Customer %'])
    charts=[('country_customers','Dim Country','Country','Total Customers','country_tooltip'),('country_balance','Dim Country','Country','Total Balance','country_tooltip'),('value_mix','Dim Customer','Customer Value Segment','Total Customers',None),('credit_mix','Dim Credit Band','Credit Band','Total Customers',None),('age_mix','Dim Age Group','Age Group','Total Customers',None),('segment_mix','Dim Customer','Primary Customer Segment','Total Customers','segment_tooltip')]
    for i,(name,table,col,measure,tooltip) in enumerate(charts):chart('overview',name,table,col,measure,24+(i%3)*469,369+(i//3)*283,tooltip=tooltip)
    narrative=visual('overview','insight','card',24,941,1392,116,'Portfolio insight',{'Values':[m('Portfolio Insight')]})
    narrative['visual']['objects']={'labels':[{'properties':{'fontSize':lit(14),'color':{'solid':{'color':lit(NAVY)}}}}],'categoryLabels':[{'properties':{'show':lit(False)}}]}
    text('overview','coverage_note','Read balances with coverage: unknown balances are excluded from financial averages. High Value and Premium describe a relative analytical proxy.',24,1075,1392,70,12)

    frame('customers','Customer Profile','Who are our customers, and how do observed financial profiles differ across age groups?', [('Dim Country','Country'),('Dim Customer','Gender'),('Dim Age Group','Age Group'),('Dim Tenure Band','Tenure Band'),('Dim Credit Band','Credit Band')])
    cards('customers',['Total Customers','Average Age','Average Tenure','Average Credit Score'])
    charts=[('age','Dim Age Group','Age Group','Total Customers'),('gender','Dim Customer','Gender','Total Customers'),('country','Dim Country','Country','Total Customers'),('tenure','Dim Tenure Band','Tenure Band','Total Customers'),('age_balance','Dim Age Group','Age Group','Average Balance'),('age_salary','Dim Age Group','Age Group','Average Estimated Salary')]
    for i,(name,table,col,measure) in enumerate(charts):chart('customers',name,table,col,measure,24+(i%3)*469,369+(i//3)*283,h=235)
    visual('customers','age_profile_matrix','pivotTable',24,905,1392,256,'Age profile: observed averages and coverage',{'Rows':[c('Dim Age Group','Age Group')],'Values':[m(name) for name in ['Total Customers','Average Balance','Average Estimated Salary','Average Credit Score','Average Tenure','Balance Coverage %']]})

    frame('financial','Financial Analysis','What financial patterns and observed-balance concentration are present?', [('Dim Country','Country'),('Dim Credit Band','Credit Band'),('Dim Tenure Band','Tenure Band'),('Dim Customer','Customer Value Segment')])
    cards('financial',['Total Balance','Median Balance','Average Estimated Salary','Average Credit Score','Balance Coverage %'])
    charts=[('country_total','Dim Country','Country','Total Balance'),('country_average','Dim Country','Country','Average Balance'),('country_salary','Dim Country','Country','Average Estimated Salary'),('credit_balance','Dim Credit Band','Credit Band','Average Balance'),('tenure_balance','Dim Tenure Band','Tenure Band','Average Balance')]
    for i,(name,table,col,measure) in enumerate(charts):chart('financial',name,table,col,measure,24+(i%3)*469,369+(i//3)*249,h=225)
    visual('financial','concentration','clusteredColumnChart',962,618,453,225,'Observed balance concentration',{'Category':[c('Balance Concentration','Cohort')],'Y':[m('Balance Concentration Share')]})
    for name,xmeasure in [('salary_balance','Average Estimated Salary'),('credit_balance_scatter','Average Credit Score')]:
        x=24 if name=='salary_balance' else 728
        visual('financial',name,'scatterChart',x,867,688,294,'Salary vs balance' if name=='salary_balance' else 'Credit score vs balance',{'Category':[c('Dim Customer','Customer ID')],'X':[m(xmeasure)],'Y':[m('Average Balance')],'Size':[m('Total Customers')],'Series':[c('Dim Customer','Customer Value Segment')],'Tooltips':[m('Average Customer Value Score'),m('Average Tenure'),m('Balance Coverage %')]})

    frame('segments','Segmentation','Which explainable cohorts merit investigation, and how complete are their value scores?', [('Dim Country','Country'),('Dim Customer','Primary Customer Segment'),('Dim Customer','Customer Value Segment')])
    cards('segments',['High Value Customers','High Value Customer %','Premium Customer %','High Balance Customers','Long-Term Customers','Score Coverage %'])
    specs=[('segment_count','Dim Customer','Primary Customer Segment','Total Customers'),('segment_balance','Dim Customer','Primary Customer Segment','Total Balance'),('premium_country','Dim Country','Country','Premium Customers'),('highvalue_age','Dim Age Group','Age Group','High Value Customers')]
    for i,(name,table,col,measure) in enumerate(specs):chart('segments',name,table,col,measure,24+(i%2)*704,369+(i//2)*249,w=688,h=225,tooltip='segment_tooltip' if col=='Primary Customer Segment' else 'country_tooltip' if col=='Country' else None)
    visual('segments','segment_profile','pivotTable',24,867,1392,294,'Segment profiles — counts, observed averages and selected share',{'Rows':[c('Dim Customer','Primary Customer Segment')],'Values':[m(n) for n in ['Total Customers','Customer Share %','Average Balance','Average Estimated Salary','Average Credit Score','Average Tenure','Average Customer Value Score']]},'segment_tooltip')

    frame('explorer','Customer Explorer','Authorized analyst view: customer identifiers and financial profiles. Hiding fields/pages is not access control.', [('Dim Country','Country'),('Dim Customer','Gender'),('Dim Customer','Customer Value Segment'),('Dim Customer','Primary Customer Segment')])
    cards('explorer',['Total Customers','Average Balance','Average Credit Score','Average Customer Value Score'])
    cols=[c('Dim Customer','Customer ID'),c('Dim Country','Country'),c('Dim Customer','Gender'),m('Average Age'),m('Average Tenure'),m('Average Credit Score'),c('Dim Credit Band','Credit Band'),m('Average Balance'),m('Average Estimated Salary'),m('Average Customer Value Score'),c('Dim Customer','Customer Value Segment'),c('Dim Customer','Primary Customer Segment')]
    v=visual('explorer','customer_table','tableEx',24,369,1392,792,'Customer profiles — right-click a customer to drill through',{'Values':cols})
    v['visual']['objects']={'grid':[{'properties':{'textSize':lit(10)}}], 'columnWidth':[{'selector':{'metadata':item['queryRef']},'properties':{'value':lit(125 if 'Segment' not in item['displayName'] else 190)}} for item in cols]}
    v['visual']['objects']['values']=[{'selector':{'metadata':'_Measures.'+measure},'properties':{'fontColor':{'solid':{'color':{'expr':field('_Measures',color,True)}}}}} for measure,color in [('Average Balance','Balance Cell Color'),('Average Credit Score','Credit Cell Color'),('Average Customer Value Score','Value Cell Color')]]

    page=new_page('customer_detail','Customer Detail',True,'Drillthrough')
    page['pageBinding']={'name':'customer_drill','type':'Drillthrough','parameters':[{'name':'customer_id','boundFilter':'drill_customer_id','fieldExpr':field('Dim Customer','Customer ID')}],'acceptsFilterContext':'Default'}
    page['filterConfig']={'filters':[{'name':'drill_customer_id','field':field('Dim Customer','Customer ID'),'type':'Categorical','howCreated':'Drillthrough'}]}
    text('customer_detail','heading','Customer Detail — authorized analysts',24,24,1100,50,25,NAVY)
    button('customer_detail','back','Back to Explorer','explorer',24,91,180)
    cards('customer_detail',['Average Balance','Average Estimated Salary','Average Credit Score','Average Tenure','Average Customer Value Score'],169)
    visual('customer_detail','identity','tableEx',24,290,1392,220,'Profile and source-data quality',{'Values':[c('Dim Customer','Customer ID'),c('Dim Country','Country'),c('Dim Customer','Gender'),m('Average Age'),c('Dim Customer','Customer Value Segment'),c('Dim Customer','Primary Customer Segment'),c('Dim Customer','Data Quality Status')]})
    visual('customer_detail','comparisons','tableEx',24,550,1392,200,'Observed balance comparisons',{'Values':[m('Average Balance'),m('Country Average Balance'),m('Overall Average Balance'),m('Balance Difference vs Overall'),m('Balance Difference %')]})
    text('customer_detail','limits','No transaction history is available. Country and overall comparisons use observed valid balances. Value score is a proxy. Export customer detail only under authorized access.',24,790,1392,110,13)

    for name,title,table,col,names in [('country_tooltip','Country Tooltip','Dim Country','Country',['Total Customers','Total Balance','Average Balance','Average Credit Score','Premium Customer %','Balance Coverage %']),('segment_tooltip','Segment Tooltip','Dim Customer','Primary Customer Segment',['Total Customers','Average Balance','Average Estimated Salary','Average Credit Score','Average Customer Value Score','Score Coverage %'])]:
        p=new_page(name,title,True,'Tooltip',640,470)
        p['pageBinding']={'name':name+'_binding','type':'Tooltip','parameters':[{'name':name+'_field','fieldExpr':field(table,col)}]}
        text(name,'heading',title,16,10,608,32,18,NAVY)
        for i,measure in enumerate(names):visual(name,'metric_'+str(i),'card',16+(i%2)*312,60+(i//2)*118,296,102,measure,{'Values':[m(measure)]})
        text(name,'note','Observed inputs only • unknown scores are not Low value',16,425,608,30,10)

    new_page('quality','Data Quality',True)
    text('quality','heading','Data Quality & Pipeline Transparency',24,24,1392,50,25,NAVY)
    button('quality','back','Overview','overview',24,91,160)
    cards('quality',['Snapshot Records Processed','Snapshot Silver Customers','Snapshot Quarantined Records','Silver Checks Failed','Gold Checks Passed','Gold Checks Failed'],162)
    visual('quality','lineage','tableEx',24,290,1392,170,'Technical build lineage — not business observation dates',{'Values':[c('Pipeline Status','Gold Build'),c('Pipeline Status','Source Batch'),c('Pipeline Status','Build Timestamp')]})
    text('quality','quality_note','Source failures remain visible. Critical records are quarantined; accepted Silver still includes missing-value warnings.',24,466,1392,28,11)
    visual('quality','checks','tableEx',24,505,1392,650,'Gold validation checks',{'Values':[c('Gold Validation',col) for col in ['Check','Records Checked','Failed Records','Status','Detail']]})

    # Explicit filter interactions avoid ambiguous cross-highlighting.
    for name,content in PAGES.items():
        data=[v for v in content['visuals'] if v['visual'].get('query') and v['visual']['visualType'] not in ['card','tableEx','pivotTable']]
        targets=[v for v in content['visuals'] if v['visual'].get('query')]
        content['page']['visualInteractions']=[{'source':s['name'],'target':t['name'],'type':'DataFilter' if t['name']!='concentration' or s['visual']['visualType']=='slicer' else 'NoFilter'} for s in data for t in targets if s['name']!=t['name']]
        for v in content['visuals']:write(DEFINITION/'pages'/name/'visuals'/v['name']/'visual.json',json.dumps(v,indent=2,ensure_ascii=False)+'\n')
        write(DEFINITION/'pages'/name/'page.json',json.dumps(content['page'],indent=2)+'\n')
    write(DEFINITION/'pages/pages.json',json.dumps({'$schema':BASE+'pagesMetadata/1.0.0/schema.json','pageOrder':list(PAGES),'activePageName':'overview'},indent=2)+'\n')
    sections={name:{'visualContainers':{v['name']:{'singleVisual':{'visualType':'slicer','objects':{'remove':[{'object':'general','property':'filter','selector':{}}]}}} for v in data['visuals'] if v['visual']['visualType']=='slicer'}} for name,data in PAGES.items()}
    bookmark={'$schema':BASE+'bookmark/1.0.0/schema.json','name':'reset_all','displayName':'Reset Filters','options':{'suppressActiveSection':True,'suppressDisplay':True,'suppressData':False},'explorationState':{'version':'1.3','activeSection':'overview','sections':sections,'filters':{'byName':{}}}}
    write(DEFINITION/'bookmarks/reset_all.bookmark.json',json.dumps(bookmark,indent=2)+'\n')
    write(DEFINITION/'bookmarks/bookmarks.json',json.dumps({'$schema':BASE+'bookmarksMetadata/1.0.0/schema.json','items':[{'name':'reset_all'}]},indent=2)+'\n')
    theme={'name':'banking_theme.json','dataColors':[TEAL,NAVY,'#3B8C78','#BD8E32','#65768C','#9F5561'],'background':BG,'foreground':NAVY,'tableAccent':TEAL,'textClasses':{'title':{'fontFace':'Segoe UI Semibold','fontSize':14,'color':NAVY},'label':{'fontFace':'Segoe UI','fontSize':11,'color':NAVY},'callout':{'fontFace':'Segoe UI Semibold','fontSize':27,'color':NAVY}}}
    write(PBI/'theme/banking_theme.json',json.dumps(theme,indent=2)+'\n')
    write(REPORT/'StaticResources/RegisteredResources/banking_theme.json',json.dumps(theme,indent=2)+'\n')
    report=json.loads((PBI/'theme/report_shell.json').read_text(encoding='utf-8'))
    report['themeCollection']['customTheme']={'name':'banking_theme.json','reportVersionAtImport':report['themeCollection']['baseTheme']['reportVersionAtImport'],'type':'RegisteredResources'}
    report['resourcePackages'].append({'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'banking_theme.json','path':'banking_theme.json','type':'CustomTheme'}]})
    write(REPORT/'.platform',(PBI/'theme/report_platform.json').read_text(encoding='utf-8'))
    write(REPORT/'StaticResources/SharedResources/BaseThemes/Fluent2-CY26SU10.json',(PBI/'theme/Fluent2-CY26SU10.json').read_text(encoding='utf-8'))
    write(DEFINITION/'report.json',json.dumps(report,indent=2)+'\n')
    write(DEFINITION/'version.json',json.dumps({'$schema':BASE+'versionMetadata/1.0.0/schema.json','version':'2.0.0'},indent=2)+'\n')
    write(REPORT/'definition.pbir',json.dumps({'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../BankingCustomerAnalytics.SemanticModel'}}},indent=2)+'\n')
    write(PBI/'BankingCustomerAnalytics.SemanticModel/definition.pbism',json.dumps({'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.0','settings':{'qnaEnabled':False}},indent=2)+'\n')
    write(PBI/'BankingCustomerAnalytics.pbip',json.dumps({'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'BankingCustomerAnalytics.Report'}}],'settings':{'enableAutoRecovery':True}},indent=2)+'\n')
    inventory={name:{'displayName':data['page']['displayName'],'hidden':data['page'].get('visibility')=='HiddenInViewMode','visuals':len(data['visuals']),'types':[v['visual']['visualType'] for v in data['visuals']]} for name,data in PAGES.items()}
    write(PBI/'model/report_inventory.json',json.dumps(inventory,indent=2)+'\n')
    print('Authored',len(PAGES),'PBIR pages and',sum(len(data['visuals']) for data in PAGES.values()),'visuals.')


if __name__=='__main__':build()
