import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import argparse
import textwrap

def list_cols(f):
    data = np.load(f)
    print("Name	Type	Offset")
    for name, typ in data.dtype.fields.items():
        print("%s	%s	%d" % (name, typ[0], typ[1]))

def query_all_numeric(data):
    out = []
    for name, _ in data.dtype.fields.items():
        if not np.issubdtype(data[name].dtype, np.number):
            continue
        out.append(query_single(data, name))
    return out

def query_single(data, column):
    if not np.issubdtype(data[column].dtype, np.number):
        raise ValueError('Column is not numeric')
    return [column, np.nanmean(data[column]),np.nanmedian(data[column]), np.nanmin(data[column]), np.nanmax(data[column])]

def query(f, column=None, all_numeric=False, csv=None):
    data = np.load(f)
    out = None
    if all_numeric:
        out = query_all_numeric(data)
    if column:
        out = [query_single(data, column)]
    for o in out:
        print('Column: %s, mean: %f, median: %f, min: %f, max: %f'%tuple(o))
    if csv:
        pd.DataFrame(out, columns=['Column', 'Mean', 'Median', 'Min', 'Max']).to_csv(csv, index=None)
    
def filter_by_col(f, column, min_cutoff=None, max_cutoff=None):
    data = np.load(f)
    if not np.issubdtype(data[column].dtype, np.number):
        raise ValueError('Column is not numeric')
    out = data
    if min_cutoff:
        out = data[data[column] > min_cutoff]
    if max_cutoff:
        out = out[out[column] < max_cutoff]
    return out   

def make_hist(f, column=None, all_numeric=False):
    data = np.load(f)
    if column:
        make_hist_single(data, column)
    elif all_numeric:
        for name, _ in data.dtype.fields.items():
            if not np.issubdtype(data[name].dtype, np.number):
                continue
            make_hist_single(data, name)

def make_hist_single(data, column):
    if not np.issubdtype(data[column].dtype, np.number):
        raise ValueError('Column is not numeric')
    plt.hist(data[column])
    plt.savefig(column.replace('/', '_') + '_histogram.png')


class RawFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        text = textwrap.dedent(text)          # Strip the indent from the original python definition that plagues most of us.
        text = textwrap.indent(text, indent)  # Apply any requested indent.
        text = text.splitlines()              # Make a list of lines
        text = [textwrap.fill(line, width) for line in text] # Wrap each line 
        text = "\n".join(text)                # Join the lines again
        return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query or filter a cs file.',
        epilog="Examples: \n python cryosel.py list \n python cryosel.py query -c alignments3D/pose_ess \n python cryosel.py query --all \n python cryosel.py query --all --csv columns_stats.csv \n python cryosel.py histogram -c alignments3D/pose_ess \n python cryosel.py histogram --all \n python cryosel.py filter -c alignments3D/pose_ess --min 2.1 --out myfilteredcsfile.cs \n python cryosel.py filter -c alignments3D/pose_ess --max 3.2 --out myfilteredcsfile.cs \n python cryosel.py filter -c alignments3D/pose_ess --min 2.1 --max 3.2 --out myfilteredcsfile.cs", formatter_class=RawFormatter)
    subparsers = parser.add_subparsers(dest='command')
    list_parser = subparsers.add_parser("list", help='List the columns in the cs file.')
    query_parser = subparsers.add_parser("query", help='Get summary statistics for a column.')
    filter_parser = subparsers.add_parser("filter", help='Filter by column values.')
    hist_parser = subparsers.add_parser("histogram", help='Save a histogram(s) for a column(s)') 
    list_parser.set_defaults(func=list_cols)
    query_parser.set_defaults(func=query)
    filter_parser.set_defaults(func=filter_by_col)
    hist_parser.set_defaults(func=make_hist)

    query_parser.add_argument('-f', '--file', required=True, 
                    help='Path to the cs file')
    list_parser.add_argument('-f', '--file', required=True, 
                    help='Path to the cs file')
    filter_parser.add_argument('-f', '--file', required=True, 
                    help='Path to the cs file')
    hist_parser.add_argument('-f', '--file', required=True, 
                    help='Path to the cs file')

    query_parser.add_argument('-c', '--column',
                    help='Retrieve statistics for this column')
    query_parser.add_argument('-a', '--all', action='store_true',
                    help="Retrieve statistics for all numeric columns")
    query_parser.add_argument('--csv', 
                    help='Write column stats to csv')
    filter_parser.add_argument('-c', '--column', required=True,
                    help='Filter on this column')
    filter_parser.add_argument('--min', type=float,
                    help='Remove rows with values equal or lesser than this value')
    filter_parser.add_argument('--max', type=float,
                    help='Remove rows with values equal or greater than this value')
    filter_parser.add_argument('-o', '--output', required=True,
                            help='Name of file to write filter output')
    hist_parser.add_argument('-c', '--column',
                    help='Save a histogram for this column')
    hist_parser.add_argument('-a', '--all', action='store_true',
                    help="Save histograms for all numeric columns")
    args = parser.parse_args()
    if args.command == 'list':
        args.func(args.file)
    if args.command == 'query':
        if not args.column and not args.all:
            raise ValueError('Must specify a column name or all')
        elif args.column and args.all:
            raise ValueError('Please specify either a column name or all, not both')
        elif not args.column:
            args.func(args.file, all_numeric=args.all, csv=args.csv)
        else:
            args.func(args.file, column=args.column, csv=args.csv)
    if args.command == 'filter':
        out = args.func(args.file, args.column, args.min, args.max)
        np.save(args.output, out)
    if args.command == 'histogram':
        if not args.column and not args.all:
            raise ValueError('Must specify a column name or all')
        elif args.column and args.all:
            raise ValueError('Please specify either a column name or all, not both')
        elif not args.column:
            args.func(args.file, all_numeric=args.all)
        else:
            args.func(args.file, column=args.column)
