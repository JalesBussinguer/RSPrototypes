"""

Este é um script em Python para a execução automatizada de processamentos básicos em imagens de radar da constelação Sentinel-1 (ESA).

Autor: Jales de Freitas Bussinguer

site: https://jalesbussinguer.wixsite.com/portfolio

"""

# Importações

# Bibliotecas básicas

import numpy as np
import matplotlib.pyplot as plt

# Módulos da biblioteca snappy

from snappy import ProductIO
from snappy import HashMap
from snappy import GPF
from snappy import jpy

# ------------------------------------------------------------------------------------

"""

Funções para executar os operadores do SNAP

"""

# Ortorretificação (Orthorectification) - Apply Orbit File
# Função que faz a correção do posicionamento de órbita da imagem

def ApplyOrbitFile(data):
    """[summary]

    Args:
        data ([type]): [description]

    Returns:
        [type]: [description]
    """
    print('Aplying Orbit File...')

    parameters = HashMap()

    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('polyDegree', '3')
    parameters.put('continueOnFail', 'false')

    return GPF.createProduct('Apply-Orbit-File', parameters, data)

# Recorte - Subset
# Função que faz o recorte de uma imagem

def Subset(data, x, y, w, h):

    print('Subsetting the image...')

    HashMap = jpy.get_type('java.util.HashMap')
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    parameters = HashMap()
    parameters.put('copyMetadata', True)
    parameters.put('region', "%s,%s,%s,%s" % (x, y, w, h))

    return GPF.createProduct('Subset', parameters, data)

# Informações - Information
# Função que retorna informações básicas da imagem como o número de pixels em X e Y, o nome da imagem e das bandas

def ProductInformation(data):

    print('Getting product informations...')

    # Getting the width of the scene
    width = data.getSceneRasterWidth()
    print('Width: {} px'.format(width))

    # Getting the height of the scene
    height = data.getSceneRasterHeight()
    print('Height: {} px'.format(height))

    # Getting the dataset name
    name = data.getName()
    print('Name: {}'.format(name))

    # Getting the band names in the imagery
    band_names = data.getBandNames()
    print('Band names: {}'.format(', '.join(band_names)))

    return width, height, name, band_names

# Calibração Radiométrica - Radiometric Calibration
# Função que aplica uma correção radiométrica na imagem, transformando os números digitais dos pixels em valroes com significado físico

def Calibration(data, band, pol):

    print('Calibrating...')
    
    parameters = HashMap()

    parameters.put('outputSigmaBand', True) 
    parameters.put('sourceBands', band)
    parameters.put('selectedPolarisations', pol)
    parameters.put('outputImageScaleInDb', False)

    return GPF.createProduct('Calibration', parameters, data)

# Filtragem Speckle - Speckle Filtering
# Função que aplica um filtro para a redução de speckle na imagem

def SpeckleFilter(data, source_band, filter, filterSizeX, filterSizeY):

    print('Aplying the Speckle Filter...')

    parameters = HashMap()

    parameters.put('sourceBands', source_band)
    parameters.put('filter', filter)
    parameters.put('filterSizeX', '%s' % (filterSizeX))
    parameters.put('filterSizeY', '%s' % (filterSizeY))
    parameters.put('dampingFactor', '2')
    parameters.put('estimateENL', 'true')
    parameters.put('enl', '1.0')
    parameters.put('numLooksStr', '1')
    parameters.put('targetWindowSizeStr', '3x3')
    parameters.put('sigmaStr', '0.9')
    parameters.put('anSize', '50')

    return GPF.createProduct('Speckle-Filter', parameters, data)

# Correção Geométrica (Range Doppler Terrain Correction)
# Função que ...

def Terrain_Correction(data, source_band):

    print('Aplying the Range Doppler Terrain Correction...')

    parameters = HashMap()

    parameters.put('demName', 'SRTM 3Sec')
    parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('pixelSpacingInMeter', 10.0)
    parameters.put('sourceBands', source_band)

    return GPF.createProduct('Terrain-Correction', parameters, data)

# Conversão para decibel (LinearToFromdB)
# Convertendo os números digitais para valores em decibel

