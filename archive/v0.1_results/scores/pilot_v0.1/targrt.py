import csv

def extract_csv_columns(input_file, output_file, columns):
    """Extract specific columns from CSV file"""
    try:
        with open(input_file, 'r', encoding='utf-8-sig') as infile, \
             open(output_file, 'w', encoding='utf-8-sig', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            fieldnames = [col for col in reader.fieldnames if col in columns]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                writer.writerow({col: row.get(col, '') for col in fieldnames})
        
        print(f"Successfully extracted columns to {output_file}")
    
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    extract_csv_columns("manual_scoring_facet_rows_v0.1.csv", "3ModelOutput.csv", ["task_id", "model","facet","model_answer"])
