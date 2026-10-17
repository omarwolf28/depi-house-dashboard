/* Native evaluation of the notebook's fitted XGBoost trees and preprocessing. */
(function(root){
  function features(row,model){
    // Notebook dates are calendar dates without a time zone. Never shift them
    // through the visitor's local clock (especially month-boundary sales).
    const year=Number(row.date.slice(0,4)),month=Number(row.date.slice(5,7)),age=Math.max(0,year-row.yr_built);
    const x={...row,sale_year:year,sale_month:month,house_age:age,
      is_renovated:row.yr_renovated>0?1:0,
      years_since_renovation:row.yr_renovated>0?Math.max(0,year-row.yr_renovated):age,
      total_rooms:row.bedrooms==null||row.bathrooms==null?null:row.bedrooms+row.bathrooms,
      has_basement:row.sqft_basement>0?1:0,
      living_to_lot_ratio:row.sqft_living/Math.max(1,row.sqft_lot)};
    const out=model.numeric.map((key,i)=>Math.fround(((x[key]==null?model.medians[i]:x[key])-model.centers[i])/model.scales[i]));
    model.zipcodes.forEach(zip=>out.push(String(row.zipcode)===String(zip)?1:0));
    // sklearn's sparse ColumnTransformer omits zeros. XGBoost treats those
    // absent entries as missing, including zero-valued numeric features.
    return out.map(v=>model.sparse&&v===0?NaN:v);
  }
  function predict(row,model){
    const x=features(row,model);
    let total=Math.fround(model.base);
    for(const t of model.trees){
      let node=0;
      while(t.left_children[node]!==-1){
        const value=x[t.split_indices[node]];
        const left=Number.isNaN(value)?Boolean(t.default_left[node]):value<Math.fround(t.split_conditions[node]);
        node=left?t.left_children[node]:t.right_children[node];
      }
      total=Math.fround(total+Math.fround(t.split_conditions[node]));
    }
    return Math.fround(Math.expm1(total));
  }
  const api={features,predict};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.DepiPredict=api;
})(typeof globalThis==='undefined'?this:globalThis);
