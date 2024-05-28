# P3: 

A web tool for data process and visualization based on Python language 


### About P3

P3 (Python based data process and visualization platform) is a Python-based online integrated platform for post-processing bioinformatics, which is designed, simulated and developed to address the needs and current situation of users in bioinformatics data processing. It processes bio-information online through open source sharing.

The platform now consists of four components, the first one (PDFC) is the data format conversion tool, through this module, the data can be converted to the standard Python data format and then processed or stored. 

The second one (PSPV) is the data basic statistics result visualization module, in which the uploaded data can be used to perform and visualize the basic statistics of the data, and the commonly used statistical visualization tools can be used in this module. 

The third module (PTDV) is based on the statistics and visualization of time series continuous data, after the user uploads the data, you can get the data expression in different formats and store it, you can get all kinds of statistical graphs of the data and store them, and you can also get the clustering results. 

The fourth module(PVV), based on the first three modules, is dedicated to the generation and realization of volcano diagrams, after the user uploads the data, the required volcano diagrams and the values of each indicator are generated according to the needs and the storage is completed through the download of different formats. 

Details are described in a publication.


### Running the tool

The web tool is available online: https://www.computingmedical.cn/

Currently, the tool can only run on the website with Python. This should launch a web browser with the web tool.

You can also run it in Python running environment by downloading it to use it offline:

-code list in Github platform : https://github.com/zhlan01/P3

-download the source code and install Python.

-install requirements

```bash
pip install -r requirements.txt
```

-run web service

```bash
python index.py
```

### Background info

Some aspects of the tool are explained in publication.

### Manual for operations

Some aspects of the operations can be referred to manual 1.0.0.

### Credits

The PSPV module is inspired by PlotsOfData by Marten Postma and Joachim Goedhart (https://huygens.science.uva.nl/PlotsOfData/ or https://github.com/JoachimGoedhart/PlotsOfData ). 

The PTDV module is inspired by PlotTwist by Joachim Goedhart (https://huygens.science.uva.nl/PlotTwist or https://goedhart.shinyapps.io/PlotTwist/ or https://github.com/JoachimGoedhart/PlotTwist). 

The PVV module is inspired by Joachim Goedhart and Martijn S. Luijsterburg (https://huygens.science.uva.nl/VolcaNoseR or https://goedhart.shinyapps.io/VolcaNoseR/ or https://github.com/JoachimGoedhart/VolcaNoseR).

P3 is created and maintained by Lannhua Zhang, Yanlin Zhou, Xinshuo Yuan, Yujuan Li and Hua Ma.

### Example output

![Output](https://github.com/zhlan01/P3/blob/main/assets/image/VolcaNoseR.png)
