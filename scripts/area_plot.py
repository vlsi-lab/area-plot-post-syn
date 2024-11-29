#Copyright 2024 Politecnico di Torino.
#
#File: area_plot.py
#Author: Flavia Guella
#Date: 06/11/2024
#Description: Treemap and sunburst plot starting from area report


import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sb
import argparse
import pandas as pd
import utils.utils_area as utils


def get_args():
  # Create an argument parser object
  parser = argparse.ArgumentParser()
  # Add arguments
  parser.add_argument('--filename', type = str, help = 'Name of the report file to parse', default = './area.rpt')
  parser.add_argument('--rename', type = bool, help = 'Rename the duplicates in the hierarchy for prettier appearance', default = False)
  parser.add_argument('--top-module', type = str, help = 'Name of the top module to plot', default = 'nmc_cisc_top')
  parser.add_argument('--max-levels-hier', type = int, help = 'Maximum number of levels to consider in the hierarchy', default = 4)
  parser.add_argument('--threshold', type = float, help = 'Minimum area percentage with respect to the parent to plot a component', default = 0.001)
  parser.add_argument('--load-from-csv', type = bool, help = 'Load the hierarchy from a csv file', default = False)
  parser.add_argument('--csv-file', type = str, help = 'Name of the csv file to load the hierarchy from or where to save the data', default = 'temp_rn.csv')
  parser.add_argument('--plot-mode', choices=['total','remainder'], default = 'total')
  parser.add_argument('--plot-type', type = str, help = 'Type of plot to generate, for now support only treemap and sunburst', default = 'treemap')
  return parser.parse_args()

def treemap_plot(df_tree, top_module, max_levels_hier, plot_mode, colormap):
  # adjust colormap
  df_tree = utils.assign_colors(df_tree, top_module, colormap)
  
  fig = go.Figure()
  fig.add_trace(go.Treemap(
      ids = df_tree['id'],
      labels = df_tree['label'],
      values=df_tree['value'],
      parents = df_tree['parent'],
      root_color="lightgrey",
      maxdepth=max_levels_hier,
      level= top_module, # should be equal to the id or else the label of the starting component
      marker_colors = df_tree['color'],
      textinfo = 'label+percent parent',
      branchvalues = plot_mode,
      #sort=True
  ))
  fig.update_layout(
    uniformtext=dict(minsize=10, mode='hide'),
    font=dict(size=14),
    width=1700,
    height=1000,
  )
  # Update the treemap trace text font colors
  fig.update_traces(
    insidetextfont=dict(color='white'),
    outsidetextfont=dict(color='white'),
    selector=dict(type='treemap')
  )

  fig.show()
  # save figure
  fig.write_image(str(top_module) + "_treemap" +".png", engine="kaleido")
  fig.write_image(str(top_module) + "_treemap" +".pdf", engine="kaleido")
  fig.write_image(str(top_module) + "_treemap" +".svg", engine="kaleido")


def sunburst_plot(df_tree, top_module, max_levels_hier, plot_mode, colormap):
  # adjust colormap
  df_tree = utils.assign_colors(df_tree, top_module, colormap)
  
  fig = go.Figure()
  fig.add_trace(go.Sunburst(
      ids = df_tree['id'],
      labels = df_tree['label'],
      values=df_tree['value'],
      parents = df_tree['parent'],
      root_color="lightgrey",
      textfont_size=20,
      textinfo='label+percent parent',
      maxdepth=max_levels_hier,
      level= top_module, # should be equal to the id or else the label of the starting component
      marker_colors = df_tree['color'],
      branchvalues = plot_mode,
      #sort=True
  ))
  fig.update_layout(
    uniformtext=dict(minsize=7, mode='hide'),
    margin = dict(t=50, l=25, r=25, b=25),  
    width=500,
    height=500,
  )
  fig.show()
  # save figure
  fig.write_image(str(top_module) + "_sunburst.png", engine="kaleido")
  fig.write_image(str(top_module) + "_sunburst.pdf", engine="kaleido")
  fig.write_image(str(top_module) + "_sunburst.svg", engine="kaleido")


def main():
  args = get_args()
  filename = args.filename
  top_module = args.top_module

  # define colormap as a list of hex colors
  if 'l1' in top_module:
    colormap = ['#6F1A07', '#E07A5F', '#005F73', '#81B29A', '#F2CC8F']

  else:
    colormap = ['#d58936', '#39393a','#6d1a36','#39393a','#007480','#39393a','#39393a', '#39393a','#39393a','#6d1a36','#007480', '#d58936' ]

  if (args.load_from_csv):
    df_tree = pd.read_csv(args.csv_file)
  else:
    df_tree = utils.get_df_from_report(filename)
  
  # Remove rows with value 0
  #df_tree = df_tree[df_tree['value'] != 0]
  
  # Find duplicate and rename them and all their children 'parent' field
  if (args.rename):
    df_tree = utils.rename_duplicates(df_tree)
    # save not to call it every time
    df_tree.to_csv(args.csv_file, index=False)
  
  # Ensure the values are numeric
  df_tree['value'] = pd.to_numeric(df_tree['value'], errors='coerce')

  # Remove wrappers
  df_tree = utils.remove_wrappers(df_tree)
  # Not required, total mode works for < area of children than parent
  #df_tree = utils.make_dataset_complete(df_tree)
  '''
  df_tree = utils.plot_threshold(df_tree, args.threshold)
  if (args.top_module == 'u_nmc_cisc'):
    df_tree = utils.remove_module(df_tree, 'u_nmc_cisc_peripherals')
  elif args.top_module == 'heep_top':
    area_ctl = 107418.3202+14917.3202+12008.52-11585.8802
    df_tree = utils.add_module(df_tree, 'cache_ctl', 'memory_subsystem_i', area_ctl)
  '''
  # Plot the treemap
  if (args.plot_type == 'treemap'):
    treemap_plot(df_tree, top_module, args.max_levels_hier, args.threshold, args.plot_mode, colormap)
  elif (args.plot_type == 'sunburst'):
    sunburst_plot(df_tree, top_module, args.max_levels_hier, args.threshold, args.plot_mode, colormap)
  
if __name__ == '__main__':
  main()

