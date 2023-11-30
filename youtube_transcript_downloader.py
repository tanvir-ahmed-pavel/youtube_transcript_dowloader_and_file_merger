import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfReader, PdfWriter
from urllib.parse import urlparse, parse_qs
from pytube import YouTube

def ensure_files_directory_exists():
    files_directory = os.path.join(os.getcwd(), "files")
    if not os.path.exists(files_directory):
        os.makedirs(files_directory)
    return files_directory

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query = parse_qs(parsed_url.query)
        return query.get('v', [None])[0]
    return None

def get_video_title(url):
    try:
        yt = YouTube(url)
        return yt.title
    except Exception as e:
        print("Error fetching video title")
        return None

def download_transcript_as_txt(url):
    files_directory = ensure_files_directory_exists()
    video_id = extract_video_id(url)
    if not video_id:
        print("Invalid YouTube URL")
        return False

    video_title = get_video_title(url)
    if not video_title:
        print("Unable to fetch video title. Using default file name.")
        video_title = "transcript"

    file_name = f"{video_title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('\"', '_').replace('<', '_').replace('>', '_').replace('|', '_')}.txt"
    file_path = os.path.join(files_directory, file_name)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
        return False
    except NoTranscriptFound:
        print("No English transcript available for this video.")
        return False

    with open(file_path, 'w') as file:
        for line in transcript:
            file.write(line['text'] + '\n')

    print(f"Transcript saved as '{file_path}'")
    return True

def merge_files_to_pdf():
    files_directory = ensure_files_directory_exists()
    output_pdf = PdfWriter()
    temp_files = []

    try:
        for file_name in sorted(os.listdir(files_directory)):
            full_path = os.path.join(files_directory, file_name)
            if file_name.endswith('.txt'):
                temp_pdf_path = full_path.replace('.txt', '.pdf')
                temp_files.append(temp_pdf_path)

                doc = SimpleDocTemplate(temp_pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []

                story.append(Paragraph(file_name, styles['Title']))
                story.append(PageBreak())

                with open(full_path, 'r') as file:
                    for line in file:
                        story.append(Paragraph(line, styles['Normal']))

                doc.build(story)

                with open(temp_pdf_path, 'rb') as f:
                    input_pdf = PdfReader(f)
                    for page in input_pdf.pages:
                        output_pdf.add_page(page)

            elif file_name.endswith('.pdf'):
                with open(full_path, 'rb') as f:
                    input_pdf = PdfReader(f)
                    for page in input_pdf.pages:
                        output_pdf.add_page(page)

        output_pdf_file = os.path.join(files_directory, "merged_documents.pdf")
        with open(output_pdf_file, 'wb') as file:
            output_pdf.write(file)
        print(f"Merged PDF saved as '{output_pdf_file}'")

        # Clean up temporary files
        for temp_file in temp_files:
            os.remove(temp_file)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    while True:
        print("1: Download YouTube Video Transcript")
        print("2: Merge Files to PDF")
        choice = input("Enter your choice (1 or 2): ")

        if choice == '1':
            url = input("Enter YouTube Video Link: ")
            success = download_transcript_as_txt(url)
            if not success:
                print("Failed to download transcript.")
        elif choice == '2':
            merge_files_to_pdf()
        else:
            print("Invalid choice.")

        continue_choice = input("Do you want to perform another action? (yes/no): ")
        if continue_choice.lower() != 'yes':
            break
