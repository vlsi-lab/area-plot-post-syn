import regex as re
import pandas as pd
import colorsys


def prettify_name(name):
    '''
    Return a pretty name for a component instance.
    @param name: str. Name of the component instance
    @return: str. Pretty name for the component instance
    '''
    pretty_name = re.sub(r'(_[iI])$', '', name)
    pretty_name = re.sub(r'gen_[a-zA-Z0-9_]*__', '', pretty_name)
    # Remove the 'u_' prefix and replace underscores with spaces
    pretty_name = pretty_name.replace('u_', '', 1).replace('_', ' ')
    # Capitalize the first letter of each word
    pretty_name = pretty_name.title()
    # Handle _i, _I or _inst at the end or beginning of components removing them
    return pretty_name

def recursive_remove(df, parent_id):
  '''
  Remove all children of a parent
  @param df: pd.DataFrame. DataFrame with the area of the components instance
  @param parent_id: str. Parent id to remove
  '''
  df = df.copy()
  children = df[df['parent'] == parent_id]
  for child_id in children['id']:
    df = df[df['id'] != child_id]
    df = recursive_remove(df, child_id)
  return df

def remove_wrappers(df):
  '''
  Remove all components containing "wrapper" in their name
  @param df: pd.DataFrame. DataFrame with the area of the components instance
  @return: pd.DataFrame. DataFrame with the area of the components instance without the wrappers
  '''  
  # Find all components containing "wrapper" in their name
  wrappers = df[df['id'].str.contains('wrapper', case=False)]
  # For all child of the wrapper id, rename parent to the same parent of the wrapper
  children = df[df['parent'].isin(wrappers['id'])]
  
  for index, row in children.iterrows():
    df.loc[index, 'parent'] = df.loc[df['id'] == row['parent'], 'parent'].values[0] 
  # Remove the wrappers
  df = df[~df['id'].str.contains('wrapper', case=False)]
  return df

def remove_module(df, module_name):
  module = df[df['id'].str.contains(module_name, case=False)]
  # For all child of the wrapper id, rename parent to the same parent of the wrapper
  children = df[df['parent'].isin(module['id'])]
  
  for index, row in children.iterrows():
    df.loc[index, 'parent'] = df.loc[df['id'] == row['parent'], 'parent'].values[0] 
  # Remove the wrappers
  df = df[~df['id'].str.contains(module_name, case=False)]
  return df

def add_module(df, module_name, parent_name, attr):
  '''
  Add a module to the dataframe
  @param df: pd.DataFrame. DataFrame with the area of the components instance
  @param module_name: str. Name of the module to add
  @param parent_name: str. Name of the parent module
  @param attr: float. Area of the module to add
  '''
  # Ensure no changes to the original DataFrame
  df = df.copy()
  # Find parent ID
  parent_row = df[df['id'].str.contains(parent_name, case=False)]
  if parent_row.empty:
      raise ValueError(f"Parent module '{parent_name}' not found.")
  parent_id = parent_row.iloc[0]['id']
  # Append the new module
  new_row = {'id': module_name, 'parent': parent_id, 'label': module_name, 'value': attr,  'color': 'blue'}
  df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
  # Update parent values
  parent = parent_id
  while parent:
      parent_row = df[df['id'] == parent]
      if parent_row.empty:
          break
      df.loc[df['id'] == parent, 'value'] += attr
      parent = parent_row['parent'].values[0] if not parent_row.empty else ''
  return df


def recursive_add(df, df_sub, parent_id):
  '''
  Add all children of a parent to df_sub dataframe
  @param df: pd.DataFrame. DataFrame with the area of the components instance
  @param parent_id: str. Parent id whose children to add
  @param df_sub: pd.DataFrame. DataFrame to add the children to
  '''
  df = df.copy()
  children = df[df['parent'] == parent_id]
  for _, child in children.iterrows():
    # add child to the dataframe
    df_sub = df_sub._append(child)
    df_sub = recursive_add(df, df_sub, child['id'])
  return df_sub

