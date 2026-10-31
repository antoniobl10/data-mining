"""Render real-Gold design previews from authored PBIR layouts, not native screenshots."""
from pathlib import Path
import json
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from tools.validate_powerbi_metrics import load_data,reference
from tools.build_powerbi_model import ROOT,PBI

NAVY='#142D4E';TEAL='#167D9A';BG='#F4F7FA';MUTED='#617187'
COLORS={'Low':'#65768C','Medium':'#167D9A','High':'#3B8C78','Premium':'#BD8E32','Unknown':'#9F5561'}
SOURCE={'Country':'country','Gender':'gender','Age Group':'age_group','Credit Band':'credit_score_band','Tenure Band':'tenure_band','Customer Value Segment':'customer_value_segment','Primary Customer Segment':'primary_customer_segment','Customer ID':'customer_id','Data Quality Status':'data_quality_status'}


def fmt(name,value):
    if value is None or pd.isna(value):return 'Unavailable'
    if isinstance(value,str):return value
    if '%' in name:return f'{value:.1%}'
    if any(x in name for x in ['Balance','Salary']) and 'Customers' not in name:
        return f'€{value/1e6:.2f}M' if abs(value)>=1e6 else f'€{value/1e3:.1f}K' if abs(value)>=1e3 else f'€{value:,.0f}'
    if any(x in name for x in ['Age','Tenure','Value Score']):return f'{value:.1f}'
    return f'{value:,.0f}'


