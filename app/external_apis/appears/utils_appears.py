# app/external_apis/appears/utils_appears.py
BAND_NAME_MAP = {
    'b01': 'b01_coastal_aerosol',
    'b02': 'b02_blue',
    'b03': 'b03_green',
    'b04': 'b04_red',
    'b05': 'b05_nir',
    'b06': 'b06_swir1',
    'b07': 'b07_swir2',
    'b08': 'b08_nir_broad',
    'b8a': 'b8a_nir_narrow',
    'b09': 'b09_water_vapor',
    'b10': 'b10_cirrus',
    'b11': 'b11_swir1',
    'b12': 'b12_swir2',
    'fmask': 'fmask_quality_bits',
    'saa': 'saa_sun_azimuth',
    'sza': 'sza_sun_zenith',
    'vaa': 'vaa_view_azimuth',
    'vza': 'vza_view_zenith'
}