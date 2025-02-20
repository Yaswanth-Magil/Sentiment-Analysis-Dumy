import openpyxl
import time
import os
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai

def generate_content_from_file(review):
    """Generates sentiment from a review using Generative AI model."""
    prompt = f"You are a machine specialized in segregating whether a review is positive, negative, or neutral. You have to answer in one word whether the review is positive, negative, or neutral. Here is the review: {review}"
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = genai.GenerativeModel('gemini-2.0-flash').generate_content(prompt)
            return response.text.strip()
        except ResourceExhausted as e:
            if attempt < max_retries - 1:
                sleep_time = 9 ** attempt  # Exponential backoff
                print(f"Quota exceeded. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise e

def get_column_index(sheet, column_name):
    """Finds the index of the specified column name."""
    for cell in sheet[1]:
        if cell.value and cell.value.strip().lower() == column_name.lower():
            return cell.column
    return None

def process_reviews(xlsx_file_path):
    """Processes reviews from all sheets in an Excel file and adds sentiment if not already present."""
    workbook = openpyxl.load_workbook(xlsx_file_path)

    for sheet in workbook.worksheets:
        sheet_name = sheet.title
        print(f"Processing sheet: {sheet_name}")

        sentiment_column_index = get_column_index(sheet, 'Sentiment')
        if sentiment_column_index:
            #print(f"Sentiment column already exists in sheet {sheet_name}. Skipping...")
            continue  # Skip processing if sentiment column is already present

        reviews_column_index = get_column_index(sheet, 'Reviews')
        if not reviews_column_index:
            print(f"Error: 'Reviews' column not found in sheet {sheet_name}. Skipping...")
            continue

        sheet.cell(row=1, column=sheet.max_column + 1, value='Sentiment')
        sentiment_column_index = sheet.max_column

        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            review = row[reviews_column_index - 1] if len(row) >= reviews_column_index else None

            if review:
                try:
                    result = generate_content_from_file(review)
                    sentiment = 'Positive' if result.lower() == 'positive' else 'Negative' if result.lower() == 'negative' else 'Neutral'
                    sheet.cell(row=row_num, column=sentiment_column_index, value=sentiment)
                    print(f"Review: {review}\nSentiment: {sentiment}\n")
                except Exception as e:
                    print(f"Error processing review in sheet {sheet_name} row {row_num}: {e}")
                    sheet.cell(row=row_num, column=sentiment_column_index, value="Error")
            else:
                print("No review text found. Skipping...\n")
                continue

    workbook.save(xlsx_file_path)
    print(f"Sentiment analysis completed. Updated file: {xlsx_file_path}")

def main():
    """Main function to execute the sentiment analysis."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    genai.configure(api_key=api_key)

    xlsx_file_path = "A2b_January_month.xlsx"
    process_reviews(xlsx_file_path)

if __name__ == "__main__":
    main()
