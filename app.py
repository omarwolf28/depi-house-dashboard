"""King County / DEPI — launch with python app.py."""
import sys
from pathlib import Path
LOCAL = Path(__file__).resolve().parent / '.packages'
if LOCAL.exists():
    sys.path.insert(0, str(LOCAL))
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, State, dcc, html, dash_table
from modeling import load_data, engineer, get_artifacts

raw, data = load_data()
bundle = get_artifacts(data)
BLUE, YELLOW = '#4b91ff', '#f4d35e'
SCALE = ['#17365e', '#438dff', '#71c4de', '#f4d35e']
px.defaults.template = 'plotly_dark'
px.defaults.color_discrete_sequence = [BLUE, YELLOW, '#67d5ce']

def style(fig, height=350):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, Segoe UI, sans-serif', color='#aebbd0', size=12), margin=dict(l=45,r=25,t=40,b=40), height=height, coloraxis_colorbar=dict(thickness=8, title='Price / USD'))
    fig.update_xaxes(gridcolor='#202c3d', zerolinecolor='#202c3d')
    fig.update_yaxes(gridcolor='#202c3d', zerolinecolor='#202c3d')
    return fig

def graph(fig, id=None):
    # Responsive Plotly clears layout.height; an auto-height parent can then
    # collapse on relayout (zoom/drag), especially inside dcc.Loading.
    return dcc.Graph(**({'id':id} if id else {}), figure=fig,
        style={'height':int(fig.layout.height or 350),'width':'100%','minWidth':0},
        config={'displaylogo':False, 'scrollZoom':False}, responsive=True)

def card(label, value, note, cls=''):
    return html.Div([html.Div(label,className='eyebrow'),html.Div(value,className='metric'),html.Div(note,className='muted')],className='stat '+cls)

def table(df):
    return dash_table.DataTable(data=df.to_dict('records'),columns=[{'name':c.replace('_',' ').title(),'id':c} for c in df.columns], page_size=10, sort_action='native', style_table={'overflowX':'auto'},style_header={'backgroundColor':'#162236','color':'#9eafc8','border':'none','fontWeight':'600'},style_cell={'backgroundColor':'#0e1827','color':'#dfe7f4','borderBottom':'1px solid #213047','borderTop':'none','borderLeft':'none','borderRight':'none','padding':'12px','fontFamily':'Segoe UI','textAlign':'left'})

def field(label,key,value,minimum,maximum,step=1):
    return html.Label([html.Span(label),dcc.Input(id=key,type='number',value=value,min=minimum,max=maximum,step=step,debounce=True)], className='field')

FIELDS = [
 ('Bedrooms','bedrooms',3,0,15,1),('Bathrooms','bathrooms',2.25,.5,8,.25),
 ('Living area · sq ft','sqft_living',2000,200,14000,10),('Lot area · sq ft','sqft_lot',6000,500,1700000,10),
 ('Floors','floors',2,1,3.5,.5),('Build year','yr_built',1990,1900,2015,1),
 ('Renovation year · 0 if none','yr_renovated',0,0,2015,1),('Basement · sq ft','sqft_basement',0,0,5000,10),
 ('Quality grade · 1–13','grade',8,1,13,1),('Condition · 1–5','condition',3,1,5,1),
 ('View score · 0–4','view',0,0,4,1),('Waterfront · 0 no / 1 yes','waterfront',0,0,1,1),
 ('Latitude','lat',47.498, float(data.lat.min()),float(data.lat.max()),.0001),('Longitude','long',-122.250,float(data.long.min()),float(data.long.max()),.0001),
 ('Nearby living area · sq ft','sqft_living15',1900,300,7000,10),('Nearby lot area · sq ft','sqft_lot15',6000,500,900000,10)]

def location_map(lat,lon):
    fig = px.scatter_map(data.sample(min(1800,len(data)),random_state=42), lat='lat',lon='long',color='price',color_continuous_scale=SCALE,range_color=[data.price.quantile(.05),data.price.quantile(.95)],hover_data={'price':':$,.0f','sqft_living':True,'zipcode':True},zoom=8.7,center={'lat':lat,'lon':lon},map_style='carto-darkmatter',opacity=.55)
    fig.add_trace(go.Scattermap(lat=[lat],lon=[lon],mode='markers',marker={'size':20,'color':YELLOW},name='Your property',hovertemplate='Your property<extra></extra>'))
    style(fig,420).update_layout(margin=dict(l=0,r=0,t=0,b=0),showlegend=False,coloraxis_showscale=False,uirevision=None)
    return fig

