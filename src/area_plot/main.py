#Copyright 2024 Politecnico di Torino.
#
#File: area_plot.py
#Author: Flavia Guella
#Date: 06/11/2024
#Description: Treemap and sunburst plot starting from area report


import plotly.graph_objects as go
import argparse
import pandas as pd
from . import utils_area as utils
import os


def get_args():
  # Create an argument parser object
  parser = argparse.ArgumentParser()
  # Add mutually arguments
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--filename', '-f', type = str, help = 'Name of the report file to parse', default = './area.rpt')
  group.add_argument('--load-from-csv', type = str, help = 'Load the hierarchy from the specified csv file')
  # Add arguments
  parser.add_argument('--out-dir', '-o', type = str, help = 'Output directory where to store the generated plots.', default = '.')
  parser.add_argument('--skip_rename', action='store_true', help = 'Skip looking for duplicates in the hierarchy. This may break the plot if duplicates are present, but it is faster.')
  parser.add_argument('--top-module', '-t', type = str, help = 'Name of the top module to plot')
  parser.add_argument('--max-levels-hier', '-d', type = int, help = 'Maximum number of levels to consider in the hierarchy', default = 4)
  parser.add_argument('--threshold', type = float, help = 'Minimum area percentage with respect to the parent to plot a component', default = 0)
  parser.add_argument('--plot-mode', choices=['total','remainder'], default = 'total')
  parser.add_argument('--plot-type', type = str, help = 'Type of plot to generate, for now support only treemap and sunburst', default = 'treemap')
  parser.add_argument('--show', action='store_true', help = 'Show the plot')
  parser.add_argument('--colormap', type = str, nargs="+",  help = 'Colormap to use for the plot', default = ['#d58936', '#39393a','#90C290','#6d1a36','#39393a','#007480'])
  return parser.parse_args()

def treemap_plot(df_tree, top_module, max_levels_hier, plot_mode, colormap, show = False, out_dir = "."):
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

  if show:
    fig.show()
  # save figure
  base_path = os.path.join(out_dir, str(top_module) + "_treemap")
  fig.write_image(str(base_path) + ".png", engine="kaleido")
  fig.write_image(str(base_path) + ".svg", engine="kaleido")
  fig.write_html(str(base_path) + ".html")


def sunburst_plot(df_tree, top_module, max_levels_hier, plot_mode, colormap, show = False, out_dir = "."):
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
  if show:
    fig.show()
  # save figure
  base_path = os.path.join(out_dir, str(top_module) + "_sunburst")
  fig.write_image(base_path + ".png", engine="kaleido")
  fig.write_image(base_path + ".svg", engine="kaleido")
  fig.write_html(base_path + ".html")

def main():
  args = get_args()
  filename = args.filename

  # define colormap as a list of hex colors
  colormap = args.colormap
  if (args.load_from_csv != None):
    df_tree = pd.read_csv(args.load_from_csv)
  else:
    df_tree = utils.get_df_from_report(filename)
  
  # Remove rows with value 0
  #df_tree = df_tree[df_tree['value'] != 0]

  # Infer top module
  if (args.top_module == None):
    top_module = df_tree['id'].iloc[0]
  else:
    top_module = args.top_module
  
  print("Selected top-level module: ", top_module)

  # Create the output directory
  if not os.path.exists(args.out_dir):
    os.makedirs(args.out_dir)
  
  # Find duplicate and rename them and all their children 'parent' field
  # Note: renaming is required not to break the plotly plot
  if not args.skip_rename:
    df_tree = utils.rename_duplicates(df_tree, top_module)
    # save not to call it every time
  
  csv_path = os.path.join(args.out_dir, str(top_module) + ".csv")
  df_tree.to_csv(csv_path, index=False)
  
  # Ensure the values are numeric
  df_tree['value'] = pd.to_numeric(df_tree['value'], errors='coerce')

  # Merge entries lower than the threshold into a single entry called 'others'
  if (args.threshold != None and args.threshold > 0 and args.threshold < 1):
    df_tree = utils.plot_threshold(df_tree, top_module, args.threshold)

  # Remove wrappers
  df_tree = utils.remove_wrappers(df_tree)
  # Not required, total mode works for < area of children than parent
  #df_tree = utils.make_dataset_complete(df_tree)

  # Plot the treemap
  if (args.plot_type == 'treemap'):
    treemap_plot(df_tree, top_module, args.max_levels_hier, args.plot_mode, colormap, args.show, args.out_dir)
  elif (args.plot_type == 'sunburst'):
    sunburst_plot(df_tree, top_module, args.max_levels_hier, args.plot_mode, colormap, args.show, args.out_dir)
  
if __name__ == '__main__':
  main()

