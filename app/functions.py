
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
    