bestrow = bundle['metrics'].iloc[0]
notebook_manifest = bundle['manifest']
notebook_plots = {plot['id']:plot for plot in notebook_manifest['plots']}

def notebook_gallery():
    return html.Div([
        html.Div('EXECUTED NOTEBOOK',className='eyebrow'),
        html.H2('The original analysis, directly from your notebook.'),
        html.P(f"{len(notebook_plots)} original plots · all notebook cells executed · includes five-fold validation and model tuning.",className='muted'),
        html.P(f"Run completed: {pd.Timestamp(notebook_manifest['executed_at']).tz_convert('Africa/Cairo').strftime('%d %b %Y, %H:%M')} Cairo · source: {notebook_manifest['notebook']}",className='fineprint'),
        html.Label([html.Span('Notebook plot'),dcc.Dropdown(id='notebook-plot',options=[{'label':p['title'],'value':p['id']} for p in notebook_plots.values()],value=next(iter(notebook_plots)),clearable=False)],className='field'),
        html.Div(id='notebook-plot-content',className='notebook-output'),
    ],className='panel')

app = Dash(__name__,title='DEPI | King County Homes',update_title='Calculating…')
server = app.server

@server.get('/health')
def health():
    return {'status':'ok','model':bundle['best']}

app.layout = html.Div([
 html.Aside([html.Div([html.Span('◈',className='brand-icon'),' DEPI'],className='brand'),html.Div('PROPERTY INTELLIGENCE',className='brand-sub'),html.Div('KING COUNTY',className='rail-label'),html.A('01  /  Estimate',href='#workspace',id='nav-estimate',n_clicks=0),html.A('02  /  Explore',href='#workspace',id='nav-explore',n_clicks=0),html.A('03  /  Model lab',href='#workspace',id='nav-models',n_clicks=0),html.Div([html.Div('●  LOCAL DATA',className='status'),html.P('Seattle & beyond'),html.Small('Historical sales · 2014–2015')],className='rail-foot')],className='sidebar'),
 html.Main([
  html.Header([html.Div('REAL ESTATE / ANALYTICS',className='eyebrow'),html.Div('●  Model ready',className='badge')]),
  html.Div([html.Div([html.Div('A clearer view of home value.',className='hero-title'),html.P('Explore the market. Understand the drivers. Estimate your next home.',className='hero-copy')]),html.Div(['KC',html.Small('WASHINGTON, US')],className='hero-mark')],className='hero'),
  html.Div([card('Homes analyzed',f'{len(data):,}','Cleaned King County sales'),card('Median sale price',f'${data.price.median():,.0f}','Historical USD · 2014–2015'),card('Test R²',f'{bestrow.r2:.1%}',bundle['best']),card('Typical absolute error',f'${bestrow.mae:,.0f}','Mean error on held-out sales','yellow-stat')],className='stats'),
  html.Div(id='workspace',children=dcc.Tabs(id='tabs',value='estimate',children=[
   dcc.Tab(label='01  House estimator',value='estimate',children=[
    html.Div([html.Div([
     html.Div('BUILD YOUR PROPERTY',className='eyebrow'),html.H2('The details make the difference.'),html.P('Enter a home’s features to estimate its historical sale value.',className='muted'),
     html.Div([html.Label([html.Span('ZIP code'),dcc.Dropdown(id='zipcode',options=[str(z) for z in sorted(data.zipcode.unique())],value='98178',clearable=False)],className='field'),html.Label([html.Span('Sale date'),dcc.DatePickerSingle(id='sale-date',date='2015-01-15',min_date_allowed='2014-05-01',max_date_allowed='2015-05-31',display_format='MMM D, YYYY')],className='field')]+[field(*f) for f in FIELDS],className='form-grid'),
     html.Button('Estimate home value  ↗',id='predict',n_clicks=0,className='primary'),html.Div(id='validation',role='alert',className='validation')
    ],className='panel input-panel'),html.Div([
     html.Div([html.Div('ESTIMATED SALE VALUE',className='eyebrow'),html.Div(id='prediction',className='prediction'),html.Div(id='prediction-detail',className='result-detail'),html.Div('Historical estimate, based on 2014–2015 sales. This is not a current appraisal.',className='fineprint')],className='result-card'),
     html.Div([html.Div([html.H3('Location & nearby sales'),html.Span('● Your property',className='map-key')],className='panel-heading'),html.P('Blue dots show a fixed sample of 1,800 historical sales. Use latitude and longitude to place your home.',className='muted'),dcc.Loading(graph(location_map(47.498,-122.250),'property-map'))],className='panel'),
     html.Div(id='comparables',className='panel')
    ],className='result-column')],className='estimator-grid')]),
   dcc.Tab(label='02  Market explorer',value='explore',children=[html.Div([notebook_gallery(),
    html.Div([html.Div('FROM THE NOTEBOOK',className='eyebrow'),html.H2('Every chart, a different perspective.'),html.P('Interactive versions of the notebook’s exploratory analysis. Filters affect these charts only.',className='muted'),
    html.Div([html.Label([html.Span('Analysis'),dcc.Dropdown(id='analysis',options=[{'label':v,'value':k} for k,v in [('distribution','Price & log-price distributions'),('areas','Living area relationships'),('categories','Quality, views & rooms'),('correlation','Correlation heatmap'),('histograms','Numeric feature distributions'),('geography','Sales geography'),('zipcodes','Top 10 ZIP codes'),('year','Build year & sale month'),('outliers','Outlier boxplots'),('quality','Missing values & data quality')]],value='distribution',clearable=False)],className='field'),html.Label([html.Span('ZIP codes · all by default'),dcc.Dropdown(id='filter-zip',options=[str(z) for z in sorted(data.zipcode.unique())],multi=True,placeholder='All ZIP codes')],className='field')],className='explore-controls'),html.Div(id='filter-summary',className='muted'),dcc.Loading(graph(go.Figure(),'analysis-chart')),html.Div(id='analysis-table')],className='panel')],className='tab-body')]),
   dcc.Tab(label='03  Model lab',value='models',children=[html.Div([
    html.Div([html.Div('TRANSPARENT BY DESIGN',className='eyebrow'),html.H2('See how the notebook models perform.'),html.P(f'Reproducible 80/20 split · random seed 42 · {bundle["train_rows"]:,} training / {bundle["test_rows"]:,} test sales. These are the fitted models and measured results exported from the full notebook run, including XGBoost, five-fold cross-validation, and randomized tuning for Random Forest and Gradient Boosting.',className='muted'),table(bundle['metrics'].drop(columns=['best_parameters'],errors='ignore').replace({np.nan:None}).round(3)),html.H3('Five-fold cross-validation'),table(bundle['cv'].round(4)),html.P('The notebook selects the highest test R². Cross-validation describes baseline stability; tuned-model search scores use three folds. The holdout was used for model selection, so it is not an independent final validation.',className='fineprint')],className='panel'),
    html.Div([html.Div([html.H3('Actual vs. predicted'),graph(style(px.scatter(x=bundle['actual'],y=bundle['predictions'][bundle['best']],labels={'x':'Actual price / USD','y':'Predicted price / USD'},opacity=.35).add_trace(go.Scatter(x=[0,max(bundle['actual'])],y=[0,max(bundle['actual'])],mode='lines',line=dict(color=YELLOW,dash='dash'),showlegend=False))))],className='panel'),html.Div([html.H3('Residuals'),graph(style(px.scatter(x=bundle['predictions'][bundle['best']],y=bundle['actual']-bundle['predictions'][bundle['best']],labels={'x':'Predicted price / USD','y':'Actual − predicted / USD'},opacity=.35).add_hline(y=0,line_color=YELLOW)))],className='panel')],className='chart-grid'),
    html.Div([html.H3('What drives the model?'),html.P('Global importance describes how the fitted model uses features; it does not imply causation.',className='muted'),html.Div(id='importance')],className='panel')],className='tab-body')])
  ],className='app-tabs')),
  html.Footer('DEPI / KING COUNTY   •   Built from your project notebook   •   Prices in historical USD')
 ],className='main')
],className='shell')

