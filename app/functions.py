
class DataFrame:
    def __init__(self, data=None, columns=None):
        """
        Initialize a DataFrame.
        
        Args:
            data: Dictionary where keys are column names and values are lists,
                  or a list of dictionaries (rows), or None for empty DataFrame
            columns: List of column names (used when data is empty)
        """
        if data is None:
            self.data = {}
            self.columns = columns if columns else []
        elif isinstance(data, dict):
            self.data = {col: list(values) for col, values in data.items()}
            self.columns = list(data.keys())
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            self.columns = list(data[0].keys())
            self.data = {col: [] for col in self.columns}
            for row in data:
                for col in self.columns:
                    self.data[col].append(row.get(col, None))
        else:
            raise ValueError("Data must be a dictionary of lists or a list of dictionaries")
        if self.data:
            lengths = [len(v) for v in self.data.values()]
            if len(set(lengths)) > 1:
                raise ValueError("All columns must have the same length")
    
    def __len__(self):
        """Return the number of rows in the DataFrame."""
        if not self.data:
            return 0
        return len(next(iter(self.data.values())))
    
    def __getitem__(self, key):
        """
        Retrieve column(s) using bracket notation.
        
        Args:
            key: Column name (str) or list of column names
            
        Returns:
            List of values for single column, or new DataFrame for multiple columns
        """
        if isinstance(key, str):
            if key not in self.data:
                raise KeyError(f"Column '{key}' not found")
            return self.data[key]
        elif isinstance(key, list):
            return self.select(key)
        else:
            raise TypeError("Key must be a string or list of strings")
    
    def __repr__(self):
        """String representation of the DataFrame."""
        if not self.data:
            return "Empty DataFrame"
        max_rows = min(10, len(self))
        col_widths = {}
        for col in self.columns:
            max_width = len(str(col))
            for i in range(max_rows):
                max_width = max(max_width, len(str(self.data[col][i])))
            col_widths[col] = min(max_width, 30)
        header = " | ".join(str(col)[:col_widths[col]].ljust(col_widths[col]) 
                           for col in self.columns)
        separator = "-+-".join("-" * col_widths[col] for col in self.columns)
        rows = []
        for i in range(max_rows):
            row = " | ".join(str(self.data[col][i])[:col_widths[col]].ljust(col_widths[col]) 
                           for col in self.columns)
            rows.append(row)
        result = f"{header}\n{separator}\n" + "\n".join(rows)
        if len(self) > max_rows:
            result += f"\n... ({len(self) - max_rows} more rows)"
        result += f"\n\n[{len(self)} rows x {len(self.columns)} columns]"
        return result
    
    def head(self, n=5):
        """
        Return the first n rows of the DataFrame.
        
        Args:
            n: Number of rows to return (default: 5)
            
        Returns:
            New DataFrame with first n rows
        """
        new_data = {col: values[:n] for col, values in self.data.items()}
        return DataFrame(new_data)
    
    def tail(self, n=5):
        """
        Return the last n rows of the DataFrame.
        
        Args:
            n: Number of rows to return (default: 5)
            
        Returns:
            New DataFrame with last n rows
        """
        new_data = {col: values[-n:] for col, values in self.data.items()}
        return DataFrame(new_data)
    
    def shape(self):
        """
        Return the dimensions of the DataFrame.
        
        Returns:
            Tuple of (num_rows, num_columns)
        """
        return (len(self), len(self.columns))
    
    def copy(self):
        """
        Create a deep copy of the DataFrame.
        
        Returns:
            New DataFrame with copied data
        """
        new_data = {col: list(values) for col, values in self.data.items()}
        return DataFrame(new_data)
    
    def filter(self, condition):
        """
        Filter rows based on a condition function.
        
        Args:
            condition: A function that takes a row dictionary and returns True/False
            
        Returns:
            New DataFrame with filtered rows
        """
        if not callable(condition):
            raise TypeError("Condition must be a callable function")
        filtered_data = {col: [] for col in self.columns}
        for i in range(len(self)):
            row = {col: self.data[col][i] for col in self.columns}
            if condition(row):
                for col in self.columns:
                    filtered_data[col].append(self.data[col][i])
        return DataFrame(filtered_data)
    
    def filter_by_value(self, column, value):
        """
        Filter rows where a specific column equals a specific value.
        
        Args:
            column: Column name to filter on
            value: Value to match
            
        Returns:
            New DataFrame with filtered rows
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        return self.filter(lambda row: row[column] == value)

    def select(self, columns):
        """
        Select specific columns (projection).
        
        Args:
            columns: List of column names to select
            
        Returns:
            New DataFrame with selected columns
        """
        if not isinstance(columns, list):
            columns = [columns]
        for col in columns:
            if col not in self.columns:
                raise KeyError(f"Column '{col}' not found")
        new_data = {col: list(self.data[col]) for col in columns}
        return DataFrame(new_data)
    
    def drop(self, columns):
        """
        Drop specific columns.
        
        Args:
            columns: List of column names to drop
            
        Returns:
            New DataFrame without specified columns
        """
        if not isinstance(columns, list):
            columns = [columns]
        remaining_cols = [col for col in self.columns if col not in columns]
        return self.select(remaining_cols)
    
    def groupby(self, by):
        """
        Group DataFrame by one or more columns.
        
        Args:
            by: Column name (str) or list of column names to group by
            
        Returns:
            GroupBy object for aggregation operations
        """
        if isinstance(by, str):
            by = [by]
        for col in by:
            if col not in self.columns:
                raise KeyError(f"Column '{col}' not found")
        return GroupBy(self, by)
    
    def aggregate(self, column, func_name):
        """
        Perform aggregation on a single column.
        
        Args:
            column: Column name to aggregate
            func_name: Aggregation function name ('sum', 'mean', 'count', 'min', 'max')
            
        Returns:
            Aggregated value
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        values = self.data[column]
        if func_name == 'count':
            return len(values)
        elif func_name == 'sum':
            return sum(v for v in values if v is not None and v != '')
        elif func_name == 'mean':
            numeric_values = [v for v in values if v is not None and v != '']
            return sum(numeric_values) / len(numeric_values) if numeric_values else None
        elif func_name == 'min':
            valid_values = [v for v in values if v is not None and v != '']
            return min(valid_values) if valid_values else None
        elif func_name == 'max':
            valid_values = [v for v in values if v is not None and v != '']
            return max(valid_values) if valid_values else None
        else:
            raise ValueError(f"Unsupported aggregation function: {func_name}")
    
    def join(self, other, on=None, left_on=None, right_on=None, how='inner'):
        """
        Join with another DataFrame.
        
        Args:
            other: Another DataFrame to join with
            on: Column name to join on (must exist in both DataFrames)
            left_on: Column name in left DataFrame (self)
            right_on: Column name in right DataFrame (other)
            how: Join type ('inner', 'left', 'right', 'outer')
            
        Returns:
            New DataFrame with joined data
        """
        if not isinstance(other, DataFrame):
            raise TypeError("Can only join with another DataFrame")
        if on is not None:
            left_key = on
            right_key = on
        elif left_on is not None and right_on is not None:
            left_key = left_on
            right_key = right_on
        else:
            raise ValueError("Must specify either 'on' or both 'left_on' and 'right_on'")
        if left_key not in self.columns:
            raise KeyError(f"Column '{left_key}' not found in left DataFrame")
        if right_key not in other.columns:
            raise KeyError(f"Column '{right_key}' not found in right DataFrame")
        right_index = {}
        for i in range(len(other)):
            key_value = other.data[right_key][i]
            if key_value not in right_index:
                right_index[key_value] = []
            right_index[key_value].append(i)
        result_columns = list(self.columns)
        for col in other.columns:
            if col not in result_columns:
                result_columns.append(col)
            elif col != right_key:
                result_columns.append(f"{col}_right")
        result_data = {col: [] for col in result_columns}
        matched_right_rows = set()
        for i in range(len(self)):
            left_key_value = self.data[left_key][i]
            if left_key_value in right_index:
                for j in right_index[left_key_value]:
                    matched_right_rows.add(j)
                    for col in self.columns:
                        result_data[col].append(self.data[col][i])
                    for col in other.columns:
                        if col == right_key and col in self.columns:
                            continue
                        result_col = f"{col}_right" if col in self.columns and col != right_key else col
                        result_data[result_col].append(other.data[col][j])
            else:
                if how in ['left', 'outer']:
                    for col in self.columns:
                        result_data[col].append(self.data[col][i])
                    for col in other.columns:
                        if col == right_key and col in self.columns:
                            continue
                        result_col = f"{col}_right" if col in self.columns and col != right_key else col
                        result_data[result_col].append(None)
        if how in ['right', 'outer']:
            for j in range(len(other)):
                if j not in matched_right_rows:
                    for col in self.columns:
                        if col == left_key:
                            result_data[col].append(other.data[right_key][j])
                        else:
                            result_data[col].append(None)
                    for col in other.columns:
                        if col == right_key and col in self.columns:
                            continue
                        result_col = f"{col}_right" if col in self.columns and col != right_key else col
                        result_data[result_col].append(other.data[col][j])
        return DataFrame(result_data)

    def sort(self, by, ascending=True):
        """
        Sort DataFrame by one or more columns.
        
        Args:
            by: Column name (str) or list of column names to sort by
            ascending: Sort order (True = ascending, False = descending)
            
        Returns:
            New sorted DataFrame
        """
        if isinstance(by, str):
            by = [by]
        for col in by:
            if col not in self.columns:
                raise KeyError(f"Column '{col}' not found")
        row_indices = list(range(len(self)))
        def get_sort_key(idx):
            return tuple(self.data[col][idx] for col in by)
        sorted_indices = sorted(row_indices, key=get_sort_key, reverse=not ascending)
        new_data = {col: [self.data[col][idx] for idx in sorted_indices] for col in self.columns}
        return DataFrame(new_data)
    
    def add_column(self, column_name, values):
        """
        Add a new column to DataFrame.
        
        Args:
            column_name: Name of new column
            values: List of values (must match DataFrame length)
            
        Returns:
            New DataFrame with added column
        """
        if len(values) != len(self):
            raise ValueError(f"Values length ({len(values)}) must match DataFrame length ({len(self)})")
        new_data = {col: list(self.data[col]) for col in self.columns}
        new_data[column_name] = list(values)
        return DataFrame(new_data)
    
    def rename_columns(self, mapping):
        """
        Rename columns in DataFrame.
        
        Args:
            mapping: Dictionary mapping old names to new names
            
        Returns:
            New DataFrame with renamed columns
        """
        new_data = {}
        new_columns = []
        for col in self.columns:
            if col in mapping:
                new_col_name = mapping[col]
                new_data[new_col_name] = list(self.data[col])
                new_columns.append(new_col_name)
            else:
                new_data[col] = list(self.data[col])
                new_columns.append(col)
        result = DataFrame(new_data)
        result.columns = new_columns
        return result
    
    def fillna_column(self, column, value):
        """
        Fill None/null values in a column with a specified value.
        
        Args:
            column: Column name to fill
            value: Value to fill None with
            
        Returns:
            New DataFrame with filled values
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        new_data = {col: list(self.data[col]) for col in self.columns}
        new_data[column] = [v if v is not None and v != '' else value for v in new_data[column]]
        return DataFrame(new_data)
    
    def convert_column_type(self, column, target_type):
        """
        Convert column values to a specific type.
        
        Args:
            column: Column name to convert
            target_type: Target type (int, float, str, etc.)
            
        Returns:
            New DataFrame with converted column
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        new_data = {col: list(self.data[col]) for col in self.columns}
        def convert_value(v):
            if v is None or v == '':
                return None
            try:
                return target_type(v)
            except (ValueError, TypeError):
                return v
        new_data[column] = [convert_value(v) for v in new_data[column]]
        return DataFrame(new_data)
    
    def round_column(self, column, decimals=2):
        """
        Round numeric values in a column.
        
        Args:
            column: Column name to round
            decimals: Number of decimal places
            
        Returns:
            New DataFrame with rounded values
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        new_data = {col: list(self.data[col]) for col in self.columns}
        def round_value(v):
            if isinstance(v, (int, float)) and v is not None:
                return round(v, decimals)
            return v
        new_data[column] = [round_value(v) for v in new_data[column]]
        return DataFrame(new_data)

class GroupBy:
    def __init__(self, dataframe, by):
        """
        Initialize GroupBy object.
        
        Args:
            dataframe: DataFrame to group
            by: List of column names to group by
        """
        self.df = dataframe
        self.by = by
        self._groups = self._create_groups()

def parse_csv_line(line, separator=','):
    """
    Parse a single line of CSV, handling quoted fields.
    Optimized for performance.
    
    Args:
        line: String line from CSV
        separator: Column separator character
        
    Returns:
        List of field values
    """
    fields = []
    current_field = []
    in_quotes = False
    i = 0
    line_len = len(line)
    while i < line_len:
        char = line[i]
        if char == '"':
            if in_quotes and i + 1 < line_len and line[i + 1] == '"':
                current_field.append('"')
                i += 2
                continue
            else:
                in_quotes = not in_quotes
                i += 1
                continue
        if char == separator and not in_quotes:
            fields.append(''.join(current_field))
            current_field = []
            i += 1
            continue
        current_field.append(char)
        i += 1
    fields.append(''.join(current_field))
    return fields

def infer_type(value):
    """
    Infer the type of a value and convert it.
    Optimized for performance - no strip on every value.
    
    Args:
        value: String value to convert
        
    Returns:
        Converted value (int, float, or string)
    """
    if not value:
        return None
    if value[0].isdigit() or (len(value) > 1 and value[0] == '-' and value[1].isdigit()):
        try:
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
    return value
        
def read_csv(filename, separator=',', encoding='utf-8', nrows=None, 
        chunksize=None, skip_type_inference=False, verbose=True):
    """
    Parse a CSV file and return a DataFrame.

    This is a custom CSV parser that handles:
    - Different column separators
    - Quoted fields (with commas inside)
    - Type inference (numbers vs strings)
    - Chunked reading for large files
    - Row limits for testing

    Args:
        filename: Path to the CSV file
        separator: Column separator character (default: ',')
        encoding: File encoding (default: 'utf-8')
        nrows: Number of rows to read (None = all rows)
        chunksize: If specified, process in chunks of this size (more memory efficient)
        skip_type_inference: If True, keep all values as strings (faster)
        verbose: Show progress indicator (default: True)
        
    Returns:
        DataFrame object containing the parsed data
    """
    try:
        with open(filename, 'r', encoding=encoding) as f:
            header_line = f.readline().strip()
            if not header_line:
                raise ValueError("File is empty")
            columns = parse_csv_line(header_line, separator)
            columns = [col.strip() for col in columns]
            data = {col: [] for col in columns}
            num_cols = len(columns)
            rows_read = 0
            line_num = 1
            if verbose:
                print(f"Reading CSV file: {filename}")
                print(f"Columns: {len(columns)}")
            for line in f:
                line_num += 1
                line = line.strip()
                if not line:
                    continue
                fields = parse_csv_line(line, separator)
                if len(fields) != num_cols:
                    if verbose and rows_read < 10:
                        print(f"Warning: Line {line_num} has {len(fields)} fields, expected {num_cols}. Skipping.")
                    continue
                if skip_type_inference:
                    for col, field in zip(columns, fields):
                        data[col].append(field if field else None)
                else:
                    for col, field in zip(columns, fields):
                        data[col].append(infer_type(field))
                rows_read += 1
                if verbose and rows_read % 10000 == 0:
                    print(f"  Processed {rows_read:,} rows...", end='\r')
                if nrows is not None and rows_read >= nrows:
                    break
            if verbose:
                print(f"  Completed! Loaded {rows_read:,} rows." + " " * 20)
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filename}' not found")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")
    return DataFrame(data)

def _parse_csv_chunk(filename, start_byte, end_byte, columns, separator, 
                    skip_type_inference, encoding):
    """
    Helper function to parse a chunk of CSV file (used by multiprocessing).
    This function runs in a separate process.
    
    Args:
        filename: Path to the CSV file
        start_byte: Starting byte position
        end_byte: Ending byte position
        columns: List of column names
        separator: Column separator
        skip_type_inference: Whether to skip type conversion
        encoding: File encoding
        
    Returns:
        Dictionary of column data for this chunk
    """
    data = {col: [] for col in columns}
    num_cols = len(columns)
    with open(filename, 'r', encoding=encoding, buffering=1024*1024) as f:
        if start_byte > 0:
            f.seek(start_byte)
            f.readline()
        else:
            f.readline()
        while f.tell() < end_byte:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            fields = parse_csv_line(line, separator)
            if len(fields) != num_cols:
                continue
            if skip_type_inference:
                for col, field in zip(columns, fields):
                    data[col].append(field if field else None)
            else:
                for col, field in zip(columns, fields):
                    data[col].append(infer_type(field))
        for _ in range(5):
            if f.tell() >= end_byte + 5000:
                break
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            fields = parse_csv_line(line, separator)
            if len(fields) != num_cols:
                continue
            if skip_type_inference:
                for col, field in zip(columns, fields):
                    data[col].append(field if field else None)
            else:
                for col, field in zip(columns, fields):
                    data[col].append(infer_type(field))
    return data

def read_csv_parallel(filename, separator=',', encoding='utf-8', num_processes=None,
                      skip_type_inference=True, verbose=True):
    """
    Read CSV file using multiple processes for faster parsing.
    Uses multiprocessing to parse different sections of the file in parallel.
    
    Args:
        filename: Path to the CSV file
        separator: Column separator character (default: ',')
        encoding: File encoding (default: 'utf-8')
        num_processes: Number of processes to use (default: CPU count)
        skip_type_inference: If True, keep all values as strings (faster, default: True)
        verbose: Show progress messages (default: True)
        
    Returns:
        DataFrame object containing the parsed data
    """
    import multiprocessing as mp
    import os
    import time
    start_time = time.time()
    if num_processes is None:
        num_processes = mp.cpu_count()
    if verbose:
        print(f"Reading CSV file in parallel using {num_processes} processes...")
    file_size = os.path.getsize(filename)
    with open(filename, 'r', encoding=encoding, buffering=1024*1024) as f:
        header_line = f.readline()
        header_size = f.tell()
        columns = parse_csv_line(header_line.strip(), separator)
        columns = [col.strip() for col in columns]
    if verbose:
        print(f"File size: {file_size / (1024**3):.2f} GB, Columns: {len(columns)}")
    data_size = file_size - header_size
    chunk_size = data_size // num_processes
    tasks = []
    for i in range(num_processes):
        start_byte = header_size + i * chunk_size
        end_byte = header_size + (i + 1) * chunk_size if i < num_processes - 1 else file_size
        tasks.append((filename, start_byte, end_byte, columns, separator, 
                     skip_type_inference, encoding))
    if verbose:
        print("Processing chunks in parallel...")
    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(_parse_csv_chunk, tasks)
    if verbose:
        read_time = time.time() - start_time
        print(f"Parallel reading completed in {read_time:.2f}s. Combining results...")
        combine_start = time.time()
    total_rows = sum(len(chunk_data[columns[0]]) for chunk_data in results)
    combined_data = {col: [None] * total_rows for col in columns}
    current_pos = 0
    for chunk_data in results:
        chunk_size = len(chunk_data[columns[0]])
        if chunk_size > 0:
            for col in columns:
                combined_data[col][current_pos:current_pos + chunk_size] = chunk_data[col]
            current_pos += chunk_size
    if verbose:
        combine_time = time.time() - combine_start
        total_time = time.time() - start_time
        print(f"Combining completed in {combine_time:.2f}s")
        print(f"✓ Total time: {total_time:.2f}s - Loaded {total_rows:,} rows")
    return DataFrame(combined_data)
    