def Convert_to_dB(data, source_band):
    
    print('Converting to dB...')

    parameters = HashMap()

    parameters.put('sourceBands', source_band)

    return GPF.createProduct('LinearToFromdB', parameters, data)

# Função que lista os parâmetros de cada operador do SNAP

def listParams(operator_name):

    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    
    op_spi = GPF.getDefaultInstance().getOperatorSpiRegistry().getOperatorSpi(operator_name)

    print('Operator name:', op_spi.getOperatorDescriptor().getName())
    print('Operator alias:', op_spi.getOperatorDescriptor().getAlias())

    param_desc = op_spi.getOperatorDescriptor().getParameterDescriptors()

    for param in param_desc:
        print(param.getName(), 'or', param.getAlias())

# --------------------------------------------------------------------------------------------------------------

# Plotagem - Plotting

# Função que plota a imagem em um gráfico
def plotBand(data, banda, vmin, vmax):

    print('Plotting the image...')
    
    w = data.getSceneRasterWidth()
    h = data.getSceneRasterHeight()
    band = data.getBand(banda)
    print(w, h)

    band_data = np.zeros(w * h, np.float32)
    band.readPixels(0, 0, w, h, band_data)

    band_data.shape = h, w

    width = 12
    height = 12

    plt.figure(figsize=(width, height))
    imgplot = plt.imshow(band_data, cmap='binary', vmin=vmin, vmax=vmax)

    return imgplot

# Função que plota o histograma da imagem
def plotHistogram(data, banda):

    print('Plotting the histogram...')
    
    band = data.getBand(banda)
    
    w = band.getRasterWidth()
    h = band.getRasterHeight()
    
    band_data = np.zeros(w * h, np.float32)
    band.readPixels(0, 0, w, h, band_data)
    band_data.shape = h * w

    histplot = plt.hist(np.asarray(band_data, dtype='float'), bins=2048, range=[-33, -1])

    return histplot

# ------------------------------------------------------------------------------------------------------

# Binarização da imagem

def find_threshold(counts, bins):
    
    x = dict(zip(counts, bins))

    dict_peak_water = {k:v for (k,v) in x.items() if -40 < v < -17}
    peak_water = max(dict_peak_water.keys())
    
    peak_land = max(x.keys())

    dict_reducted = {k:v for (k,v) in x.items() if x[peak_land] > v > x[peak_water]}

    key_threshold = min(dict_reducted.keys())

    return x[key_threshold]

# ------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # GPF Initialization
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    # Product initialization
    s1_path = 'C:/Users/jales/Desktop/S1/S1A_processado/Sigma0_VH_db.hdr'

    # Reading the data
    product = ProductIO.readProduct(s1_path)

    # ------------------------------------------------------------------------------------------------------

    #ProductInformation(product)

    #S1_Orb = ApplyOrbitFile(product)

    #S1_Orb_Subset = Subset(S1_Orb, 0, 9928, 25580, 16846)

    #ProductInformation(S1_Orb_Subset)

    #S1_Orb_Subset_Cal = Calibration(S1_Orb_Subset, 'Intensity_VH', 'VH')

    #S1_Orb_Subset_Cal_Ter = Terrain_Correction(S1_Orb_Subset_Cal, 'Sigma0_VH')

    #S1_Orb_Subset_Cal_Ter_Spec = SpeckleFilter(S1_Orb_Subset_Cal_Ter, 'Sigma0_VH', 'Lee', 3, 3)

    #S1_Orb_Subset_Cal_Ter_Spec_dB = Convert_to_dB(S1_Orb_Subset_Cal_Ter_Spec, 'Sigma0_VH')

    #print('Writing...')
    #ProductIO.writeProduct(S1_Orb_Subset_Cal_Ter_Spec_dB, 'C:/Users/jales/Desktop/S1/S1A_processado', 'ENVI')

    #print('Processamento finalizado')
    # ------------------------------------------------------------------------------------------------------

    #plotBand(S1_Orb_Subset, 'Intensity_VH')
    print('Calculating the histogram...')
    plotHistogram(product, 'Sigma0_VH_db')
    
    print('Thresholding...')
    find_threshold(histplot[0], histplot[1])
    # ------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------