@app.callback(Output('tabs','value'),Input('nav-estimate','n_clicks'),Input('nav-explore','n_clicks'),Input('nav-models','n_clicks'),prevent_initial_call=True)
def navigate(*_):
    from dash import ctx
    return ctx.triggered_id.removeprefix('nav-')

@app.callback(Output('notebook-plot-content','children'),Input('notebook-plot','value'))
def show_notebook_plot(plot_id):
    plot = notebook_plots[plot_id]
    return [html.Img(src=plot['src'],alt=plot['title'],className='notebook-image'),dcc.Markdown(plot['insight'],className='muted'),html.A('Open full-resolution plot ↗',href=plot['src'],target='_blank',className='plot-link'),html.P(f"Original notebook cell {plot['cell']} · complete source dataset · ZIP filters below apply only to the interactive charts.",className='fineprint')]

@app.callback(Output('prediction','children'),Output('prediction-detail','children'),Output('property-map','figure'),Output('comparables','children'),Output('validation','children'),Input('predict','n_clicks'),State('zipcode','value'),State('sale-date','date'),*[State(f[1],'value') for f in FIELDS])
def predict(n,zipcode,date,*values):
    from dash import no_update
    try:
        if not zipcode or not date or any(v is None for v in values):
            raise ValueError('Complete all property fields before estimating.')
        row = dict(zip([f[1] for f in FIELDS],values))
        for label,key,_,low,high,step in FIELDS:
            if not np.isfinite(row[key]) or not low <= row[key] <= high or abs((row[key]-low)/step-round((row[key]-low)/step)) > 1e-5 and key not in ['lat','long']:
                raise ValueError(f'{label} must be between {low:g} and {high:g}, in steps of {step:g}.')
        sale = pd.Timestamp(date)
        if not pd.Timestamp('2014-05-01') <= sale <= pd.Timestamp('2015-05-31'):
            raise ValueError('Choose a sale date in the historical dataset period.')
        if row['yr_built'] > sale.year or row['yr_renovated'] > sale.year:
            raise ValueError('Build and renovation years cannot be after the sale year.')
        if row['yr_renovated'] and row['yr_renovated'] < row['yr_built']:
            raise ValueError('Renovation year must be zero or at least the build year.')
        if row['sqft_basement'] > row['sqft_living']:
            raise ValueError('Basement area cannot exceed total living area.')
        row.update(zipcode=zipcode,date=sale)
        estimate = float(bundle['models'][bundle['best']].predict(engineer(pd.DataFrame([row])))[0])
        distance = 6371 * 2*np.arcsin(np.sqrt(np.sin(np.radians(data.lat-row['lat'])/2)**2+np.cos(np.radians(row['lat']))*np.cos(np.radians(data.lat))*np.sin(np.radians(data.long-row['long'])/2)**2))
        nearest = data.assign(distance_km=distance).nsmallest(5,'distance_km')
        comp = nearest[['price','bedrooms','bathrooms','sqft_living','zipcode','distance_km']].copy().round(2)
        return f'${estimate:,.0f}',[html.Span(f'${estimate/row["sqft_living"]:,.0f} / sq ft'),html.Span(f'{bundle["best"]} model')],location_map(row['lat'],row['long']),[html.H3('Five nearest historical sales'),html.P('Selected by geographic distance only; these homes may differ in size and quality.',className='muted'),table(comp)],''
    except (ValueError,TypeError,OverflowError) as exc:
        return no_update,no_update,no_update,no_update,str(exc)