def plot_threshold(df, top_module, threshold):
  '''
  Remove all children with area < threshold * parent area
  @param df: pd.DataFrame. DataFrame with the area of the components instance
  @param threshold: float. Threshold to remove children
  '''
  df = df.copy()
  
  # Look at the hierarchy starting from the top_module
  df_sub = pd.DataFrame(columns=['id', 'parent', 'label', 'value', 'color'])
  df_sub = df_sub._append(df.loc[df['id'] == top_module], ignore_index=True)
  df_sub.loc[df_sub['id'] == top_module, 'parent'] = ''
  df_sub = recursive_add(df, df_sub, top_module)
  # Iterate over all parents
  for parent_id in df_sub['parent'].unique():
      other_value = 0.0
      if pd.isna(parent_id) or parent_id == '':
          continue
      children = df_sub[df_sub['parent'] == parent_id]
      for child_id in children['id']:
        # find child value
        child_attr = df_sub.loc[df_sub['id'] == child_id, 'value'].values[0]
        parent_attr = df_sub.loc[df_sub['id'] == parent_id, 'value'].values[0]
        # Remove child if child_attr < threshold * parent_attr
        if child_attr < threshold * parent_attr:
          other_value += child_attr
          df_sub = df_sub[df_sub['id'] != child_id]
          df_sub = recursive_remove(df_sub, child_id)

      # Add the 'others' component
      if other_value > 0:
          df_sub = df_sub._append({'id': parent_id + '_others', 'parent': parent_id, 'label': 'others', 'value': other_value, 'color': 'blue'}, ignore_index=True)

          
  return df_sub


def lighten_color(hex_color, amount=0.5):
    '''
    Lighten the color by the specified amount
    @param hex_color: str. Hexadecimal color code
    @param amount: float. Amount to lighten the color by (default 0.5)
    '''
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    
    # Convert RGB to HLS (Hue, Lightness, Saturation)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    
    # Increase the lightness by the specified amount, keeping it within the range [0, 1]
    l = min(1, l + amount * (1 - l))
    
    # Convert back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

def make_color_transparent(hex_color, amount=0.5):
    '''
    Make the color more transparent by reducing the alpha value.
    
    @param hex_color: str. Hexadecimal color code with or without alpha (e.g., "#RRGGBB" or "#RRGGBBAA").
    @param amount: float. Fraction to reduce the alpha by (default 0.5, range 0-1).
    @return: str. Hexadecimal color code with updated alpha.
    '''
    import colorsys

    # Ensure the color starts with a '#'
    hex_color = hex_color.lstrip('#')
    
    # Parse RGB(A) values
    if len(hex_color) == 6:  # If no alpha is provided, assume fully opaque
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        a = 255  # Default alpha is fully opaque
    elif len(hex_color) == 8:  # If alpha is provided
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16)
    else:
        raise ValueError("Invalid hex color format. Use '#RRGGBB' or '#RRGGBBAA'.")
    
    # Decrease alpha by the specified amount
    a = max(0, int(a * (1 - amount)))  # Clamp alpha to range [0, 255]

    # Return as hex string with alpha included
    return f'#{r:02x}{g:02x}{b:02x}{a:02x}'


def assign_colors(df, top_module, root_colors):  
    '''
    Starting from a df with columns: id, parent, label, value, color 
    assign a color to each component based on the parent-child relationship
    Assign a color of the root colors to all the children of the top_module, then each
    subchild will have a color that is a lighter version of the parent color, based
    on the hierarchical level
    @param df: pd.DataFrame. DataFrame with the area of the components instance
    @param root_colors: list of str. List of colors to assign to the first generation children
    @return: pd.DataFrame. DataFrame with the area of the components instance and the assigned colors
    '''
    df = df.copy()
    
    # Set the root node color
    df.loc[df['id'] == top_module, 'color'] = root_colors[0]
    # print line where id == top_module
    #print(df.loc[df['id'] == top_module])
    # Recursive color assignment based on parent-child relationships
    c_idx = 1
    eps = 1e-4
    for parent_id in df['parent'].unique():
        if pd.isna(parent_id) or parent_id == '':
            continue
        elif parent_id == top_module:
          # assign color in the list
          # assign one color to each child
          children = df[df['parent'] == parent_id]
          for child_id in children['id']:
            df.loc[df['id'] == child_id, 'color'] = root_colors[c_idx]
            c_idx = (c_idx + 1) % len(root_colors)
        else:
          parent_color = df.loc[df['id'] == parent_id, 'color'].values[0]
          # Find all children of the current parent
          children = df[df['parent'] == parent_id]

          # Assign color to each child based on its importance relative to the parent
          for child_id in children['id']:
            # TODO: improve, this serves when top_module != from top
            try:
              child_color = make_color_transparent(parent_color, amount=0.3)  # Scale lightening by ratio
            except ValueError:
              continue
            df.loc[df['id'] == child_id, 'color'] = child_color

    return df


