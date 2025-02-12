from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from gtts import gTTS, gTTSError
import io
import base64
import tempfile
import os
import pdfplumber  # For PDFs
import docx  # For DOCX

class MainPageView(View):
    def get(self, request):
        return render(request, template_name="txt_2_speech/main_page.html")

    def post(self, request):
        text = request.POST.get('content')  # Get text from the form
        file = request.FILES.get('file')  # Get uploaded file
        lang = request.POST.get('lang')  # Get selected language
        speed = request.POST.get('speed')  # Get speed setting

        def get_text(text, file):
            # Use provided text if available
            if text:
                return text
            # If a file is uploaded, save it temporarily and process it
            elif file:
                tmp_name = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as tmp:
                        for chunk in file.chunks():
                            tmp.write(chunk)
                        tmp.flush()  # Ensure all data is written to disk
                        tmp_name = tmp.name  # Get the path of the temporary file

                    # Extract text based on file type
                    if file.name.endswith('.pdf'):
                        # Extract text from PDF using pdfplumber
                        with pdfplumber.open(tmp_name) as pdf:
                            text = ""
                            for page in pdf.pages:
                                text += page.extract_text()
                        return text

                    elif file.name.endswith('.docx'):
                        # Extract text from DOCX using python-docx
                        doc = docx.Document(tmp_name)
                        return "\n".join([para.text for para in doc.paragraphs])

                    elif file.name.endswith('.txt'):
                        # Extract text from TXT using built-in file handling
                        with open(tmp_name, 'r', encoding='utf-8', errors='replace') as f:
                            return f.read()

                    else:
                        print(f"Unsupported file type: {file.name}")
                        return None

                except Exception as e:
                    # Handle any unexpected errors
                    print(f"Error processing file: {e}")
                    return None
                finally:
                    # If a temporary file was created, remove it
                    if tmp_name and os.path.exists(tmp_name):
                        os.remove(tmp_name)
            return None

        def get_lang(lang):
            # If no language is selected, default to English ('en')
            if lang == 'lang':
                return 'en'
            return lang

        def is_slow_speed(speed):
            return speed == 'slow'

        # Extract text content
        text_content = get_text(text, file)

        if text_content:
            try:
                # Generate the audio using gTTS
                audio_file = gTTS(
                    text=text_content,
                    lang=get_lang(lang),
                    slow=is_slow_speed(speed),
                    tld="com"
                )
                audio_buffer = io.BytesIO()
                audio_file.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')

                return JsonResponse({'audio_base64': audio_base64}, status=200)

            except gTTSError as e:
                # Handle gTTS-specific errors (including network errors)
                return JsonResponse({'error_msg': "Ooops!, no Network. Please refresh and try again."}, status=403)

            except Exception as e:
                # Handle other unexpected errors
                return JsonResponse({'error_msg': f"An error occurred: {str(e)}"}, status=403)

        else:
            # Return 403 if no text content is provided
            return JsonResponse({'error_msg': "You didn't input any text or text document"}, status=403)
