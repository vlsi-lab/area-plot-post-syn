# area-plot-post-syn
This repository contains a python script allowing to plot in `treemap` format and analyze the post-synthesis area report of your RTL design.
By providing an interactive interface through [`plotly`](https://plotly.com) library, the tool enables hierarchical designs exploration.
Furthermore, it represents a simple way to visualize complex designs, observing the relative dimensions of the different components and their impact on the overall design.

![Example screenshot]([https://github.com/vlsi-lab/area-plot-post-syn/tree/main/images](https://github.com/vlsi-lab/area-plot-post-syn/blob/main/images/example_image.png)

## Requirements

All packages to run the tool are grouped in `environment.yml` file.

Using [`conda`](https://docs.anaconda.com/) you can create a new environment starting from the `.yml` file as:

```bash
 conda env create -f environment.yml
```

## Plot a design layout

To plot the layout of a design, the only requirement is a post-synthesis area report.
Launch the area generation thorugh the command:
```bash
python3 scripts/area_plot.py --filename report_file.rpt --rename True
```
Further options are available to tweak the interactive plot, such as plotting only modules whose area contribution is higher than a certain percentage or setting the maximum hierarchical level up to which visualize the block scheme.


For all available options try:
```bash
python3 scripts/area_plot.py --help
```
The tool also supports interactive `sunburst` visualization using [plotly](https://plotly.com/python/sunburst-charts/)

The tool has only been tested using Synopsys DC® output files