def compute_area_percentage(df):
  '''
  Add a column with the percentage of the area of each component with respect to the parent area
  @param df: pd.DataFrame. DataFrame with the area of the components instance
  @return: pd.DataFrame. DataFrame with the area of the components instance and the percentage of the area
  '''
  df = df.copy()
  for parent_id in df['parent'].unique():
    if pd.isna(parent_id) or parent_id == '':
      continue
    parent_value = df.loc[df['id'] == parent_id, 'value'].values[0]
    children = df[df['parent'] == parent_id]
    for child_id in children['id']:
      child_value = df.loc[df['id'] == child_id, 'value'].values[0]
      if parent_value == 0:
        df.loc[df['id'] == child_id, 'percent'] = 0
      else:
        df.loc[df['id'] == child_id, 'percent'] = 100 * child_value / parent_value
  return df


def add_component_to_dict(component_dict, parent_name, component_name, attr, threshold, curr_level_hier=0, max_levels_hier=2):
  '''
  Add a component to a dictionary with the following structure:
  {
    'component_name': {
      'attr': float,
      'sub_component_name': {
        'attr': float,
        'sub_sub_component_name': {
          'attr': float
        }
      }
    }
  }
  @param component_dict: dict. Dictionary to add the component to
  @param parent_name: str. Name of the parent component
  @param component_name: str. Name of the component to add
  @param attr: float. attr of the component to add
  @param threshold: float. Minimum attr percentage to consider a component
  @param curr_level_hier: int. Current level of the hierarchy
  @param max_levels_hier: int. Maximum number of levels to consider in the hierarchy
  @return: True if the component is added, False otherwise
  '''
  if curr_level_hier > max_levels_hier:
    return False
  # TODO: add supporto for other components occupying additional area
  #print(component_dict)
  for k, v in component_dict.items():
    #print(k)
    if k == parent_name:
      #print('HERE', curr_level_hier)
      if curr_level_hier <= max_levels_hier:
        if attr > threshold * v['attr']:
          component_dict[k][component_name] = {'attr': attr}
        return True
      else:
        return False

    elif isinstance(v, dict):
      found = add_component_to_dict(component_dict[k], parent_name, component_name, attr, threshold, curr_level_hier+1, max_levels_hier)
    
  return False

def dict2df(component_dict, hier_levels, parent_inst=None, df_tree=None):
  '''
  Convert a dictionary with the following structure:
  {
    'component_name': {
      'attr': float,
      'sub_component_name': {
        'attr': float,
        'sub_sub_component_name': {
          'attr': float
        }
      }
    }
  }
  to a pandas DataFrame
  @param component_dict: dict. Dictionary to convert
  @param hier_levels: int. Number of hierarchy levels to consider
  @param parent_inst: str. Name of the parent instance
  @param first_iter: bool. True if it is the first iteration
  @return: pd.DataFrame
  '''
  # DataFrame to store the tree
  if df_tree is None:
    df_tree = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
  if hier_levels == 0:
    return df_tree
  for k, v in component_dict.items():
    # traverse the tree and recursively add id, parent, value, color
    if parent_inst is not None:
      if k == parent_inst:
        df_tree = df_tree._append({'id': k, 'parent': '', 'value': v['attr'], 'color': 'blue'}, ignore_index=True)
        if isinstance(v, dict):
          #df_tree = df_tree._append({'id': k, 'parent': '', 'value': v['attr'], 'color': 'blue'}, ignore_index=True)
          df_tree = dict2df(v, hier_levels-1, k, df_tree)
      else:
        if isinstance(v, dict):
          df_tree = df_tree._append({'id': k, 'parent': parent_inst, 'value': v['attr'], 'color': 'blue'}, ignore_index=True)
          df_tree = dict2df(v, hier_levels, k, df_tree)

  return df_tree

def make_dataset_complete(df_tree):
  # df_tree is a dataframe with columns: id, parent, value, color
  # For each line of the dataframe find all lines with parent = id
  for index, row in df_tree.iterrows():
    curr_parent = row['id']
    parent_area = row['value']
    cum_area = 0
    # Find all lines with parent = curr_parent
    for index2, row2 in df_tree.iterrows():
      if row2['parent'] == curr_parent:
        # Accumulate the area of all children
        cum_area += row2['value']
    # Insert the line right after the parent
    if cum_area > 0:
      df_tree.loc[index+1] = [curr_parent +'_cum', curr_parent, curr_parent +'_cum', (parent_area-cum_area), 'blue']
  return df_tree