def render():
    font=Path('C:/Windows/Fonts/segoeui.ttf')
    if font.exists():font_manager.fontManager.addfont(font);plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name()
    manifest,base=load_data()
    source=Path(manifest['parquet_path'])
    customer=pd.read_parquet(source/'dim_customer.parquet')
    base=base.merge(customer[['customer_key','customer_id','data_quality_status']],on='customer_key',validate='one_to_one')
    kpi=pd.read_parquet(source/'mart_customer_kpis.parquet').iloc[0]
    concentrations=pd.read_parquet(source/'mart_balance_concentration.parquet')
    validation=pd.read_parquet(Path(manifest['quality_path'])/'gold_validation_report.parquet')
    all_metrics=reference(base)
    meta={'Snapshot Records Processed':manifest['upstream_silver_manifest']['bronze_rows'],'Snapshot Silver Customers':manifest['upstream_silver_manifest']['silver_rows'],'Snapshot Quarantined Records':manifest['upstream_silver_manifest']['quarantine_rows'],'Silver Checks Failed':manifest['upstream_silver_manifest']['quality_statuses'].get('FAIL',0),'Gold Checks Passed':int(validation.status.eq('PASS').sum()),'Gold Checks Failed':int(validation.status.eq('FAIL').sum())}
    def measure(name,data):
        values=reference(data)
        if name in values:return values[name]
        if name in meta:return meta[name]
        if name.endswith(' Title'):return name[:-6]+' — All Countries'
        if name=='Portfolio Insight':
            leaders=data.groupby('country').balance.sum(min_count=1).sort_values(ascending=False)
            return f'Largest observed balance: {leaders.index[0]}. Premium: {values["Premium Customer %"]:.1%}. Balance coverage: {values["Balance Coverage %"]:.1%}. Value is an analytical proxy.'
        if name=='Customer Share %':return len(data)/len(base)
        if name=='Country Average Balance':return base.loc[base.country.isin(data.country.unique()),'balance'].mean()
        if name=='Overall Average Balance':return all_metrics['Average Balance']
        if name=='Balance Difference vs Overall':return values['Average Balance']-all_metrics['Average Balance']
        if name=='Balance Difference %':return (values['Average Balance']-all_metrics['Average Balance'])/all_metrics['Average Balance']
        return np.nan
    output=PBI/'previews';output.mkdir(exist_ok=True)
    for page_file in sorted((PBI/'BankingCustomerAnalytics.Report/definition/pages').glob('*/page.json')):
        page=json.loads(page_file.read_text(encoding='utf-8'))
        if page['name'] not in ['overview','customers','financial','segments','explorer','customer_detail','country_tooltip','segment_tooltip','quality']:continue
        w,h=page['width'],page['height']
        fig=plt.figure(figsize=(w/100,h/100),facecolor=BG)
        data=base.loc[base.customer_value_segment.eq('Premium')].iloc[:1] if page['name']=='customer_detail' else base.loc[base.country.eq('France')] if page['name']=='country_tooltip' else base.loc[base.primary_customer_segment.eq('High Value')] if page['name']=='segment_tooltip' else base
        visuals=[json.loads(p.read_text(encoding='utf-8')) for p in (page_file.parent/'visuals').glob('*/visual.json')]
        for visual in sorted(visuals,key=lambda v:v['position'].get('z',0)):
            pos=visual['position'];x,y,vw,vh=[pos[n] for n in ['x','y','width','height']]
            ax=fig.add_axes([x/w,1-(y+vh)/h,vw/w,vh/h],facecolor='white')
            cfg=visual['visual'];kind=cfg['visualType'];roles=cfg.get('query',{}).get('queryState',{})
            if 'Demo ' in json.dumps(roles):continue
            annotations={a['name']:a['value'] for a in visual.get('annotations',[])}
            title=cfg['visualContainerObjects']['title'][0]['properties'].get('text',{}).get('expr',{}).get('Literal',{}).get('Value',"''")[1:-1]
            if kind=='textbox':
                ax.set_facecolor(BG);ax.axis('off');plain=annotations.get('plainText','')
                size=20 if visual['name']=='heading' else 9 if visual['name'] in ['brand','footer'] else 10
                if visual['name']=='footer':plain='DESIGN PREVIEW • Real Gold values; not native Power BI rendering • EUR unverified'
                ax.text(0,.8,'\n'.join(textwrap.wrap(plain,max(35,int(vw/(size*.55))))),ha='left',va='top',fontsize=size,color=TEAL if visual['name']=='brand' else NAVY if visual['name']=='heading' else MUTED,transform=ax.transAxes)
            elif kind=='actionButton':
                selected=annotations.get('actionTarget')==page['name']
                ax.set_facecolor(TEAL if selected else '#E4EDF3');ax.text(.5,.5,annotations.get('buttonLabel',''),ha='center',va='center',fontsize=10,color='white' if selected else NAVY,transform=ax.transAxes)
                ax.set_xticks([]);ax.set_yticks([])
            elif kind=='slicer':
                ax.text(.04,.78,title,fontsize=9,color=MUTED,transform=ax.transAxes);ax.text(.04,.28,'All',fontsize=12,color=NAVY,transform=ax.transAxes);ax.text(.94,.3,'v',fontsize=10,color=NAVY,transform=ax.transAxes);ax.set_xticks([]);ax.set_yticks([])
            elif kind=='card':
                item=roles['Values']['projections'][0];name=item['field']['Measure']['Property'];value=measure(name,data)
                ax.set_xticks([]);ax.set_yticks([])
                if name.endswith(' Title'):
                    ax.set_facecolor(BG);ax.text(0,.5,value,va='center',fontsize=21,color=NAVY,transform=ax.transAxes)
                else:
                    ax.text(.04,.79,title or name,va='top',fontsize=9,color=MUTED,transform=ax.transAxes)
                    display=fmt(name,value)
                    if isinstance(value,str):
                        ax.text(.04,.52,'\n'.join(textwrap.wrap(display,max(30,int(vw/7.0)))),va='top',fontsize=12,color=NAVY,transform=ax.transAxes)
                    else:ax.text(.04,.21,display,fontsize=24 if vw>180 else 20,color=NAVY,weight='bold',transform=ax.transAxes)
            elif kind in ['clusteredBarChart','clusteredColumnChart']:
                category=roles['Category']['projections'][0]['field']['Column']['Property']
                metric=roles['Y']['projections'][0]['field']['Measure']['Property']
                if category=='Cohort':values=concentrations.set_index('cohort').balance_share
                else:
                    field=SOURCE[category]
                    values=pd.Series({name:measure(metric,group) for name,group in data.groupby(field,dropna=False)})
                    order={'Age Group':['Unknown','18–25','26–35','36–45','46–55','56–65','66+'],'Credit Band':['Unknown','Poor','Fair','Good','Very Good','Excellent'],'Tenure Band':['Unknown','New','Established','Loyal','Long-Term'],'Customer Value Segment':['Low','Medium','High','Premium','Unknown']}.get(category)
                    values=values.reindex([name for name in order if name in values.index]) if order else values.sort_values(ascending=False)
                ax.set_axis_off()
                chart=fig.add_axes([(x+145)/w,1-(y+vh-32)/h,(vw-165)/w,(vh-85)/h],facecolor='white')
                colors=[COLORS.get(str(label),TEAL) if category=='Customer Value Segment' else TEAL for label in values.index]
                labels=[str(label).replace('High Credit Quality','High Credit').replace('Long-Term Customer','Long-Term') for label in values.index]
                chart.barh(labels,values,color=colors,height=.6);chart.invert_yaxis();chart.tick_params(labelsize=8,length=0)
                chart.grid(axis='x',alpha=.12);chart.set_axisbelow(True)
                if '%' in metric or 'Concentration' in metric:chart.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x:.0%}'))
                elif any(s in metric for s in ['Balance','Salary']) and 'Customers' not in metric:chart.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1e6:.0f}M' if abs(x)>=1e6 else f'{x/1e3:.0f}K'))
                chart.spines[['top','right','left']].set_visible(False)
                fig.text((x+12)/w,1-(y+24)/h,title,fontsize=10,weight='bold',color=NAVY)
            elif kind=='scatterChart':
                ax.axis('off');plot=fig.add_axes([(x+62)/w,1-(y+vh-42)/h,(vw-80)/w,(vh-100)/h])
                xname=roles['X']['projections'][0]['field']['Measure']['Property'];xcol='estimated_salary' if 'Salary' in xname else 'credit_score'
                valid=data[[xcol,'balance','customer_value_segment']].dropna(subset=[xcol,'balance'])
                plot.scatter(valid[xcol],valid.balance,c=[COLORS[x] for x in valid.customer_value_segment],s=8,alpha=.35)
                plot.tick_params(labelsize=8);plot.set_xlabel(xname,fontsize=9);plot.set_ylabel('Observed balance',fontsize=9);plot.spines[['top','right']].set_visible(False)
                plot.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1e3:.0f}K'))
                if xcol=='estimated_salary':plot.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x/1e3:.0f}K'))
                fig.text((x+12)/w,1-(y+24)/h,title+f' • {len(valid)} complete pairs',fontsize=10,weight='bold',color=NAVY)
            elif kind in ['tableEx','pivotTable']:
                ax.axis('off')
                result=[]
                fields=roles.get('Values',{}).get('projections',[])
                if 'Rows' in roles:
                    row=roles['Rows']['projections'][0]['field']['Column']['Property'];groups=list(data.groupby(SOURCE[row]))
                    headings=[row]+[item['displayName'] for item in fields]
                    result=[[label]+[fmt(item['displayName'],measure(item['displayName'],group)) for item in fields] for label,group in groups]
                elif page['name']=='quality':
                    if visual['name']=='lineage':headings=['Gold Build','Source Batch','Build Timestamp'];result=[[manifest['gold_build_id'],manifest['source_batch_id'],manifest['gold_build_timestamp']]]
                    else:headings=['Check','Checked','Failed','Status'];result=validation[['check_name','records_checked','failed_records','status']].head(12).values.tolist()
                else:
                    headings=[item['displayName'] for item in fields]
                    for _,row in data.head(12 if page['name']=='explorer' else 1).iterrows():
                        group=data.loc[data.customer_key.eq(row.customer_key)]
                        result.append([fmt(item['displayName'],measure(item['displayName'],group)) if 'Measure' in item['field'] else ('…'+str(row.customer_id)[-4:] if item['field']['Column']['Property']=='Customer ID' else str(row.get(SOURCE.get(item['field']['Column']['Property'],''),''))) for item in fields])
                headings=['\n'.join(textwrap.wrap(str(x),16)) for x in headings]
                table=ax.table(cellText=result,colLabels=headings,cellLoc='left',loc='upper center',bbox=[.01,.03,.98,.78])
                table.auto_set_font_size(False);table.set_fontsize(9 if len(headings)<8 else 7)
                for (r,col),cell in table.get_celld().items():cell.set_edgecolor('#E1E7ED');cell.set_facecolor('#E7EFF4' if r==0 else '#FFFFFF' if r%2 else '#F7F9FB');cell.set_text_props(color=NAVY)
                fig.text((x+12)/w,1-(y+24)/h,title,fontsize=10,weight='bold',color=NAVY)
            else:ax.axis('off')
            for spine in ax.spines.values():spine.set_visible(False)
        fig.savefig(output/(page['name']+'.png'),dpi=140,facecolor=BG)
        plt.close(fig)
    print('Rendered original nine design previews only. Synthetic pages require native screenshots; Explorer IDs are masked.')


if __name__=='__main__':render()