@app.callback(Output('analysis-chart','figure'),Output('analysis-table','children'),Output('filter-summary','children'),Output('analysis-chart','style'),Input('analysis','value'),Input('filter-zip','value'))
def explore(kind,zips):
    df = data[data.zipcode.astype(str).isin(zips)] if zips else data
    extra = None
    summary = f'{len(df):,} cleaned sales selected · exploratory charts use observed sale prices'
    if df.empty:
        return style(go.Figure().add_annotation(text='No sales match these filters',showarrow=False)),None,summary,{'height':350,'width':'100%','minWidth':0}
    if kind == 'distribution':
        fig=make_subplots(rows=1,cols=2,subplot_titles=['Sale price','Log-transformed sale price'])
        for i,series in enumerate([df.price,np.log1p(df.price)],1):
            fig.add_trace(go.Histogram(x=series,nbinsx=50,marker_color=[BLUE,YELLOW][i-1],showlegend=False),row=1,col=i)
        extra=html.P(f'Raw skewness: {df.price.skew():.2f} · Log skewness: {np.log1p(df.price).skew():.2f}',className='muted')
    elif kind == 'areas':
        fig=make_subplots(rows=1,cols=3,subplot_titles=['Living area','Above-ground area','Nearby living area'])
        for i,c in enumerate(['sqft_living','sqft_above','sqft_living15'],1):
            fig.add_trace(go.Scattergl(x=df[c],y=df.price,mode='markers',marker=dict(size=3,color=BLUE,opacity=.25),showlegend=False),row=1,col=i)
            valid=df[[c,'price']].dropna()
            if valid[c].nunique()>1:
                slope,intercept=np.polyfit(valid[c],valid.price,1)
                xx=np.array([valid[c].min(),valid[c].max()])
                fig.add_trace(go.Scatter(x=xx,y=slope*xx+intercept,mode='lines',line_color=YELLOW,showlegend=False),row=1,col=i)
        fig.update_xaxes(title_text='Area / sq ft');fig.update_yaxes(title_text='Price / USD')
    elif kind == 'categories':
        fig=make_subplots(rows=2,cols=3,subplot_titles=['Grade','View','Waterfront','Condition','Bedrooms'])
        for i,c in enumerate(['grade','view','waterfront','condition','bedrooms']):
            fig.add_trace(go.Box(x=df[c],y=df.price,marker_color=BLUE,boxpoints=False,showlegend=False),row=i//3+1,col=i%3+1)
    elif kind == 'correlation':
        corr=df.select_dtypes('number').corr()
        fig=px.imshow(corr,zmin=-1,zmax=1,color_continuous_scale=['#346cdd','#111d30',YELLOW],aspect='auto')
    elif kind == 'histograms':
        cols=list(df.select_dtypes('number').columns)
        fig=make_subplots(rows=int(np.ceil(len(cols)/4)),cols=4,subplot_titles=cols)
        for i,c in enumerate(cols): fig.add_trace(go.Histogram(x=df[c],nbinsx=30,marker_color=BLUE,showlegend=False),row=i//4+1,col=i%4+1)
    elif kind == 'geography':
        fig=px.scatter_map(df,lat='lat',lon='long',color='price',color_continuous_scale=SCALE,hover_data={'price':':$,.0f','zipcode':True,'sqft_living':True},map_style='carto-darkmatter',zoom=8.5,opacity=.5)
    elif kind == 'zipcodes':
        top=df.groupby('zipcode').price.agg(['mean','count']).nlargest(10,'mean').sort_values('mean')
        fig=px.bar(x=top['mean'],y=top.index.astype(str),orientation='h',labels={'x':'Mean sale price / USD','y':'ZIP code'},color=top['mean'],color_continuous_scale=SCALE)
        extra=table(top.reset_index().round(0))
    elif kind == 'year':
        fig=make_subplots(rows=1,cols=2,subplot_titles=['Average price by build year','Average price by sale month'])
        year=df.groupby('yr_built').price.mean(); month=df.groupby(df.date.dt.month).price.mean()
        fig.add_trace(go.Scatter(x=year.index,y=year,mode='lines',line_color=BLUE,showlegend=False),row=1,col=1)
        fig.add_trace(go.Bar(x=month.index,y=month,marker_color=YELLOW,showlegend=False),row=1,col=2)
    elif kind == 'outliers':
        cols=['price','sqft_living','sqft_lot','bedrooms','bathrooms']
        fig=make_subplots(rows=1,cols=5,subplot_titles=cols)
        records=[]
        for i,c in enumerate(cols,1):
            fig.add_trace(go.Box(y=df[c],marker_color=BLUE,boxpoints='outliers',showlegend=False),row=1,col=i)
            q1,q3=df[c].quantile([.25,.75]);iqr=q3-q1
            records.append({'feature':c,'IQR_outliers':int(((df[c]<q1-1.5*iqr)|(df[c]>q3+1.5*iqr)).sum())})
        extra=table(pd.DataFrame(records))
    else:
        missing=raw.isna().sum().sort_values(ascending=False)
        fig=px.bar(x=missing.index,y=missing.values,labels={'x':'Source feature','y':'Missing values in raw data'})
        extra=html.Div([html.P(f'Raw rows: {len(raw):,} · Clean rows: {len(data):,} · Removed duplicates or invalid rooms: {len(raw)-len(data):,}. Missing rooms are imputed inside each training pipeline. This quality view always describes the full source file.',className='muted'),table(pd.DataFrame({'feature':missing.index,'missing':missing.values,'percent':(missing.values/len(raw)*100).round(3)}))])
    height = 1000 if kind=='histograms' else 680 if kind in ['categories','correlation'] else 480
    return style(fig,height),extra,summary,{'height':height,'width':'100%','minWidth':0}

model=bundle['models'][bundle['best']].regressor_
estimator=model.named_steps['model']
names=model.named_steps['preprocessor'].get_feature_names_out()
weights=estimator.feature_importances_ if hasattr(estimator,'feature_importances_') else np.abs(estimator.coef_)
importance=pd.DataFrame({'Feature':[n.split('__')[-1] for n in names],'Importance':weights}).nlargest(18,'Importance').sort_values('Importance')
@app.callback(Output('importance','children'),Input('tabs','value'))
def show_importance(_):
    return graph(style(px.bar(importance,x='Importance',y='Feature',orientation='h'),440))

if __name__ == '__main__':
    import os
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT','8050')),debug=False)



