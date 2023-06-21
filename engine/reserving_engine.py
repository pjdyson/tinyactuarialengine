
import datetime as dt
import pandas as pd
import numpy as np
import scipy.stats as sps
import chainladder as cl
import datetime as dt
import json




# data imported to be annual-monthly, incremental data
def load_tri_data(filename):
    dtypes = {'origin_year':str,
            'development_month':int,
            'value':float
            }

    df_data = pd.read_csv(filename, dtype=dtypes)    
    # clean up
    df_data = df_data.dropna()

    #build the scaffold
    max_origin = df_data['origin_year'].astype(int).max()
    min_origin = df_data['origin_year'].astype(int).min()

    tri_scaff_origin = pd.DataFrame({'origin_year':range(min_origin,max_origin +1)})
    tri_scaff_dev = pd.DataFrame({'development_month':range(1,(max_origin-min_origin+1)*12+1)})
    tri_scaff = pd.merge(left=tri_scaff_origin, right=tri_scaff_dev, how='cross')
    tri_scaff['origin_year'] = tri_scaff['origin_year'].astype(str)
    #join in the data provided onto the scaffold
    tri_data = tri_scaff.merge(df_data, how='left',left_on=['origin_year', 'development_month'], right_on=['origin_year', 'development_month'])


    # convert development month to date-like 
    tri_data['development_date_year'] = (np.ceil(tri_data['development_month']/12)-1) + tri_data['origin_year'].astype(int)
    tri_data['development_date_month'] = tri_data['development_month'] - (np.ceil(tri_data['development_month']/12)-1)*12
    tri_data['development_date_month_str'] = tri_data['development_date_month'].astype(int).astype(str).str.zfill(2)
    tri_data['development_date_year_str'] = tri_data['development_date_year'].astype(int).astype(str).str.zfill(2)
    tri_data['development_date'] = tri_data['development_date_year_str'] + "-" + tri_data['development_date_month_str']


    return tri_data[['origin_year', 'development_date', 'value']]

def project_triangle(input_json):

    #get datetime of this current run
    date_run_str =  dt.datetime.utcnow().strftime(date_format),

    #process inputs
    inputs = json.loads(input_json)
    analysis_id = inputs['analysis_id']
    date_format = inputs['date_format']
    benchmark_dev_pattern: inputs['benchmark_dev_pattern']
    date_valuation_str = inputs['date_valuation']
    input_triangle_str = inputs['input_triangle']
    
    date_valuation = dt.datetime.strptime(date_valuation_str, date_format)

    input_triangle = pd.read_json(input_triangle_str)

    # load into triangle object
    triangle = cl.Triangle(input_triangle,
                        origin='origin_year',
                        origin_format='%Y',
                        development='development_date',
                        development_format='%Y-%m',
                        columns=['value'],
                        cumulative=False)   

    triangle = triangle[triangle.valuation<=date_valuation]
    triangle_annual = triangle.grain('OYDY').incr_to_cum()

    # Do some projections with the triangle:
    #https://chainladder-python.readthedocs.io/en/latest/methods.html

    dev = cl.Development(
        average='volume',
        n_periods=5, 
        drop_high=True, 
        drop_low=True,
        preserve=3,
        ).fit_transform(triangle_annual)

    # mack reserve prediction
    model_output = cl.MackChainladder().fit(dev)
    
    model_output_summary = model_output.summary_.to_frame(origin_as_datetime=False)

    # calculate reserve margin
    ibnr_total = model_output_summary['IBNR'].sum()
    mean = ibnr_total
    std =np.sqrt( (model_output_summary['Mack Std Err']**2).sum() )
    model_output_summary['CoV'] = model_output_summary['Mack Std Err'] / model_output_summary['IBNR']
    mu = np.log(mean**2/np.sqrt((std**2+mean**2)))
    sigma = np.sqrt(np.log(std**2/mean**2+1))
    ibnr_margin_80 = sps.lognorm.ppf(q=0.8 ,s=sigma, scale=np.exp(mu))

    # build results pack
    result_pack= {}
    result_pack['analysis_id'] = analysis_id
    result_pack['date_run'] = date_run_str
    result_pack['date_valuation'] = date_valuation_str
    result_pack['summary'] = {
        'ibnr': ibnr_total,
        'ibnr_margin_80': ibnr_margin_80,   
        'ibnr_cov': ibnr_margin_80/ibnr_total
    }
    result_pack['summary_table'] = model_output_summary.to_json()
    result_pack['summary_triangle_complete'] = model_output.full_triangle_.grain('OYDY').to_frame(origin_as_datetime=False).to_json()

 

    return json.dumps(result_pack, indent=4)

if __name__ == '__main__':
    
    filename='sample_upload/sample_raa.csv'
    data_tri = load_tri_data(filename)

    date_format = '%Y-%m-%d %H:%M:%S'
    valuation_date_year = data_tri['origin_year'].max()
    valuation_date = dt.datetime.strptime(str(valuation_date_year) + '-12-31' + ' 23:59:59', date_format)
    
    #setup input for api-style interface
    input_dict = {'analysis_id': 'test0001',
                    'date_run': dt.datetime.utcnow().strftime(date_format),
                    'date_valuation': valuation_date.strftime(date_format),
                    'input_triangle': data_tri.to_json(),
                    'date_format': date_format,
                    }
    input_json = json.dumps(input_dict)

    result_json = project_triangle(data_tri, valuation_date, input_json) 
    
    result = json.loads(result_json)
    print(result)
    
  