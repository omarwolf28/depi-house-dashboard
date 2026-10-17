'use strict';
const $=id=>document.getElementById(id);
const money=v=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v);
const count=v=>new Intl.NumberFormat('en-US').format(v);
const config={displaylogo:false,responsive:true,scrollZoom:false};
let metadata,model,sales,chartRequest=0;
const chartNames={distribution:'Price & log-price distributions',areas:'Living area relationships',categories:'Quality, views & rooms',correlation:'Correlation heatmap',histograms:'Numeric feature distributions',geography:'Sales geography',zipcodes:'Top 10 ZIP codes',year:'Build year & sale month',outliers:'Outlier boxplots',quality:'Missing values & data quality'};
const figures=new Map();
function fail(error){const el=$('app-error');el.hidden=false;el.textContent='Could not load the dashboard. Please refresh the page. '+error.message;console.error(error);}
async function fetchJSON(path){const response=await fetch(path);if(!response.ok)throw new Error('Loading '+path+' failed ('+response.status+').');return response.json();}
function addOption(select,value,text){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}
function makeTable(target,rows,columns){
  const table=document.createElement('table'),head=document.createElement('thead'),tr=document.createElement('tr');
  columns.forEach(c=>{const th=document.createElement('th');th.textContent=c.label;tr.append(th);});head.append(tr);table.append(head);
  const body=document.createElement('tbody');
  rows.forEach(row=>{const tr=document.createElement('tr');columns.forEach(c=>{const td=document.createElement('td'),value=row[c.key];td.textContent=value==null?'—':c.format?c.format(value):String(value);tr.append(td);});body.append(tr);});
  table.append(body);$(target).replaceChildren(table);
}
function renderStats(){
  const best=metadata.metrics.find(x=>x.model===metadata.best);
  const cards=[['Homes analyzed',count(metadata.rows),'Cleaned King County sales'],['Median sale price',money(metadata.median),'Historical USD · 2014–2015'],['Test R²',(best.r2*100).toFixed(1)+'%',metadata.best],['Typical absolute error',money(best.mae),'Mean error on held-out sales']];
  cards.forEach((c,i)=>{const box=document.createElement('div');box.className='stat'+(i===3?' yellow-stat':'');['eyebrow','metric','muted'].forEach((cls,j)=>{const span=document.createElement('div');span.className=cls;span.textContent=c[j];box.append(span);});$('stats').append(box);});
}
function renderFields(){
  const container=$('property-fields');
  const zipLabel=document.createElement('label');zipLabel.className='field';const zipText=document.createElement('span');zipText.textContent='ZIP code';const zip=document.createElement('select');zip.id='zipcode';zip.name='zipcode';model.zipcodes.forEach(z=>addOption(zip,z,z));zip.value='98178';zipLabel.append(zipText,zip);container.append(zipLabel);
  const dateLabel=document.createElement('label');dateLabel.className='field';const text=document.createElement('span');text.textContent='Sale date';const date=document.createElement('input');Object.assign(date,{type:'date',name:'date',id:'sale-date',value:'2015-01-15',min:'2014-05-01',max:'2015-05-31',required:true});dateLabel.append(text,date);container.append(dateLabel);
  for(const f of metadata.fields){const label=document.createElement('label');label.className='field';const text=document.createElement('span');text.textContent=f.label;const input=document.createElement('input');Object.assign(input,{id:f.key,name:f.key,type:'number',value:f.value,min:f.min,max:f.max,step:['lat','long'].includes(f.key)?'any':f.step,required:true});label.append(text,input);container.append(label);}
  $('property-form').addEventListener('submit',event=>{event.preventDefault();estimate();});
}
function property(){
  const result={zipcode:$('zipcode').value,date:$('sale-date').value};
  for(const f of metadata.fields){const input=$(f.key),value=Number(input.value);if(!input.value.trim()||!Number.isFinite(value)||value<f.min||value>f.max)throw new Error(f.label+' must be between '+f.min+' and '+f.max+'.');result[f.key]=value;}
  const year=Number(result.date.slice(0,4));
  if(!result.date||result.date<'2014-05-01'||result.date>'2015-05-31')throw new Error('Choose a sale date in the dataset period.');
  if(result.yr_built>year||result.yr_renovated>year)throw new Error('Build and renovation years cannot be after the sale year.');
  if(result.yr_renovated&&result.yr_renovated<result.yr_built)throw new Error('Renovation year must be zero or at least the build year.');
  if(result.sqft_basement>result.sqft_living)throw new Error('Basement area cannot exceed total living area.');
  return result;
}
function distance(lat,lon,row){const rad=Math.PI/180,a=Math.sin((row[5]-lat)*rad/2)**2+Math.cos(lat*rad)*Math.cos(row[5]*rad)*Math.sin((row[6]-lon)*rad/2)**2;return 6371*2*Math.asin(Math.sqrt(Math.min(1,a)));}
function estimate(){
  try{
    const row=property(),price=DepiPredict.predict(row,model);
    if(!Number.isFinite(price)||price<=0)throw new Error('The model could not estimate this home. Please review the inputs.');
    $('prediction').textContent=money(price);$('prediction-detail').replaceChildren();
    for(const value of [money(price/row.sqft_living)+' / sq ft','XGBoost model']){const span=document.createElement('span');span.textContent=value;$('prediction-detail').append(span);}
    $('validation').textContent='';
    const nearby=sales.map(s=>({price:s[0],bedrooms:s[1],bathrooms:s[2],sqft_living:s[3],zipcode:s[4],distance:distance(row.lat,row.long,s)})).sort((a,b)=>a.distance-b.distance).slice(0,5);
    makeTable('comparables',nearby,[{key:'price',label:'Sale price',format:money},{key:'bedrooms',label:'Beds'},{key:'bathrooms',label:'Baths'},{key:'sqft_living',label:'Sq ft',format:count},{key:'zipcode',label:'ZIP'},{key:'distance',label:'km',format:v=>v.toFixed(2)}]);
    drawMap(row).catch(fail);
  }catch(error){$('validation').textContent=error.message;}
}
async function drawMap(row){
  const sample=sales.filter((_,i)=>i%12===0);
  const traces=[{type:'scattermap',lat:sample.map(s=>s[5]),lon:sample.map(s=>s[6]),mode:'markers',marker:{size:6,color:'#4b91ff',opacity:.55},text:sample.map(s=>money(s[0])+' · ZIP '+s[4]),hovertemplate:'%{text}<extra>Historical sale</extra>',name:'Historical sales'},{type:'scattermap',lat:[row.lat],lon:[row.long],mode:'markers',marker:{size:20,color:'#f4d35e'},hovertemplate:'Your property<extra></extra>',name:'Your property'}];
  const layout={height:420,autosize:true,margin:{l:0,r:0,t:0,b:0},paper_bgcolor:'rgba(0,0,0,0)',showlegend:false,map:{style:'carto-darkmatter',center:{lat:row.lat,lon:row.long},zoom:8.7}};
  await Plotly.react('property-map',traces,layout,config);
}
function notebookPlot(){
  const p=metadata.manifest.plots.find(p=>p.id===$('notebook-plot').value);
  $('notebook-image').src=p.src;$('notebook-image').alt=p.title;$('notebook-full').href=p.src;
  $('notebook-insight').textContent=p.insight.replace(/\*\*/g,'');$('notebook-cell').textContent='Original notebook cell '+p.cell+' · complete source dataset';
}
async function chartFigure(kind){if(!figures.has(kind))figures.set(kind,fetchJSON('charts/'+kind+'.json'));return structuredClone(await figures.get(kind));}
async function drawFigure(target,kind){
  const figure=await chartFigure(kind),height=figure.layout.height||350;$(target).style.height=height+'px';
  await Plotly.newPlot(target,figure.data,{...figure.layout,autosize:true},config);
}
async function analysis(){
  const serial=++chartRequest,kind=$('analysis').value,figure=await chartFigure(kind);
  if(serial!==chartRequest)return;
  $('analysis-chart').style.height=(figure.layout.height||480)+'px';
  $('chart-summary').textContent=count(metadata.rows)+' cleaned historical sales · observed sale prices'+(kind==='quality'?' · missing values refer to the full source file':'');
  await Plotly.react('analysis-chart',figure.data,{...figure.layout,autosize:true},config);
}
function renderModels(){
  $('model-scope').textContent='Reproducible 80/20 split · seed 42 · '+count(metadata.train_rows)+' training / '+count(metadata.test_rows)+' test sales. Metrics, predictions, and five-fold validation are exported from the executed notebook. Browser predictions evaluate the same fitted XGBoost trees and preprocessing, verified against all 4,323 notebook test predictions.';
  const score=v=>Number(v).toFixed(4);
  makeTable('model-table',metadata.metrics,[{key:'model',label:'Model'},{key:'train_r2',label:'Train R²',format:score},{key:'r2',label:'Test R²',format:score},{key:'mae',label:'MAE',format:money},{key:'rmse',label:'RMSE',format:money},{key:'best_cv_r2',label:'Tuning CV R²',format:score}]);
  makeTable('cv-table',metadata.cv,[{key:'model',label:'Model'},{key:'cv_r2_mean',label:'Mean CV R²',format:score},{key:'cv_r2_std',label:'CV R² std',format:score},{key:'cv_mae_mean',label:'CV MAE',format:money}]);
}
let modelsDrawn=false;
async function navigate(){
  const name=['estimate','explore','models'].includes(location.hash.slice(1))?location.hash.slice(1):'estimate';
  for(const id of ['estimate','explore','models'])$(id).hidden=id!==name;
  document.querySelectorAll('[data-tab]').forEach(a=>{a.classList.toggle('active',a.dataset.tab===name);if(a.dataset.tab===name)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  if(name==='explore')await analysis();
  if(name==='models'&&!modelsDrawn){await Promise.all([drawFigure('actual-chart','actual'),drawFigure('residuals-chart','residuals'),drawFigure('importance-chart','importance')]);modelsDrawn=true;}
  document.querySelectorAll('.view:not([hidden]) .js-plotly-plot').forEach(el=>Plotly.Plots.resize(el));
}
async function start(){
  [metadata,model,sales]=await Promise.all([fetchJSON('metadata.json'),fetchJSON('model.json'),fetchJSON('sales.json')]);
  renderStats();renderFields();renderModels();
  metadata.manifest.plots.forEach(p=>addOption($('notebook-plot'),p.id,p.title));notebookPlot();
  $('execution').textContent='Run completed: '+new Date(metadata.manifest.executed_at).toLocaleString('en-GB',{timeZone:'Africa/Cairo'})+' Cairo · '+metadata.manifest.notebook;
  Object.entries(chartNames).forEach(([key,label])=>addOption($('analysis'),key,label));
  $('analysis').addEventListener('change',()=>analysis().catch(fail));$('notebook-plot').addEventListener('change',notebookPlot);
  window.addEventListener('hashchange',()=>navigate().catch(fail));
  estimate();await navigate();$('ready').textContent='● XGBoost ready';
}
start().catch(fail);
