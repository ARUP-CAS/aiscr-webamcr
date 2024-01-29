import csv


def csv_to_rst_table(csv_file_path, rst_file_path):
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        with open(rst_file_path, 'w', encoding='utf-8') as rst_file:
            for row_index, row in enumerate(reader):
                # Convert the first row to a header
                if row_index == 0:
                    for column_index, column in enumerate(row):
                        rst_file.write(f"   * - {column}\n" if column_index == 0 else f"     - {column}\n")
                else:
                    for column_index, column in enumerate(row):
                        rst_file.write(f"   * - {column}\n" if column_index == 0 else f"     - {column}\n")


csv_to_rst_table('docs/source/licenses/licenses.csv', 'docs/source/licenses/licenses.rst')