def get_area_from_component_name(component_name, filename):
  '''
  Parse the report file to get the area of the component instance.
  This function does not account for any hierarchy in the design.
  @param component_name: str or list of string. Reduced name of the component instance
  @param filename: str. Name of the report to parse
  @return: List of float. Area of the components instance
  '''
  
  file = open(filename, 'r')
  lines = file.readlines()
  file.close()
  
  if type(component_name) == str:
    component_name = [component_name]
  
  area = []
  for name in component_name:
    str_match = r'\w*' + name + r'\s+(\d+\.+\d+)'
    for line in lines:
      
      match = re.search(str_match, line)
      if match:
        area.append(float(match.group(1)))
        break
    else:
      raise ValueError(f'No area found for {name} in {filename}')

  return area
  

def rename_duplicates(df, top_module):
    # Step 1: Find duplicates in the 'id' column
    duplicates = df[df.duplicated(subset=['id'], keep=False)]

    # Step 2: Iterate over duplicates and rename them uniquely
    for idx, (id_val, parent, label, value, color) in enumerate(duplicates.values):
        # Exit if the duplicate is the top module
        if id_val == top_module:
          raise NameError(f"Cannot choose among multiple instances of the top module '{id_val}'.")
        
        # Find all rows with this duplicate ID
        matching_rows = df[df['id'] == id_val].index
        # Find all children of a given id, they can go from the current idx to the next matching_rows element
        for i, row_idx in enumerate(matching_rows):
          try:
            next_row_idx = matching_rows[i+1]
          except IndexError:
            next_row_idx = len(df)
          for j in range(row_idx+1, next_row_idx):
            if df.loc[j, 'parent'] == id_val:
              #print(f"Found child {df.loc[j, 'id']} of {id_val}")
              # substitute the parent with the new name
              df.loc[j, 'parent'] = f"{id_val}_{i+1}"
        # Rename all duplicate occurrences uniquely (e.g., append '_1', '_2', etc.)
        for i, row_idx in enumerate(matching_rows):
            new_id = f"{id_val}_{i+1}"
            df.loc[row_idx, 'id'] = new_id
        
    return df

def get_df_from_report(filename:str):
  '''
  Parse the report file to get the area of the component instance.

  @param filename: str. Name of the report to parse
  @return: pd.DataFrame. DataFrame with the area of the components instance
  The DataFrame has the following columns:
  - id: str. Name of the component instance
  - parent: str. Name of the parent component instance
  - label: str. Pretty name of the component instance (TO BE DEFINED IN A PRETTY WAY)
  - value: float. Area of the component instance
  - color: str. Color of the component instance (TO BE DEFINED IN A PRETTY WAY)
  '''
  file = open(filename, 'r')
  lines = file.readlines()
  file.close()

  df = pd.DataFrame(columns=['id', 'parent', 'label', 'value', 'color'])
  
  component_str = r'([[a-zA-Z\_]+[\/[a-zA-Z0-9\_]*]{0,})\s+(\d+\.+\d+)'
  first_match_is_top = False
  
  rows = []  # Store rows before adding them to df
  
  for line in lines:
      match = re.search(component_str, line)
      if match:
          split_hier = match.group(1).split('/')
          area = float(match.group(2))
          label = prettify_name(split_hier[-1])
  
          if not first_match_is_top:
              rows.append({'id': split_hier[-1], 'parent': '', 'label': label, 'value': area, 'color': 'blue'})
              top_name = split_hier[-1]
              first_match_is_top = True
          elif len(split_hier) == 1:
              print(f"Found top module {split_hier[-1]}")
              rows.append({'id': split_hier[-1], 'parent': top_name, 'label': label, 'value': area, 'color': 'blue'})
          else:
              rows.append({'id': split_hier[-1], 'parent': split_hier[-2], 'label': label, 'value': area, 'color': 'blue'})
  
  # Convert list of rows to DataFrame and concatenate in one operation
  # Check for empty rows to avoid error in concatenation
  if rows:
      df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
  
  # Remove last row (assumed to be the total)
  # Careful!!!! this is true for the tested tools, may be a problem with others
  # print last row
  if not df.empty:
      df = df[:-1]

  # save to temp cvs
  #df.to_csv('temp.csv', index=False, float_format='%.4f', columns=['id', 'parent', 'label', 'value', 'color'], header=True)
  return df  